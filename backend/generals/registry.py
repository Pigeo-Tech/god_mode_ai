"""General registry + factory (generated for the AGNI 15-general hierarchy).

Registers every General with the Agent Manager via AgentSpec (Factory). Registry keys are
tier-qualified (``general:<domain>``); the agent id stays the bare domain (bus: general.<domain>).
"""
from __future__ import annotations

from backend.core.agent_context import AgentDeps
from backend.core.agent_manager.manager import AgentManager, AgentSpec
from backend.generals.base import BaseGeneral
from backend.generals.knowledge.general import KnowledgeGeneral
from backend.generals.planning.general import PlanningGeneral
from backend.generals.execution.general import ExecutionGeneral
from backend.generals.memory.general import MemoryGeneral
from backend.generals.coding.general import CodingGeneral
from backend.generals.media.general import MediaGeneral
from backend.generals.finance.general import FinanceGeneral
from backend.generals.communication.general import CommunicationGeneral
from backend.generals.system.general import SystemGeneral
from backend.generals.automation.general import AutomationGeneral
from backend.generals.device.general import DeviceGeneral
from backend.generals.security.general import SecurityGeneral
from backend.generals.iot.general import IotGeneral
from backend.generals.asi.general import AsiGeneral
from backend.generals.voice.general import VoiceGeneral
from backend.schemas.agent import AgentTier

GENERAL_CLASSES: list[type[BaseGeneral]] = [
    KnowledgeGeneral, PlanningGeneral, ExecutionGeneral, MemoryGeneral, CodingGeneral, MediaGeneral, FinanceGeneral, CommunicationGeneral, SystemGeneral, AutomationGeneral, DeviceGeneral, SecurityGeneral, IotGeneral, AsiGeneral, VoiceGeneral,
]


def general_key(domain: str) -> str:
    return f"general:{domain}"


def register_generals(manager: AgentManager, deps: AgentDeps) -> list[str]:
    names: list[str] = []
    for cls in GENERAL_CLASSES:
        manager.register(AgentSpec(
            name=general_key(cls.domain),
            tier=AgentTier.GENERAL,
            builder=lambda agent_id, c=cls, d=deps: c(c.domain, d),
        ))
        names.append(cls.domain)
    return names


async def ensure_all_generals(manager: AgentManager) -> list:
    return [await manager.ensure(general_key(cls.domain)) for cls in GENERAL_CLASSES]
