from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ──────────────────────────────────────────
# USER RULES
# ──────────────────────────────────────────

class UserRuleCreate(BaseModel):
    name: str
    prompt: str
    is_active: bool = True

class UserRuleUpdate(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    is_active: Optional[bool] = None

class UserRuleResponse(BaseModel):
    id: int
    name: str
    prompt: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────
# SCREENSHOTS
# ──────────────────────────────────────────

class ScreenshotResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    active_window: Optional[str]
    active_app: Optional[str]
    change_score: float
    width: Optional[int]
    height: Optional[int]
    captured_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────
# AI ANALYSIS
# ──────────────────────────────────────────

class AIAnalysisResponse(BaseModel):
    id: int
    screenshot_id: int
    description: Optional[str]
    activity_type: Optional[str]
    summary: Optional[str]
    analyzed_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────
# ALERTS
# ──────────────────────────────────────────

class AlertResponse(BaseModel):
    id: int
    screenshot_id: int
    rule_id: Optional[int]
    title: str
    message: str
    severity: str
    is_read: bool
    triggered_at: datetime

    class Config:
        from_attributes = True

class AlertMarkRead(BaseModel):
    alert_ids: List[int]


# ──────────────────────────────────────────
# DASHBOARD (combined response)
# ──────────────────────────────────────────

class DashboardItem(BaseModel):
    screenshot: ScreenshotResponse
    analysis: Optional[AIAnalysisResponse]
    alerts: List[AlertResponse]

    class Config:
        from_attributes = True


# ──────────────────────────────────────────
# MONITOR CONTROL
# ──────────────────────────────────────────

class MonitorStatus(BaseModel):
    is_running: bool
    message: str

class MonitorControl(BaseModel):
    action: str   # "start" or "stop"

# ──────────────────────────────────────────
# SETTINGS
# ──────────────────────────────────────────

class MonitorSettings(BaseModel):
    screenshot_interval_seconds: int