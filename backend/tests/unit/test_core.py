"""Unit tests for the Phase 2 Core Framework.

Run: pytest backend/tests/unit/test_core.py  (asyncio_mode=auto is set in pyproject.toml)
These tests require no external infrastructure — all backends are in-memory.
"""
from __future__ import annotations

import asyncio

import pytest

from backend.core.agent_manager.manager import AgentManager, AgentSpec
from backend.core.base_agent import BaseAgent
from backend.core.container import Container
from backend.core.event_bus.event_bus import EventBus
from backend.core.memory_manager.memory import MemoryManager
from backend.core.message_bus.message_bus import MessageBus
from backend.core.metrics.metrics import MetricsRegistry
from backend.core.permission_manager.permissions import PermissionError, PermissionManager
from backend.core.scheduler.scheduler import (CronTrigger, IntervalTrigger, ScheduledJob,
                                              Scheduler)
from backend.core.task_manager.tasks import InvalidTransition, Task, TaskGraph, TaskManager
from backend.core.tool_registry.registry import FunctionTool, ToolRegistry
from backend.core.workflow_engine.engine import Workflow, WorkflowEngine
from backend.schemas.agent import (AgentRequest, AgentResponse, AgentTier, TaskStatus)
from datetime import datetime, timedelta, timezone


# --------------------------------------------------------------------------- metrics
def test_metrics_counter_and_render():
    m = MetricsRegistry()
    m.counter("tool_invocations", tool="x", status="ok")
    m.counter("tool_invocations", tool="x", status="ok")
    with m.timer("op"):
        pass
    out = m.render()
    assert "tool_invocations_total" in out
    assert "op_count" in out


# --------------------------------------------------------------------------- event bus
async def test_event_bus_pubsub_and_groups():
    bus = EventBus()
    got_a: list = []
    got_b: list = []
    await bus.subscribe("topic.x", "group-a", lambda p: got_a.append(p) or _aok())
    await bus.subscribe("topic.x", "group-b", lambda p: got_b.append(p) or _aok())
    await bus.publish("topic.x", {"n": 1})
    await bus.drain()
    assert got_a and got_b  # each group received it once
    await bus.shutdown()


async def _aok():
    return None


async def test_event_bus_dead_letter():
    bus = EventBus(max_retries=2)

    async def boom(_):
        raise RuntimeError("nope")

    await bus.subscribe("t", "g", boom)
    await bus.publish("t", {"a": 1})
    await bus.drain()
    assert len(bus.dead_letter) == 1
    await bus.shutdown()


# --------------------------------------------------------------------------- message bus
async def test_message_bus_request_reply():
    mb = MessageBus()

    async def handler(payload):
        return {"echo": payload["msg"]}

    mb.handle("soldier.echo", handler)
    res = await mb.request("soldier.echo", {"msg": "hi"})
    assert res == {"echo": "hi"}


async def test_message_bus_unknown_target():
    mb = MessageBus()
    with pytest.raises(KeyError):
        await mb.request("missing", {})


# --------------------------------------------------------------------------- permissions
async def test_permissions_deny_by_default_and_wildcard():
    pm = PermissionManager()
    assert await pm.check("user1", "tool:web") is False
    pm.grant("operator", "tool:*")
    pm.assign("user1", "operator")
    assert await pm.check("user1", "tool:web") is True
    with pytest.raises(PermissionError):
        await pm.require("user1", "admin:delete")
    assert any(e.decision == "deny" for e in pm.audit_log)


# --------------------------------------------------------------------------- tools
async def test_tool_registry_invoke_with_permission():
    pm = PermissionManager()
    pm.grant("r", "tool:adder")
    pm.assign("agent1", "r")
    tr = ToolRegistry(permissions=pm)

    async def add(args):
        return args["a"] + args["b"]

    tr.register(FunctionTool("adder", add,
                             schema={"type": "object", "required": ["a", "b"]}))
    assert await tr.invoke("adder", {"a": 2, "b": 3}, agent_id="agent1") == 5
    with pytest.raises(ValueError):  # missing required arg
        await tr.invoke("adder", {"a": 2}, agent_id="agent1")


async def test_tool_registry_blocks_unpermitted_agent():
    pm = PermissionManager()
    tr = ToolRegistry(permissions=pm)
    tr.register(FunctionTool("secret", lambda a: _aok()))
    with pytest.raises(PermissionError):
        await tr.invoke("secret", {}, agent_id="nobody")


# --------------------------------------------------------------------------- memory
async def test_memory_remember_recall_forget():
    mm = MemoryManager()
    await mm.remember("the capital of France is Paris", scope="kb", owner="u1")
    await mm.remember("python is a programming language", scope="kb", owner="u1")
    hits = await mm.recall("France capital city", scope="kb", owner="u1", k=1)
    assert hits and "Paris" in hits[0]["content"]
    mid = hits[0]["id"]
    await mm.forget(mid)
    assert mm.long_term.get(mid) is None


