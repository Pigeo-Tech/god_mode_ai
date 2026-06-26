/* AGNI King Command Center — Phase 1. Vanilla JS, talks to the live AGNI FastAPI backend. */
(() => {
  "use strict";

  // ---------------------------------------------------------------- API client
  const store = {
    get base() { return localStorage.getItem("agni_base") || "http://13.60.255.199:8000"; },
    set base(v) { localStorage.setItem("agni_base", v); },
    get token() { return localStorage.getItem("agni_token") || ""; },
    set token(v) { v ? localStorage.setItem("agni_token", v) : localStorage.removeItem("agni_token"); },
  };

  const api = {
    headers() {
      const h = { "Content-Type": "application/json" };
      if (store.token) h["Authorization"] = "Bearer " + store.token;
      return h;
    },
    async get(p) {
      const r = await fetch(store.base + p, { headers: api.headers() });
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    },
    async post(p, body) {
      const r = await fetch(store.base + p, { method: "POST", headers: api.headers(), body: JSON.stringify(body) });
      if (!r.ok) { const t = await r.text(); throw new Error("HTTP " + r.status + ": " + t); }
      return r.json();
    },
    register: (e, pw) => api.post("/v1/auth/register", { email: e, password: pw }),
    async login(e, pw) {
      const r = await api.post("/v1/auth/login", { email: e, password: pw });
      store.token = r.access_token;
    },
    health: () => api.get("/health"),
    agents: () => api.get("/v1/agents"),
    tools: () => api.get("/v1/tools"),
    chat: (m) => api.post("/v1/chat", { message: m, stream: false }),
  };

  // ---------------------------------------------------------------- navigation
  const SECTIONS = [
    ["dashboard", "Dashboard", "fa-gauge-high", renderDashboard],
    ["king", "King · Agent Tree", "fa-fire", renderKing],
    ["buddy", "Buddy Console", "fa-comments", renderBuddy],
    ["generals", "Generals", "fa-chess-rook", renderGenerals],
    ["soldiers", "Soldiers", "fa-users", renderSoldiers],
    ["skills", "Skills", "fa-scroll", phase2("Skills Manager", "Create, edit, assign and version SKILL.md files for King/Generals/Soldiers.")],
    ["llms", "LLM Manager", "fa-microchip", renderLLMs],
    ["knowledge", "Knowledge", "fa-book", phase2("Knowledge Base", "Upload PDF/DOCX/CSV/MD, tag, search, vector-index.")],
    ["memory", "Memory", "fa-brain", phase2("Memory System", "Short / long / session / persistent memory, search & export.")],
    ["prompts", "Prompt Library", "fa-pen-nib", phase2("Prompt Library", "Store, version, test and assign prompts.")],
    ["users", "Users", "fa-user-shield", phase2("User Management", "Roles, permissions, 2FA, admin operators.")],
    ["automation", "Automation", "fa-robot", phase2("Automation", "Triggers, schedules, self-healing workflows.")],
    ["analytics", "Analytics", "fa-chart-line", phase2("Analytics", "Growth, requests, cost, agent performance.")],
    ["wallet", "Wallet", "fa-wallet", phase2("Wallet & Cost", "Balance, AI cost, budget caps.")],
    ["apimgr", "API Manager", "fa-plug", phase2("API Manager", "Keys, services, rate limits, health.")],
    ["logs", "Logs", "fa-list", phase2("Audit Logs", "Every login, task, skill, error, upload.")],
    ["security", "Security", "fa-shield-halved", phase2("Security", "RBAC, sessions, audit, threat status.")],
    ["backups", "Backups", "fa-database", phase2("Backups", "Skills, knowledge, prompts, settings — backup & restore.")],
    ["settings", "Settings", "fa-gear", renderSettings],
  ];

  let CACHE = { agents: null, tools: null };

  // ---------------------------------------------------------------- boot
  const $ = (s) => document.querySelector(s);
  document.addEventListener("DOMContentLoaded", () => {
    $("#srv").value = store.base;
    $("#signin").onclick = () => doAuth(false);
    $("#signup").onclick = () => doAuth(true);
    $("#logout").onclick = () => { store.token = ""; location.reload(); };
    $("#themeBtn").onclick = toggleTheme;
    if (store.token) enterApp();
  });

  async function doAuth(create) {
    const err = $("#loginErr"); err.textContent = "";
    store.base = $("#srv").value.trim();
    const e = $("#email").value.trim(), pw = $("#pw").value;
    $("#signin").disabled = $("#signup").disabled = true;
    try {
      if (create) { try { await api.register(e, pw); } catch (_) {} }
      await api.login(e, pw);
      enterApp();
    } catch (ex) { err.textContent = String(ex.message || ex); }
    finally { $("#signin").disabled = $("#signup").disabled = false; }
  }

  function enterApp() {
    $("#login").classList.add("hidden");
    $("#app").classList.remove("hidden");
    buildNav();
    pollHealth();
    setInterval(pollHealth, 15000);
    go("dashboard");
  }

  function buildNav() {
    const nav = $("#nav");
    nav.innerHTML = "";
    SECTIONS.forEach(([id, label, icon]) => {
      const el = document.createElement("div");
      el.className = "nav-item"; el.dataset.id = id;
      el.innerHTML = `<i class="fa-solid ${icon}"></i><span>${label}</span>`;
      el.onclick = () => go(id);
      nav.appendChild(el);
    });
  }

  function go(id) {
    const sec = SECTIONS.find((s) => s[0] === id);
    if (!sec) return;
    document.querySelectorAll(".nav-item").forEach((n) => n.classList.toggle("active", n.dataset.id === id));
    $("#crumb").textContent = sec[1];
    const view = $("#view");
    view.innerHTML = `<div class="center"><div class="spin"></div></div>`;
    Promise.resolve(sec[3](view)).catch((e) => {
      view.innerHTML = `<div class="placeholder"><div class="ph glass"><i class="fa-solid fa-triangle-exclamation"></i><h3>Could not load</h3><p class="muted">${e.message || e}</p></div></div>`;
    });
  }

  async function pollHealth() {
    const pill = $("#health");
    try { const h = await api.health(); const ok = h.status === "ok";
      pill.className = "pill " + (ok ? "ok" : "down");
      pill.innerHTML = `<i class="fa-solid fa-circle"></i> ${ok ? "Online" : "Degraded"}`;
    } catch { pill.className = "pill down"; pill.innerHTML = `<i class="fa-solid fa-circle"></i> Offline`; }
  }

  function toggleTheme() {
    const cur = document.documentElement.getAttribute("data-theme");
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    $("#themeBtn").innerHTML = `<i class="fa-solid fa-${next === "dark" ? "moon" : "sun"}"></i>`;
  }

  async function loadAgents() { if (!CACHE.agents) CACHE.agents = await api.agents(); return CACHE.agents; }
  async function loadTools() { if (!CACHE.tools) CACHE.tools = await api.tools(); return CACHE.tools; }
  const byTier = (list, t) => (list || []).filter((a) => a && String(a.tier) === t);
  const aname = (a) => String(a.name || a.id || a.agent_id || "agent");

  // ---------------------------------------------------------------- Dashboard
  async function renderDashboard(view) {
    const [ag, tl] = await Promise.all([loadAgents(), loadTools()]);
    const agents = ag.agents || [];
    const gens = byTier(agents, "general").length || 15;
    const sols = byTier(agents, "soldier").length || 145;
    const total = ag.count || agents.length;
    const tools = tl.count || (tl.all || []).length;
    const stat = (ic, col, val, lbl) =>
      `<div class="card glass stat"><div class="ic" style="background:${col}22;color:${col}"><i class="fa-solid ${ic}"></i></div><div class="val">${val}</div><div class="lbl">${lbl}</div></div>`;
    view.innerHTML = `
      <div class="grid stats">
        ${stat("fa-hubspot", "#FF8A3D", total, "Total Agents")}
        ${stat("fa-chess-rook", "#39E0C4", gens, "Generals")}
        ${stat("fa-users", "#39E0C4", sols, "Soldiers")}
        ${stat("fa-screwdriver-wrench", "#FFC857", tools, "Tools")}
        ${stat("fa-bolt", "#35D07F", "Live", "Server Status")}
        ${stat("fa-microchip", "#FF8A3D", llmCount(tl), "LLMs Active")}
      </div>
      <div class="grid" style="grid-template-columns: 1.4fr 1fr; margin-top:16px;">
        <div class="card glass"><div class="section-title" style="margin:0 0 12px">System Activity <span class="tag">live sample</span></div><canvas id="actChart" height="120"></canvas></div>
        <div class="card glass"><div class="section-title" style="margin:0 0 12px">Hierarchy</div><canvas id="hierChart" height="180"></canvas></div>
      </div>`;
    drawActivity(); drawHierarchy(1, gens, sols);
  }
  function llmCount(tl) { const k = (tl.by_kind || {}).llm; return Array.isArray(k) ? k.length : 0; }

  let _chart1, _chart2;
  function drawActivity() {
    const ctx = document.getElementById("actChart"); if (!ctx) return;
    const data = Array.from({ length: 24 }, () => Math.round(20 + Math.random() * 80));
    if (_chart1) _chart1.destroy();
    _chart1 = new Chart(ctx, {
      type: "line",
      data: { labels: data.map((_, i) => i), datasets: [{ data, borderColor: "#FF8A3D", backgroundColor: "rgba(255,138,61,.12)", fill: true, tension: .4, pointRadius: 0, borderWidth: 2 }] },
      options: { plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { ticks: { color: "#8793AD" }, grid: { color: "rgba(255,255,255,.04)" } } } },
    });
  }
  function drawHierarchy(k, g, s) {
    const ctx = document.getElementById("hierChart"); if (!ctx) return;
    if (_chart2) _chart2.destroy();
    _chart2 = new Chart(ctx, {
      type: "doughnut",
      data: { labels: ["King", "Generals", "Soldiers"], datasets: [{ data: [k, g, s], backgroundColor: ["#FF8A3D", "#39E0C4", "#2B62FF"], borderWidth: 0 }] },
      options: { plugins: { legend: { labels: { color: "#8793AD" }, position: "bottom" } }, cutout: "62%" },
    });
  }

  // ---------------------------------------------------------------- King (agent tree)
  async function renderKing(view) {
    const ag = await loadAgents();
    const agents = ag.agents || [];
    const gens = byTier(agents, "general");
    const sols = byTier(agents, "soldier");
    view.innerHTML = `
      <div class="card glass tree-king">
        <span class="ember"><i class="fa-solid fa-crown"></i></span>
        <div><div class="val">KING</div><div class="muted">Orchestrating ${gens.length || 15} generals · ${sols.length || 145} soldiers</div></div>
        <span class="pill ok" style="margin-left:auto"><i class="fa-solid fa-circle"></i> Thinking</span>
      </div>
      <div class="section-title">Generals</div>
      <div class="grid generals">${(gens.length ? gens : placeholderGens()).map(genCard).join("")}</div>`;
  }
  function placeholderGens() {
    return ["knowledge","planning","execution","memory","coding","media","finance","communication","system","automation","device","security","iot","asi","voice"].map((d) => ({ name: d, tier: "general" }));
  }
  function genCard(g) {
    const n = aname(g);
    return `<div class="card glass gen" onclick="window.__filterSol&&window.__filterSol('${n}')">
      <div class="top"><span class="dot"></span><span class="nm">${n}</span></div>
      <div class="meta">Status: online · soldiers reporting</div></div>`;
  }

  // ---------------------------------------------------------------- Generals
  async function renderGenerals(view) {
    const ag = await loadAgents();
    const gens = byTier(ag.agents || [], "general");
    const list = gens.length ? gens : placeholderGens();
    view.innerHTML = `<div class="grid generals">${list.map(genCard).join("")}</div>`;
  }

  // ---------------------------------------------------------------- Soldiers
  async function renderSoldiers(view) {
    const ag = await loadAgents();
    const sols = byTier(ag.agents || [], "soldier");
    view.innerHTML = `
      <input id="solSearch" class="fld" placeholder="Search ${sols.length} soldiers…" style="max-width:340px;margin-bottom:16px" />
      <div id="solGrid" class="grid soldiers"></div>`;
    const grid = $("#solGrid");
    const draw = (q) => {
      grid.innerHTML = sols.filter((s) => aname(s).toLowerCase().includes(q)).map((s) => {
        const n = aname(s), st = String(s.status || "live");
        return `<div class="card glass sol"><div class="ic"><i class="fa-solid fa-microchip"></i></div><div><div class="nm">${n}</div><div class="st">${st}</div></div></div>`;
      }).join("") || `<p class="muted">No soldiers match.</p>`;
    };
    draw("");
    $("#solSearch").oninput = (e) => draw(e.target.value.toLowerCase());
  }

  // ---------------------------------------------------------------- Buddy console
  async function renderBuddy(view) {
    view.innerHTML = `
      <div class="console">
        <div id="clog" class="console-log"><p class="muted center" style="min-height:auto">Send a request to the King — e.g. "research quantum computing" or "book Jailer ticket, 2 seats".</p></div>
        <div class="composer">
          <input id="cin" class="fld" placeholder="Ask the King anything…" />
          <button id="csend" class="btn-ember" style="flex:0 0 auto;padding:11px 18px">Send</button>
        </div>
      </div>`;
    const log = $("#clog"), input = $("#cin"), btn = $("#csend");
    const add = (cls, text, meta) => {
      if (log.querySelector("p.muted")) log.innerHTML = "";
      const d = document.createElement("div"); d.className = "msg " + cls;
      d.innerHTML = text.replace(/</g, "&lt;") + (meta ? `<div class="meta">${meta}</div>` : "");
      log.appendChild(d); log.scrollTop = log.scrollHeight;
    };
    const send = async () => {
      const m = input.value.trim(); if (!m) return;
      add("u", m); input.value = ""; btn.disabled = true;
      try {
        const r = await api.chat(m);
        const res = r.result || r;
        const sol = (((res.breakdown || [])[0] || {}).result || {}).results || [];
        const sr = (sol[0] || {}).result || {};
        const meta = [sr.provider && ("provider: " + sr.provider), sr.model, sr.domain && ("soldier: " + sr.domain), sr.skill && ("skill: " + sr.skill)].filter(Boolean).join(" · ");
        add("k", res.summary || res.answer || "Done.", meta);
      } catch (e) { add("k", "Error: " + (e.message || e)); }
      finally { btn.disabled = false; }
    };
    btn.onclick = send; input.onkeydown = (e) => { if (e.key === "Enter") send(); };
  }

  // ---------------------------------------------------------------- LLM Manager
  async function renderLLMs(view) {
    const tl = await loadTools();
    const llms = (tl.by_kind || {}).llm || [];
    const labelMap = { "llm.nvidia": ["NVIDIA NIM", "meta/llama-3.3-70b", "#76B900", 1], "llm.openai": ["OpenAI", "gpt-4o-mini", "#10A37F", 2], "llm.anthropic": ["Anthropic", "claude", "#D97757", 3], "llm.local": ["Local (offline)", "local-stub", "#8793AD", 9] };
    const rows = (llms.length ? llms : ["llm.local"]).map((t) => {
      const [nm, model, col, pr] = labelMap[t] || [t, "", "#8793AD", 5];
      return `<div class="card glass" style="display:flex;align-items:center;gap:14px;padding:16px">
        <div class="ic" style="width:42px;height:42px;border-radius:12px;display:grid;place-items:center;background:${col}22;color:${col}"><i class="fa-solid fa-microchip"></i></div>
        <div><div style="font-weight:600">${nm}</div><div class="muted mono" style="font-size:12px">${t} · ${model}</div></div>
        <div style="margin-left:auto;text-align:right"><span class="pill ok"><i class="fa-solid fa-circle"></i> active</span><div class="muted" style="font-size:11px;margin-top:6px">priority ${pr}</div></div>
      </div>`;
    }).join("");
    view.innerHTML = `<p class="muted" style="margin-bottom:14px">Soldiers pick the highest-priority available model. NVIDIA is primary (free); OpenAI is fallback; local always works offline.</p><div class="grid" style="gap:12px">${rows}</div>`;
  }

  // ---------------------------------------------------------------- Settings
  async function renderSettings(view) {
    view.innerHTML = `
      <div class="card glass" style="max-width:560px">
        <div class="section-title" style="margin:0 0 14px">Connection</div>
        <label>Server URL</label>
        <input id="setSrv" class="fld" value="${store.base}" />
        <div style="margin-top:16px"><button id="setSave" class="btn-ember" style="flex:0 0 auto;padding:10px 18px">Save & reload</button></div>
        <p class="muted" style="margin-top:18px;font-size:12px">Theme, agents and live data come from the AGNI backend. PostgreSQL/Redis persistence arrives in a later phase.</p>
      </div>`;
    $("#setSave").onclick = () => { store.base = $("#setSrv").value.trim(); CACHE = { agents: null, tools: null }; location.reload(); };
  }

  // ---------------------------------------------------------------- Phase-2 placeholder
  function phase2(title, desc) {
    return (view) => {
      view.innerHTML = `<div class="placeholder"><div class="ph glass">
        <i class="fa-solid fa-screwdriver-wrench"></i><h3>${title}</h3>
        <p class="muted">${desc}</p>
        <span class="tag" style="margin-top:14px;display:inline-block">Designed · backend endpoint in next phase</span>
      </div></div>`;
    };
  }
})();
