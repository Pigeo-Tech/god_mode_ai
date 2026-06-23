# AGNI — Full King → General → Soldier Hierarchy

> Expanded from the 10-General base to the complete **AGNI** spec: **1 King · 15 Generals ·
> 145 Soldiers** (161 agents). Verified live — `bootstrap_system()` brings all of them up and the
> King routes across every domain. Package name stays `god_mode_ai`; **AGNI** is the product name.

## Counts (verified at boot)

- **King:** 1
- **Generals:** 15
- **Soldiers:** 145
- **Live in Agent Manager:** 160 (15 + 145); **+ King = 161 agents**
- **Tools:** 145 (144 soldier mock tools + `llm.local`; remote LLMs added when keys are set).
  The one custom soldier (`long_term_memory`) uses the Memory Manager instead of a tool.

## The 15 Generals and their rosters

| # | General | Mission | # Soldiers |
|---|---|---|---|
| 1 | Knowledge | Acquire and organize knowledge | 8 |
| 2 | Planning | Plan and schedule activities | 6 |
| 3 | Execution | Execute requested operations | 5 |
| 4 | Memory | Store, retrieve, manage memory | 8 |
| 5 | Coding | Software engineering | 6 |
| 6 | Media | Process multimedia | 8 |
| 7 | Finance | Financial intelligence | 8 |
| 8 | Communication | Handle communication | 7 |
| 9 | System | Infrastructure & cloud | 9 |
| 10 | Automation | Intelligent automation | 5 |
| 11 | **Device OS** | Manage the user's device | 20 |
| 12 | **Cyber Security** | Protect user, device, data | 13 |
| 13 | **IoT** | Manage smart devices | 12 |
| 14 | **ASI** | Continuously optimize AGNI | 18 |
| 15 | **Voice Intelligence** | Natural voice assistant | 12 |

Bold = the 5 new domains added in this expansion.

### Full soldier rosters

- **Knowledge:** internet, search, research, news, weather, maps, translation, knowledge_graph
- **Planning:** calendar, reminder, task_planning, project_planning, route_planning, goal_planning
- **Execution:** tool, api, terminal, workflow, automation
- **Memory:** long_term_memory*, short_term_memory, semantic_memory, context, file, ocr, pdf, vector_memory
- **Coding:** coding, debugging, git, docker, testing, deployment
- **Media:** image, video, audio, music, speech, vision, camera, editing
- **Finance:** banking, loan, credit_card, investment, stock, crypto, shopping, budget
- **Communication:** email, whatsapp, sms, call, notification, contacts, social_media
- **System:** aws, azure, gcp, database, kubernetes, authentication, monitoring, logging, devops
- **Automation:** trigger, scheduler, auto_workflow, api_automation, notification_automation
- **Device OS:** device_control, app_management, settings, flashlight, volume, brightness, battery,
  storage, file_manager, clipboard, dev_camera, gallery, phone, dev_contacts, bluetooth, wifi,
  nfc, sensor, accessibility, device_health
- **Cyber Security:** malware, antivirus, threat_detection, phishing, scam_detection,
  network_security, firewall, encryption, password, privacy, secure_vault, identity_protection,
  incident_response
- **IoT:** smart_home, smart_lighting, smart_camera, smart_tv, smart_speaker, appliance, vehicle,
  wearable, medical_iot, industrial_iot, energy_management, matter_protocol
- **ASI:** intelligence, reasoning, planning_optimization, performance, memory_optimization,
  cpu_optimization, gpu_optimization, battery_optimization, storage_optimization,
  cache_optimization, thermal_management, prediction, learning, decision, knowledge_evolution,
  ai_model_selection, resource_allocation, self_diagnostics
- **Voice Intelligence:** wake_word, speech_recognition, speaker_recognition, voice_biometrics,
  text_to_speech, noise_cancellation, emotion_detection, language_understanding,
  accent_adaptation, offline_voice, call_assistant, conversation

\* `long_term_memory` is the one custom soldier (backed by the Memory Manager). A few soldier
names collide across domains (Camera, Contacts, Workflow), so the colliding ones are
domain-prefixed for uniqueness — `dev_camera`, `dev_contacts`, `auto_workflow`.

## How it was built — generated, not hand-typed

Because soldiers are declarative and generals are data-driven, the whole hierarchy is generated
from one master spec into:

- `backend/generals/_spec.py` — `GENERAL_SPECS` (rosters + keyword routers) for all 15 domains.
- `backend/generals/<domain>/general.py` — 15 thin `BaseGeneral` subclasses reading their spec
  (Knowledge keeps a custom `aggregate()` that surfaces `findings`).
- `backend/generals/registry.py` — `GENERAL_CLASSES` with all 15.
- `backend/soldiers/catalog.py` — 145 `SoldierSpec` entries (unique, collision-resolved slugs).
- `backend/soldiers/tools.py` — 144 mock tools.
- `backend/king/king.py` — planner routes extended to device/security/iot/asi/voice.

Adding more later stays trivial: a General is a spec entry + a thin class; a Soldier is one
catalog line.

## Verified end-to-end

```
objective: "scan for malware then optimize performance"
  → King plans 2 steps (then = sequential)
  → general.security  → malware soldier   ✓
  → general.asi       → performance soldier ✓
  → 2/2 subtasks completed
```

Boot output: `soldiers=145, generals=15`. Full test suite: **86/86 passing** (counts updated to
145 soldiers / 15 generals / 160 live agents).
