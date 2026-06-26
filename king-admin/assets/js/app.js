/* AGNI King Command Center — Phase 1. Vanilla JS, talks to the live AGNI FastAPI backend. */
(() => {
  "use strict";

  // ---------------------------------------------------------------- API client
  const store = {
    get base() { return localStorage.getItem("agni_base") || "https://api.agentagni.online"; },
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
      if (r.status === 401) return api.onUnauthorized();
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    },
    async post(p, body) {
      const r = await fetch(store.base + p, { method: "POST", headers: api.headers(), body: JSON.stringify(body) });
      if (r.status === 401 && store.token) return api.onUnauthorized();
      if (!r.ok) { const t = await r.text(); throw new Error("HTTP " + r.status + ": " + t); }
      return r.json();
    },
    onUnauthorized() {
      // Stale/expired token (e.g. after a server redeploy) — drop it and return to login.
      if (store.token) { store.token = ""; location.reload(); }
      throw new Error("Session expired — please sign in again.");
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
    admin: (p) => api.get("/v1/admin/" + p),
    adminPost: (p, body) => api.post("/v1/admin/" + p, body),
  };

  // ---------------------------------------------------------------- navigation
  const SECTIONS = [
    ["dashboard", "Dashboard", "fa-gauge-high", renderDashboard],
    ["king", "King · Agent Tree", "fa-fire", renderKing],
    ["buddy", "Buddy Console", "fa-comments", renderBuddy],
    ["generals", "Generals", "fa-chess-rook", renderGenerals],
    ["soldiers", "Soldiers", "fa-users", renderSoldiers],
    ["skills", "Skills", "fa-scroll", renderSkills],
    ["llms", "LLM Manager", "fa-microchip", renderLLMs],
    ["knowledge", "Knowledge", "fa-book", renderKnowledge],
    ["memory", "Memory", "fa-brain", renderMemory],
    ["prompts", "Prompt Library", "fa-pen-nib", renderPrompts],
    ["users", "Users", "fa-user-shield", renderUsers],
    ["automation", "Automation", "fa-robot", renderAutomation],
    ["analytics", "Analytics", "fa-chart-line", renderAnalytics],
    ["wallet", "Wallet", "fa-wallet", renderWallet],
    ["apimgr", "API Manager", "fa-plug", renderApiMgr],
    ["logs", "Logs", "fa-list", renderLogs],
    ["security", "Security", "fa-shield-halved", renderSecurity],
    ["backups", "Backups", "fa-database", renderBackups],
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

  // ---------------------------------------------------------------- shared helpers
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const fmtBytes = (n) => { n = +n || 0; if (n < 1024) return n + " B"; if (n < 1048576) return (n / 1024).toFixed(1) + " KB"; return (n / 1048576).toFixed(1) + " MB"; };
  const fmtDur = (s) => { s = +s || 0; const d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60); return d ? `${d}d ${h}h` : h ? `${h}h ${m}m` : `${m}m`; };
  const ago = (ts) => { if (!ts) return "—"; const s = Date.now() / 1000 - ts; if (s < 60) return Math.floor(s) + "s ago"; if (s < 3600) return Math.floor(s / 60) + "m ago"; if (s < 86400) return Math.floor(s / 3600) + "h ago"; return Math.floor(s / 86400) + "d ago"; };
  const note = (t) => `<p class="muted" style="margin:16px 2px 0;font-size:12px">${esc(t)}</p>`;
  const title = (t, tag) => `<div class="section-title">${esc(t)}${tag ? ` <span class="tag">${esc(tag)}</span>` : ""}</div>`;
  const stat = (ic, col, val, lbl) => `<div class="card glass stat"><div class="ic" style="background:${col}22;color:${col}"><i class="fa-solid ${ic}"></i></div><div class="val">${val}</div><div class="lbl">${esc(lbl)}</div></div>`;
  const pill = (ok, txt) => `<span class="pill ${ok ? "ok" : "down"}"><i class="fa-solid fa-circle"></i> ${esc(txt)}</span>`;

  // ---------------------------------------------------------------- Skills
  async function renderSkills(view) {
    const d = await api.admin("skills");
    const cards = (d.skills || []).map((s) => `
      <div class="card glass">
        <div style="display:flex;align-items:center;gap:10px">
          <span class="ember sm"><i class="fa-solid fa-scroll"></i></span>
          <div style="font-weight:600">${esc(s.name)}</div>
          <span class="tag" style="margin-left:auto">${s.chars} chars</span>
        </div>
        <p class="muted" style="margin:10px 0 8px">${esc(s.description) || "No description."}</p>
        <pre class="mono" style="white-space:pre-wrap;font-size:11px;max-height:120px;overflow:auto;background:rgba(255,255,255,.03);padding:10px;border-radius:8px;margin:0">${esc(s.preview)}</pre>
      </div>`).join("");
    view.innerHTML = title(`Skills · ${d.count}`, "SKILL.md") +
      `<div class="card glass" style="margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
          <span class="ember sm"><i class="fa-solid fa-plus"></i></span>
          <div style="font-weight:600">Teach AGNI a new skill</div>
          <label class="btn-ghost" style="margin-left:auto;cursor:pointer;font-size:12px;padding:7px 12px">
            <i class="fa-solid fa-file-arrow-up"></i> Load .md file
            <input id="skFile" type="file" accept=".md,.markdown,text/markdown,text/plain" style="display:none" />
          </label>
        </div>
        <input id="skName" class="fld" placeholder="Skill name (e.g. invoice-parser)" style="margin-bottom:10px" />
        <textarea id="skBody" class="fld" rows="8" placeholder="Paste SKILL.md content here. Frontmatter (--- name / description ---) is optional — it'll be added automatically." style="resize:vertical;font-family:'JetBrains Mono',monospace;font-size:12px"></textarea>
        <div style="display:flex;align-items:center;gap:12px;margin-top:12px">
          <button id="skSave" class="btn-ember" style="flex:0 0 auto;padding:10px 18px">Save skill</button>
          <span id="skMsg" class="muted" style="font-size:12px"></span>
        </div>
      </div>
      <div class="grid" style="gap:12px">${cards || `<p class="muted">No skills loaded yet.</p>`}</div>` + note(d.note);
    const nameEl = $("#skName"), bodyEl = $("#skBody"), msg = $("#skMsg");
    $("#skFile").onchange = (e) => {
      const f = e.target.files[0]; if (!f) return;
      const r = new FileReader();
      r.onload = () => { bodyEl.value = r.result; if (!nameEl.value) nameEl.value = f.name.replace(/\.(md|markdown|txt)$/i, ""); };
      r.readAsText(f);
    };
    $("#skSave").onclick = async () => {
      const name = nameEl.value.trim(), content = bodyEl.value.trim();
      if (!name || !content) { msg.textContent = "Name and content are required."; return; }
      msg.textContent = "Saving…"; $("#skSave").disabled = true;
      try {
        const r = await api.adminPost("skills", { name, content });
        msg.innerHTML = `<span style="color:var(--good)">Saved "${esc(r.name)}" · ${r.count} skills loaded.</span>`;
        setTimeout(() => go("skills"), 700);
      } catch (ex) { msg.innerHTML = `<span style="color:var(--bad)">${esc(ex.message || ex)}</span>`; }
      finally { $("#skSave").disabled = false; }
    };
  }

  // ---------------------------------------------------------------- Knowledge
  async function renderKnowledge(view) {
    const d = await api.admin("knowledge");
    const rows = (d.documents || []).map((doc) => `
      <div class="card glass" style="display:flex;align-items:center;gap:14px;padding:14px 16px">
        <span class="ic" style="width:38px;height:38px;border-radius:10px;display:grid;place-items:center;background:#2B62FF22;color:#5B8CFF"><i class="fa-solid fa-folder-open"></i></span>
        <div><div style="font-weight:600">${esc(doc.name)}</div><div class="muted" style="font-size:12px">${(doc.files || []).map(esc).join(" · ") || "—"}</div></div>
        <span class="tag" style="margin-left:auto">${fmtBytes(doc.bytes)}</span>
      </div>`).join("");
    view.innerHTML = title(`Knowledge Base · ${d.count} sources`, `${d.skills_indexed} indexed`) +
      `<div class="grid" style="gap:10px">${rows || `<p class="muted">No knowledge sources yet.</p>`}</div>` +
      note("Knowledge sources are the SKILL.md folders AGNI learns from. Add a folder under backend/skills/ to teach a new capability.");
  }

  // ---------------------------------------------------------------- Memory
  async function renderMemory(view) {
    const d = await api.admin("memory");
    view.innerHTML = title("Memory System", d.backend) +
      `<div class="grid stats">
        ${stat("fa-pen", "#FF8A3D", d.writes, "Memories Written")}
        ${stat("fa-magnifying-glass", "#39E0C4", d.reads, "Recalls")}
        ${stat("fa-layer-group", "#2B62FF", (d.scopes || []).length, "Memory Scopes")}
      </div>
      <div class="card glass" style="margin-top:16px">
        ${title("Scopes")}
        <div style="display:flex;flex-wrap:wrap;gap:8px">${(d.scopes || []).map((s) => `<span class="tag">${esc(s)}</span>`).join("")}</div>
        ${title("Backing Stores")}
        <div class="muted mono" style="font-size:12px">${Object.entries(d.stores || {}).map(([k, v]) => `${k}: ${esc(v)}`).join("<br>")}</div>
      </div>` + note(d.note);
  }

  // ---------------------------------------------------------------- Prompt Library
  async function renderPrompts(view) {
    const d = await api.admin("prompts");
    const cards = (d.prompts || []).map((p) => `
      <div class="card glass">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
          <span class="dot"></span><div style="font-weight:600;text-transform:capitalize">${esc(p.domain)}</div>
          <span class="tag" style="margin-left:auto">${(p.preferred_models || []).map((m) => esc(m.replace("llm.", ""))).join(" › ")}</span>
        </div>
        <p class="muted" style="margin:0">${esc(p.system_prompt)}</p>
      </div>`).join("");
    view.innerHTML = title(`Prompt Library · ${d.count} domains`) +
      `<div class="grid" style="gap:12px">${cards}</div>
       <div class="card glass" style="margin-top:14px">${title("Action voice")}<p class="muted" style="margin:0">${esc(d.action_voice)}</p></div>` +
      note(d.note);
  }

  // ---------------------------------------------------------------- Users
  async function renderUsers(view) {
    const d = await api.admin("users");
    const rows = (d.users || []).map((u) => `
      <tr>
        <td>${esc(u.email)}</td>
        <td>${(u.roles || []).map((r) => `<span class="tag">${esc(r)}</span>`).join(" ")}</td>
        <td class="mono" style="font-size:11px">${(u.scopes || []).map(esc).join(", ") || "—"}</td>
        <td>${u.last_login ? ago(u.last_login) : `<span class="muted">never</span>`}</td>
      </tr>`).join("");
    view.innerHTML = title(`Users · ${d.count}`) +
      `<div class="card glass" style="overflow:auto"><table class="tbl">
        <thead><tr><th>Email</th><th>Roles</th><th>Scopes</th><th>Last login</th></tr></thead>
        <tbody>${rows || `<tr><td colspan="4" class="muted">No users registered.</td></tr>`}</tbody>
      </table></div>` +
      note("Users register through Buddy or the admin login. Roles map to scopes via the Permission Manager.");
  }

  // ---------------------------------------------------------------- Automation
  async function renderAutomation(view) {
    const d = await api.admin("automation");
    const caps = (d.capabilities || []).map((c) => `
      <div class="card glass" style="display:flex;align-items:center;gap:14px;padding:14px 16px">
        <span class="ic" style="width:38px;height:38px;border-radius:10px;display:grid;place-items:center;background:#35D07F22;color:#35D07F"><i class="fa-solid fa-robot"></i></span>
        <div><div style="font-weight:600">${esc(c.name)}</div><div class="muted" style="font-size:12px">${esc(c.detail)}</div></div>
        <span style="margin-left:auto">${pill(c.status === "active", c.status)}</span>
      </div>`).join("");
    view.innerHTML = title("Automation") +
      `<div class="grid stats">
        ${stat("fa-clock", "#FF8A3D", (d.scheduled_jobs || []).length, "Scheduled Jobs")}
        ${stat("fa-bolt", "#39E0C4", d.jobs_fired, "Jobs Fired")}
        ${stat("fa-diagram-project", "#2B62FF", d.workflow_steps, "Workflow Steps")}
      </div>
      <div style="margin-top:16px">${title("Capabilities")}<div class="grid" style="gap:10px">${caps}</div></div>`;
  }

  // ---------------------------------------------------------------- Analytics
  async function renderAnalytics(view) {
    const d = await api.admin("analytics");
    view.innerHTML = title("Analytics", "live") +
      `<div class="grid stats">
        ${stat("fa-paper-plane", "#FF8A3D", d.total_requests, "Total Requests")}
        ${stat("fa-microchip", "#39E0C4", d.soldier_runs, "Soldier Runs")}
        ${stat("fa-screwdriver-wrench", "#FFC857", d.tool_invocations, "Tool Calls")}
        ${stat("fa-clock", "#35D07F", fmtDur(d.uptime_seconds), "Uptime")}
      </div>
      <div class="grid" style="grid-template-columns:1fr 1fr;margin-top:16px;gap:16px">
        <div class="card glass">${title("Requests by Model Provider")}<canvas id="provChart" height="160"></canvas></div>
        <div class="card glass">${title("Event Counters")}<div id="ctrList" class="mono" style="font-size:12px;max-height:220px;overflow:auto"></div></div>
      </div>`;
    const usage = d.provider_usage || {};
    const labels = Object.keys(usage), vals = Object.values(usage);
    const ctx = document.getElementById("provChart");
    if (ctx && labels.length) new Chart(ctx, { type: "bar", data: { labels, datasets: [{ data: vals, backgroundColor: ["#76B900", "#10A37F", "#D97757", "#5B8CFF", "#8793AD"] }] }, options: { plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#8793AD" }, grid: { display: false } }, y: { ticks: { color: "#8793AD" }, grid: { color: "rgba(255,255,255,.04)" } } } } });
    else if (ctx) ctx.parentElement.innerHTML = title("Requests by Model Provider") + `<p class="muted">No requests yet — ask the King something in Buddy Console.</p>`;
    const cl = document.getElementById("ctrList");
    if (cl) cl.innerHTML = Object.entries(d.counters || {}).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid rgba(255,255,255,.04)"><span>${esc(k)}</span><span style="color:#FF8A3D">${v}</span></div>`).join("") || `<p class="muted">No metrics yet.</p>`;
  }

  // ---------------------------------------------------------------- Wallet
  async function renderWallet(view) {
    const d = await api.admin("wallet");
    const usage = Object.entries(d.provider_usage || {});
    view.innerHTML = title("Wallet & Cost") +
      `<div class="grid stats">
        ${stat("fa-coins", "#FFC857", "$" + (d.estimated_ai_cost ?? 0), "Est. AI Cost")}
        ${stat("fa-shield-halved", "#35D07F", "Gated", "Spend Control")}
        ${stat("fa-receipt", "#39E0C4", usage.reduce((a, [, v]) => a + v, 0), "Billable Answers")}
      </div>
      <div class="card glass" style="margin-top:16px">
        ${title("Usage by provider")}
        ${usage.length ? usage.map(([p, v]) => `<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.05)"><span style="text-transform:capitalize">${esc(p)}</span><span class="muted">${v} answers · $${((d.pricing_per_answer || {})[p] || 0)}/answer</span></div>`).join("") : `<p class="muted">No billable usage yet (NVIDIA + local are free).</p>`}
      </div>` + note(d.note);
  }

  // ---------------------------------------------------------------- API Manager
  async function renderApiMgr(view) {
    const d = await api.admin("apikeys");
    const rows = (d.providers || []).map((p) => `
      <div class="card glass" style="display:flex;align-items:center;gap:14px;padding:14px 16px">
        <span class="ic" style="width:38px;height:38px;border-radius:10px;display:grid;place-items:center;background:#FF8A3D22;color:#FF8A3D"><i class="fa-solid fa-plug"></i></span>
        <div><div style="font-weight:600">${esc(p.label)} ${p.free ? `<span class="tag">free</span>` : ""}</div><div class="muted mono" style="font-size:11px">${esc(p.tool)} · ${esc(p.model)} · priority ${p.priority}</div></div>
        <span style="margin-left:auto">${p.configured ? pill(true, p.registered ? "active" : "configured") : pill(false, "not set")}</span>
      </div>`).join("");
    const svc = Object.entries(d.services || {}).map(([k, v]) => `<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.05)"><span>${esc(k)}</span>${v ? pill(true, "configured") : pill(false, "not set")}</div>`).join("");
    view.innerHTML = title("API Manager", `${d.tools_total} tools`) +
      `<div class="grid" style="gap:10px">${rows}</div>
       <div class="card glass" style="margin-top:14px">${title("Services")}${svc}</div>` + note(d.note);
  }

  // ---------------------------------------------------------------- Logs
  async function renderLogs(view) {
    const d = await api.admin("logs");
    const icon = { system: "fa-server", chat: "fa-comment", auth: "fa-key", error: "fa-triangle-exclamation" };
    const rows = (d.events || []).map((e) => `
      <div style="display:flex;gap:12px;align-items:flex-start;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.05)">
        <i class="fa-solid ${icon[e.kind] || "fa-circle-info"}" style="color:#FF8A3D;margin-top:3px"></i>
        <div style="flex:1"><div><b>${esc(e.event)}</b> ${e.detail ? `<span class="muted">— ${esc(e.detail)}</span>` : ""}</div>
        <div class="muted" style="font-size:11px">${esc(e.kind)}${e.user ? " · " + esc(e.user) : ""} · ${ago(e.ts)}</div></div>
      </div>`).join("");
    view.innerHTML = title(`Audit Logs · ${d.count}`) +
      `<div class="card glass">${rows || `<p class="muted">No events recorded yet.</p>`}</div>`;
  }

  // ---------------------------------------------------------------- Security
  async function renderSecurity(view) {
    const d = await api.admin("security");
    const roles = Object.entries(d.rbac_roles || {}).map(([r, sc]) => `<div style="display:flex;gap:10px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.05)"><span class="tag">${esc(r)}</span><span class="muted mono" style="font-size:12px">${(sc || []).map(esc).join(", ")}</span></div>`).join("");
    view.innerHTML = title("Security", d.threat_status) +
      `<div class="grid stats">
        ${stat("fa-user-shield", "#35D07F", d.users_total, "Users")}
        ${stat("fa-right-to-bracket", "#39E0C4", d.sessions_seen, "Sessions Seen")}
        ${stat("fa-list-check", "#FF8A3D", d.audit_events, "Audit Events")}
      </div>
      <div class="grid" style="grid-template-columns:1fr 1fr;margin-top:16px;gap:16px">
        <div class="card glass">${title("Authentication")}
          <div class="muted" style="line-height:1.9">
            Method: <b style="color:var(--ink)">${esc(d.auth.method)}</b><br>
            Algorithm: ${esc(d.auth.algorithm)}<br>
            Token TTL: ${esc(d.auth.access_token_minutes)} min<br>
            Transport: ${esc(d.transport)}<br>
            CORS: ${esc(d.cors)}<br>
            Secrets: ${esc(d.secrets)}
          </div>
        </div>
        <div class="card glass">${title("RBAC roles → scopes")}${roles || `<p class="muted">Default roles.</p>`}</div>
      </div>`;
  }

  // ---------------------------------------------------------------- Backups
  async function renderBackups(view) {
    const d = await api.admin("backups");
    const p = d.policy || {};
    const arch = (d.local_archives || []).map((a) => `<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.05)"><span class="mono" style="font-size:12px">${esc(a.name)}</span><span class="muted">${fmtBytes(a.bytes)} · ${ago(a.modified)}</span></div>`).join("");
    view.innerHTML = title("Backups") +
      `<div class="card glass">${title("Policy")}
        <div class="muted" style="line-height:1.9">
          Backs up: ${(p.what || []).map((x) => `<span class="tag">${esc(x)}</span>`).join(" ")}<br>
          Target: <b style="color:var(--ink)">${esc(p.target)}</b><br>
          Schedule: ${esc(p.schedule)}<br>
          Retention: ${esc(p.retention)}<br>
          Script: <span class="mono">${esc(d.script)}</span>
        </div>
      </div>
      <div class="card glass" style="margin-top:14px">${title(`Local archives · ${(d.local_archives || []).length}`)}${arch || `<p class="muted">No local archives yet. Backups are pushed to Hostinger when the cron job runs.</p>`}</div>` +
      note(d.note);
  }
})();
