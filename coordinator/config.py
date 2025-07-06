import os
from typing import Dict, List, Any
from pathlib import Path

# === LLM CONFIGURATION ===
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "phi3")
FALLBACK_MODELS = ["llama2", "mistral", "codellama"]

# Model-specific settings
MODEL_CONFIGS = {
    "phi3": {
        "temperature": 0.7,
        "num_predict": 2048,
        "top_p": 0.9,
        "top_k": 40
    },
    "llama2": {
        "temperature": 0.6,
        "num_predict": 1024,
        "top_p": 0.8,
        "top_k": 30
    },
    "mistral": {
        "temperature": 0.8,
        "num_predict": 2048,
        "top_p": 0.95,
        "top_k": 50
    }
}

# === SYSTEM FEATURES ===
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
ENABLE_MEMORY_PERSISTENCE = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
ENABLE_WEB_SCRAPING = os.getenv("ENABLE_WEB_SCRAPING", "true").lower() == "true"
ENABLE_EMAIL_SENDING = os.getenv("ENABLE_EMAIL", "false").lower() == "true"

# === WORKFLOW CONFIGURATION ===
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
WORKFLOW_TIMEOUT_SECONDS = int(os.getenv("WORKFLOW_TIMEOUT", "300"))
AGENT_EXECUTION_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "60"))

# === AGENT SETTINGS ===
AGENT_CONFIGS = {
    "idea_agent": {
        "max_ideas": 5,
        "creativity_weight": 0.7,
        "feasibility_weight": 0.3,
        "enable_web_research": True
    },
    "location_agent": {
        "max_locations": 8,
        "search_radius_km": 25,
        "enable_map_integration": True,
        "require_accessibility": False
    },
    "vendor_agent": {
        "max_vendors_per_category": 5,
        "enable_rating_filter": True,
        "min_rating_threshold": 3.5,
        "enable_price_comparison": True
    },
    "scheduler_agent": {
        "time_buffer_minutes": 15,
        "enable_conflict_detection": True,
        "max_schedule_iterations": 3
    },
    "invitation_agent": {
        "default_template": "elegant",
        "enable_custom_branding": True,
        "max_image_size_mb": 5
    },
    "reviewer_agent": {
        "quality_threshold": 0.8,
        "enable_sentiment_analysis": True,
        "max_revision_rounds": 2
    }
}

# === FILE HANDLING ===
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for dir_path in [OUTPUT_DIR, TEMP_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# File formats and sizes
SUPPORTED_EXPORT_FORMATS = ["pdf", "markdown", "ics", "json", "html"]
MAX_FILE_SIZE_MB = 50
PDF_SETTINGS = {
    "page_size": "A4",
    "margin_inches": 1,
    "font_family": "Arial",
    "include_images": True
}

# === EMAIL CONFIGURATION ===
EMAIL_SETTINGS = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "use_tls": os.getenv("USE_TLS", "true").lower() == "true",
    "max_recipients": 100,
    "attachment_limit_mb": 25
}

# === LOGGING CONFIGURATION ===
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_rotation": "daily",
    "max_files": 30
}

# === API RATE LIMITS ===
RATE_LIMITS = {
    "ollama_requests_per_minute": 60,
    "web_scraping_requests_per_minute": 30,
    "email_sends_per_hour": 100
}

# === VALIDATION RULES ===
VALIDATION_RULES = {
    "budget": {"min": 0, "max": 1000000},
    "guests": {"min": 1, "max": 10000},
    "duration_hours": {"min": 0.5, "max": 168},  # Up to 1 week
    "email_format": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
}

# === DEBUG SETTINGS ===
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
VERBOSE_LOGGING = os.getenv("VERBOSE", "false").lower() == "true"
PROFILE_PERFORMANCE = os.getenv("PROFILE", "false").lower() == "true"