# --------------------------------------------------------------------------- tasks
async def test_task_graph_dependencies_and_execution():
    tm = TaskManager()
    g = TaskGraph()
    a = g.add(Task(objective="A", owner_agent="gen"))
    b = g.add(Task(objective="B", owner_agent="gen", depends_on={a.id}))
    order: list = []

    async def executor(task: Task):
        order.append(task.objective)
        return f"done:{task.objective}"

    result = await tm.run_graph(g, executor)
    assert order == ["A", "B"]  # dependency respected
    assert all(t.status == TaskStatus.COMPLETED for t in result.values())


async def test_task_retry_then_dead_letter():
    tm = TaskManager()
    g = TaskGraph()
    t = g.add(Task(objective="flaky", owner_agent="gen", max_attempts=2))

    async def always_fail(_):
        raise RuntimeError("boom")

    await tm.run_graph(g, always_fail)
    assert t.status == TaskStatus.FAILED
    assert t.attempts == 2


def test_task_invalid_transition():
    tm = TaskManager()
    t = Task(objective="x", owner_agent="g")
    with pytest.raises(InvalidTransition):
        tm.transition(t, TaskStatus.COMPLETED)  # cannot go PENDING -> COMPLETED


def test_task_graph_cycle_detection():
    g = TaskGraph()
    a = g.add(Task(objective="A", owner_agent="g"))
    b = g.add(Task(objective="B", owner_agent="g", depends_on={a.id}))
    g.tasks[a.id].depends_on = {b.id}  # introduce a cycle
    with pytest.raises(ValueError):
        g.topological_order()


# --------------------------------------------------------------------------- workflow
async def test_workflow_sequential_conditional_loop():
    eng = WorkflowEngine()
    wf = Workflow("demo")

    async def init(s):
        s["count"] = 0
        return s

    async def inc(s):
        s["count"] += 1
        return s

    async def skipped(s):
        s["skipped"] = True
        return s

    wf.step("init", init)
    wf.step("loop_inc", inc, loop_while=lambda s: s["count"] < 3)
    wf.step("never", skipped, condition=lambda s: False)
    run = await eng.run(wf)
    assert run.status == "completed"
    assert run.state["count"] == 3
    assert "skipped" not in run.state


# --------------------------------------------------------------------------- scheduler
async def test_scheduler_interval_fires():
    bus = EventBus()
    fired: list = []
    await bus.subscribe("job.fired", "g", lambda p: fired.append(p) or _aok())
    sch = Scheduler(bus=bus)
    job = ScheduledJob(name="ping", trigger=IntervalTrigger(seconds=0.0),
                       payload={"k": "v"})
    sch.schedule(job)
    await sch.tick()  # next_run is ~now, should fire
    await bus.drain()
    assert fired and fired[0]["job"] == "ping"
    await bus.shutdown()


def test_cron_trigger_next():
    cron = CronTrigger("0 * * * *")  # top of every hour
    now = datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc)
    nxt = cron.next_after(now)
    assert nxt == datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- agent manager
class _DummyAgent(BaseAgent):
    tier = AgentTier.SOLDIER

    def __init__(self, agent_id, healthy=True):
        super().__init__(agent_id)
        self._healthy = healthy
        self.initialized = False

    async def initialize(self):
        self.initialized = True

    async def execute(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(request_id=request.request_id, agent_id=self.agent_id,
                             tier=self.tier, status=TaskStatus.COMPLETED, result="ok")

    async def validate(self, request):
        return True

    async def health_check(self):
        return {"status": "ok" if self._healthy else "error"}

    async def shutdown(self):
        self.initialized = False


async def test_agent_manager_ensure_and_execute():
    am = AgentManager()
    am.register(AgentSpec(name="echo_soldier", tier=AgentTier.SOLDIER,
                          builder=lambda aid: _DummyAgent(aid)))
    agent = await am.ensure("echo_soldier")
    assert agent.initialized
    resp = await agent.execute(AgentRequest(objective="ping"))
    assert resp.status == TaskStatus.COMPLETED
    # idempotent
    assert await am.ensure("echo_soldier") is agent


async def test_agent_manager_supervise_restarts_unhealthy():
    am = AgentManager()
    am.register(AgentSpec(name="bad", tier=AgentTier.SOLDIER,
                          builder=lambda aid: _DummyAgent(aid, healthy=False)))
    await am.ensure("bad")
    restarted = await am.supervise()
    assert "bad" in restarted


# --------------------------------------------------------------------------- container
async def test_container_wires_everything_and_health():
    c = Container()
    await c.startup()
    code, detail = await c.health.report()
    assert code == 200 and detail["healthy"] is True
    # exercise the full stack through the container
    c.permissions.grant("r", "tool:noop")
    c.permissions.assign("a1", "r")
    c.tools.register(FunctionTool("noop", lambda args: _aok()))
    await c.tools.invoke("noop", {}, agent_id="a1")
    await c.memory.remember("hello world", scope="s", owner="a1")
    assert "tool_invocations_total" in c.metrics.render()
    await c.shutdown()
