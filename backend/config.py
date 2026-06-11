from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

print("CONFIG FILE LOADED")

# backend folder path
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "ActivityMonitor"
    DEBUG: bool = True
    SECRET_KEY: str = "fallback-secret-key"

    # Database
    DATABASE_URL: str = "sqlite:///./activity_monitor.db"

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    AI_INSTRUCTION: str = """
Analyze the user's screen activity.

Requirements:
- Detect every visible application.
- Detect every visible website.
- Detect split-screen usage.
- Detect multiple windows shown simultaneously.
- Detect coding tools, AI tools, social media, communication apps, video platforms, office tools and productivity tools.
- If multiple websites are visible, identify each separately.
- If multiple applications are visible, identify each separately.
- If user-defined rules match any visible content, generate alerts.
- Provide a detailed activity summary.
- Provide a list of all visible items.
- Provide alerts for each matching rule.
"""

    # Screenshot Settings
    SCREENSHOT_INTERVAL_SECONDS: int = 60
    CHANGE_THRESHOLD: float = 0.005
    MAX_SCREENSHOTS_STORED: int = 500
    SCREENSHOT_QUALITY: int = 85

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # Storage
    UPLOAD_DIR: str = "uploads"


settings = Settings()

print("Current Directory:", Path.cwd())
print("Backend Directory:", BASE_DIR)
print("Env Path:", BASE_DIR / ".env")
print("Env Exists:", (BASE_DIR / ".env").exists())

print(
    "GEMINI KEY:",
    settings.GEMINI_API_KEY[:10]
    if settings.GEMINI_API_KEY
    else "NOT FOUND"
)

Path(settings.UPLOAD_DIR).mkdir(
    parents=True,
    exist_ok=True
)