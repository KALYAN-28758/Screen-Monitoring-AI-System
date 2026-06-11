from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class UserRule(Base):
    """
    Stores the user's custom monitoring rules/prompts.
    Example: "Alert me when I open YouTube" or "Notify if coding stops"
    """
    __tablename__ = "user_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)           # Rule display name
    prompt = Column(Text, nullable=False)                # Natural language rule
    is_active = Column(Boolean, default=True)            # Can be toggled on/off
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # One rule can generate many alerts
    alerts = relationship("Alert", back_populates="rule")


class Screenshot(Base):
    """
    Stores each captured screenshot with metadata.
    """
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)       # Image file name
    filepath = Column(String(500), nullable=False)       # Full path to image
    active_window = Column(String(255), nullable=True)   # Window title at capture
    active_app = Column(String(255), nullable=True)      # App name at capture
    all_windows = Column(Text, nullable=True)            # JSON list of all open windows
    change_score = Column(Float, default=0.0)            # How much screen changed (0-1)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())

    # One screenshot can have one AI analysis
    analysis = relationship("AIAnalysis", back_populates="screenshot", uselist=False)
    # One screenshot can trigger many alerts
    alerts = relationship("Alert", back_populates="screenshot")


class AIAnalysis(Base):
    """
    Stores the AI-generated analysis for each screenshot.
    """
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    screenshot_id = Column(Integer, ForeignKey("screenshots.id"), nullable=False)
    description = Column(Text, nullable=True)            # What AI sees on screen
    activity_type = Column(String(100), nullable=True)   # e.g., "coding", "browsing"
    detected_apps = Column(Text, nullable=True)          # JSON list of detected apps
    summary = Column(Text, nullable=True)                # Short summary of change
    raw_response = Column(Text, nullable=True)           # Full AI response (for debug)
    processing_time_ms = Column(Integer, nullable=True)  # How long AI took
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

    screenshot = relationship("Screenshot", back_populates="analysis")


class Alert(Base):
    """
    Stores alerts triggered when AI detects something matching user rules.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    screenshot_id = Column(Integer, ForeignKey("screenshots.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("user_rules.id"), nullable=True)
    title = Column(String(255), nullable=False)          # Alert headline
    message = Column(Text, nullable=False)               # Detailed alert message
    severity = Column(String(50), default="info")        # info / warning / critical
    is_read = Column(Boolean, default=False)             # Has user seen this?
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())

    screenshot = relationship("Screenshot", back_populates="alerts")
    rule = relationship("UserRule", back_populates="alerts")