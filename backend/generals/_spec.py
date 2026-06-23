"""AGNI hierarchy spec (generated). 15 Generals and their soldier rosters + routing."""
GENERAL_SPECS = {
    "knowledge": {
        "title": "Knowledge",
        "mission": "Acquire and organize knowledge.",
        "soldiers": [
            "internet",
            "search",
            "research",
            "news",
            "weather",
            "maps",
            "translation",
            "knowledge_graph"
        ],
        "keywords": {
            "internet": "internet",
            "search": "search",
            "research": "research",
            "news": "news",
            "weather": "weather",
            "maps": "maps",
            "translation": "translation",
            "knowledge": "knowledge_graph",
            "graph": "knowledge_graph"
        }
    },
    "planning": {
        "title": "Planning",
        "mission": "Plan and schedule activities.",
        "soldiers": [
            "calendar",
            "reminder",
            "task_planning",
            "project_planning",
            "route_planning",
            "goal_planning"
        ],
        "keywords": {
            "calendar": "calendar",
            "reminder": "reminder",
            "task": "task_planning",
            "planning": "task_planning",
            "project": "project_planning",
            "route": "route_planning",
            "goal": "goal_planning"
        }
    },
    "execution": {
        "title": "Execution",
        "mission": "Execute requested operations.",
        "soldiers": [
            "tool",
            "api",
            "terminal",
            "workflow",
            "automation"
        ],
        "keywords": {
            "tool": "tool",
            "api": "api",
            "terminal": "terminal",
            "workflow": "workflow",
            "automation": "automation"
        }
    },
    "memory": {
        "title": "Memory",
        "mission": "Store, retrieve, and manage memory.",
        "soldiers": [
            "long_term_memory",
            "short_term_memory",
            "semantic_memory",
            "context",
            "file",
            "ocr",
            "pdf",
            "vector_memory"
        ],
        "keywords": {
            "long": "long_term_memory",
            "term": "long_term_memory",
            "memory": "long_term_memory",
            "short": "short_term_memory",
            "semantic": "semantic_memory",
            "context": "context",
            "file": "file",
            "ocr": "ocr",
            "pdf": "pdf",
            "vector": "vector_memory"
        }
    },
    "coding": {
        "title": "Coding",
        "mission": "Software engineering and development.",
        "soldiers": [
            "coding",
            "debugging",
            "git",
            "docker",
            "testing",
            "deployment"
        ],
        "keywords": {
            "coding": "coding",
            "debugging": "debugging",
            "git": "git",
            "docker": "docker",
            "testing": "testing",
            "deployment": "deployment"
        }
    },
    "media": {
        "title": "Media",
        "mission": "Process multimedia.",
        "soldiers": [
            "image",
            "video",
            "audio",
            "music",
            "speech",
            "vision",
            "camera",
            "editing"
        ],
        "keywords": {
            "image": "image",
            "video": "video",
            "audio": "audio",
            "music": "music",
            "speech": "speech",
            "vision": "vision",
            "camera": "camera",
            "editing": "editing"
        }
    },
    "finance": {
        "title": "Finance",
        "mission": "Financial intelligence.",
        "soldiers": [
            "banking",
            "loan",
            "credit_card",
            "investment",
            "stock",
            "crypto",
            "shopping",
            "budget"
        ],
        "keywords": {
            "banking": "banking",
            "loan": "loan",
            "credit": "credit_card",
            "card": "credit_card",
            "investment": "investment",
            "stock": "stock",
            "crypto": "crypto",
            "shopping": "shopping",
            "budget": "budget"
        }
    },
    "communication": {
        "title": "Communication",
        "mission": "Handle communication.",
        "soldiers": [
            "email",
            "whatsapp",
            "sms",
            "call",
            "notification",
            "contacts",
            "social_media"
        ],
        "keywords": {
            "email": "email",
            "whatsapp": "whatsapp",
            "sms": "sms",
            "call": "call",
            "notification": "notification",
            "contacts": "contacts",
            "social": "social_media",
            "media": "social_media"
        }
    },
    "system": {
        "title": "System",
        "mission": "Infrastructure and cloud operations.",
        "soldiers": [
            "aws",
            "azure",
            "gcp",
            "database",
            "kubernetes",
            "authentication",
            "monitoring",
            "logging",
            "devops"
        ],
        "keywords": {
            "aws": "aws",
            "azure": "azure",
            "gcp": "gcp",
            "database": "database",
            "kubernetes": "kubernetes",
            "authentication": "authentication",
            "monitoring": "monitoring",
            "logging": "logging",
            "devops": "devops"
        }
    },
    "automation": {
        "title": "Automation",
        "mission": "Intelligent automation.",
        "soldiers": [
            "trigger",
            "scheduler",
            "auto_workflow",
            "api_automation",
            "notification_automation"
        ],
        "keywords": {
            "trigger": "trigger",
            "scheduler": "scheduler",
            "workflow": "auto_workflow",
            "api": "api_automation",
            "automation": "api_automation",
            "notification": "notification_automation"
        }
    },
    "device": {
        "title": "Device Operating System",
        "mission": "Manage the user's device.",
        "soldiers": [
            "device_control",
            "app_management",
            "settings",
            "flashlight",
            "volume",
            "brightness",
            "battery",
            "storage",
            "file_manager",
            "clipboard",
            "dev_camera",
            "gallery",
            "phone",
            "dev_contacts",
            "bluetooth",
            "wifi",
            "nfc",
            "sensor",
            "accessibility",
            "device_health"
        ],
        "keywords": {
            "device": "device_control",
            "control": "device_control",
            "app": "app_management",
            "management": "app_management",
            "settings": "settings",
            "flashlight": "flashlight",
            "volume": "volume",
            "brightness": "brightness",
            "battery": "battery",
            "storage": "storage",
            "file": "file_manager",
            "manager": "file_manager",
            "clipboard": "clipboard",
            "camera": "dev_camera",
            "gallery": "gallery",
            "phone": "phone",
            "contacts": "dev_contacts",
            "bluetooth": "bluetooth",
            "wifi": "wifi",
            "nfc": "nfc",
            "sensor": "sensor",
            "accessibility": "accessibility",
            "health": "device_health"
        }
    },
    "security": {
        "title": "Cyber Security",
        "mission": "Protect the user, device, and information.",
        "soldiers": [
            "malware",
            "antivirus",
            "threat_detection",
            "phishing",
            "scam_detection",
            "network_security",
            "firewall",
            "encryption",
            "password",
            "privacy",
            "secure_vault",
            "identity_protection",
            "incident_response"
        ],
        "keywords": {
            "malware": "malware",
            "antivirus": "antivirus",
            "threat": "threat_detection",
            "detection": "threat_detection",
            "phishing": "phishing",
            "scam": "scam_detection",
            "network": "network_security",
            "security": "network_security",
            "firewall": "firewall",
            "encryption": "encryption",
            "password": "password",
            "privacy": "privacy",
            "secure": "secure_vault",
            "vault": "secure_vault",
            "identity": "identity_protection",
            "protection": "identity_protection",
            "incident": "incident_response",
            "response": "incident_response"
        }
    },
    "iot": {
        "title": "IoT",
        "mission": "Manage connected smart devices.",
        "soldiers": [
            "smart_home",
            "smart_lighting",
            "smart_camera",
            "smart_tv",
            "smart_speaker",
            "appliance",
            "vehicle",
            "wearable",
            "medical_iot",
            "industrial_iot",
            "energy_management",
            "matter_protocol"
        ],
        "keywords": {
            "smart": "smart_home",
            "home": "smart_home",
            "lighting": "smart_lighting",
            "camera": "smart_camera",
            "speaker": "smart_speaker",
            "appliance": "appliance",
            "vehicle": "vehicle",
            "wearable": "wearable",
            "medical": "medical_iot",
            "iot": "medical_iot",
            "industrial": "industrial_iot",
            "energy": "energy_management",
            "management": "energy_management",
            "matter": "matter_protocol",
            "protocol": "matter_protocol"
        }
    },
    "asi": {
        "title": "ASI",
        "mission": "Continuously optimize AGNI.",
        "soldiers": [
            "intelligence",
            "reasoning",
            "planning_optimization",
            "performance",
            "memory_optimization",
            "cpu_optimization",
            "gpu_optimization",
            "battery_optimization",
            "storage_optimization",
            "cache_optimization",
            "thermal_management",
            "prediction",
            "learning",
            "decision",
            "knowledge_evolution",
            "ai_model_selection",
            "resource_allocation",
            "self_diagnostics"
        ],
        "keywords": {
            "intelligence": "intelligence",
            "reasoning": "reasoning",
            "planning": "planning_optimization",
            "optimization": "planning_optimization",
            "performance": "performance",
            "memory": "memory_optimization",
            "cpu": "cpu_optimization",
            "gpu": "gpu_optimization",
            "battery": "battery_optimization",
            "storage": "storage_optimization",
            "cache": "cache_optimization",
            "thermal": "thermal_management",
            "management": "thermal_management",
            "prediction": "prediction",
            "learning": "learning",
            "decision": "decision",
            "knowledge": "knowledge_evolution",
            "evolution": "knowledge_evolution",
            "model": "ai_model_selection",
            "selection": "ai_model_selection",
            "resource": "resource_allocation",
            "allocation": "resource_allocation",
            "self": "self_diagnostics",
            "diagnostics": "self_diagnostics"
        }
    },
    "voice": {
        "title": "Voice Intelligence",
        "mission": "Deliver a natural voice assistant experience.",
        "soldiers": [
            "wake_word",
            "speech_recognition",
            "speaker_recognition",
            "voice_biometrics",
            "text_to_speech",
            "noise_cancellation",
            "emotion_detection",
            "language_understanding",
            "accent_adaptation",
            "offline_voice",
            "call_assistant",
            "conversation"
        ],
        "keywords": {
            "wake": "wake_word",
            "word": "wake_word",
            "speech": "speech_recognition",
            "recognition": "speech_recognition",
            "speaker": "speaker_recognition",
            "voice": "voice_biometrics",
            "biometrics": "voice_biometrics",
            "text": "text_to_speech",
            "noise": "noise_cancellation",
            "cancellation": "noise_cancellation",
            "emotion": "emotion_detection",
            "detection": "emotion_detection",
            "language": "language_understanding",
            "understanding": "language_understanding",
            "accent": "accent_adaptation",
            "adaptation": "accent_adaptation",
            "offline": "offline_voice",
            "call": "call_assistant",
            "assistant": "call_assistant",
            "conversation": "conversation"
        }
    }
}
