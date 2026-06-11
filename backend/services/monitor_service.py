import json
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import SessionLocal
from backend.models.db_models import Screenshot, AIAnalysis, Alert, UserRule
from backend.services.ai_service import analyze_screenshot
from backend.services.change_detector import compute_change_score, is_significant_change
from backend.services.background_monitor import analyze_background_apps
from backend.config import settings

# ---------------- STATE ----------------
_monitor_state = {
    "is_running": False,
    "last_image_bytes": None,
    "last_description": "",
    "screenshots_taken": 0,
    "alerts_triggered": 0,
}

_websocket_clients = set()

# ---------------- STATUS ----------------
def get_monitor_status():
    return {
        "is_running": _monitor_state["is_running"],
        "screenshots_taken": _monitor_state["screenshots_taken"],
        "alerts_triggered": _monitor_state["alerts_triggered"],
    }

def add_websocket_client(ws):
    _websocket_clients.add(ws)

def remove_websocket_client(ws):
    _websocket_clients.discard(ws)

# ---------------- CORE LOGIC ----------------
def process_uploaded_screenshot(img_bytes: bytes, filename: str, filepath: str, width: int = 1920, height: int = 1080, active_window: str = "Browser Capture", active_app: str = "Browser", all_windows: list = None):
    """Process a screenshot uploaded by the frontend."""
    if all_windows is None:
        all_windows = []

    try:
        # 1. Background apps — used as context for AI, not for direct alerts
        background_info = analyze_background_apps()

        # Build background context string for AI (not displayed to user)
        bg_context = ""
        if background_info.get("changes"):
            context_parts = []
            for change in background_info["changes"]:
                if change["type"] == "new_apps":
                    context_parts.append(f"New applications opened: {', '.join(change['data'])}")
                elif change["type"] == "closed_apps":
                    context_parts.append(f"Applications closed: {', '.join(change['data'])}")
                elif change["type"] == "new_windows":
                    context_parts.append(f"New windows opened: {', '.join(change['data'])}")
                elif change["type"] == "closed_windows":
                    context_parts.append(f"Windows closed: {', '.join(change['data'])}")
            bg_context = "\n".join(context_parts)

        # 2. Change detection — only proceed for significant visual changes
        change_score = 0.0

        if _monitor_state["last_image_bytes"] is not None:
            change_score = compute_change_score(
                _monitor_state["last_image_bytes"],
                img_bytes
            )

            # Let frontend dictate rate, but we can still skip AI processing if no change
            # Actually, since frontend sends it, let's always process it if it's sent, 
            # or we can still drop it to save API calls. Let's drop it to save API calls.
            if not is_significant_change(change_score, settings.CHANGE_THRESHOLD):
                print(f"Skipping processing: Change score {change_score:.2%} below threshold.")
                return {"status": "skipped", "reason": "no_significant_change", "change_score": change_score}

        _monitor_state["last_image_bytes"] = img_bytes

        # 3. Save screenshot to database
        db: Session = SessionLocal()

        try:
            screenshot = Screenshot(
                filename=filename,
                filepath=filepath,
                active_window=active_window,
                active_app=active_app,
                all_windows=json.dumps(all_windows),
                change_score=change_score,
                width=width,
                height=height,
            )

            db.add(screenshot)
            db.commit()
            db.refresh(screenshot)

            _monitor_state["screenshots_taken"] += 1

            # 4. Load user-defined rules
            active_rules = db.query(UserRule).filter(UserRule.is_active == True).all()
            rules_for_ai = [{"name": r.name, "prompt": r.prompt} for r in active_rules]

            # 5. AI Analysis
            ai_result = analyze_screenshot(
                img_bytes,
                rules_for_ai,
                settings.AI_INSTRUCTION,
                _monitor_state["last_description"],
                bg_context
            )
            print("AI RESULT:", json.dumps(ai_result, indent=2))

            _monitor_state["last_description"] = ai_result.get("description", "")

            # 6. Save AI Result
            importance = ai_result.get("change_importance", "low")
            summary_to_save = ai_result.get("summary", "")

            if importance == "low" and _monitor_state.get("last_summary"):
                summary_to_save = _monitor_state["last_summary"]
            else:
                _monitor_state["last_summary"] = summary_to_save

            analysis = AIAnalysis(
                screenshot_id=screenshot.id,
                description=ai_result.get("description"),
                activity_type=ai_result.get("activity_type"),
                detected_apps=json.dumps(ai_result.get("detected_apps", [])),
                summary=summary_to_save,
                raw_response=ai_result.get("raw_response"),
                processing_time_ms=ai_result.get("processing_time_ms"),
            )

            db.add(analysis)
            db.commit()

            # 7. Create alerts ONLY from AI rule-matching (user-defined rules)
            new_alerts = []

            for alert_data in ai_result.get("alerts", []):
                if alert_data.get("triggered"):
                    rule_name_lower = str(alert_data.get("rule_name", "")).strip().lower()
                    matching_rule = next(
                        (r for r in active_rules if r.name.strip().lower() == rule_name_lower or r.name.strip().lower() in rule_name_lower or rule_name_lower in r.name.strip().lower()),
                        None
                    )

                    alert = Alert(
                        screenshot_id=screenshot.id,
                        rule_id=(matching_rule.id if matching_rule else None),
                        title=alert_data.get("title", "Activity Detected"),
                        message=alert_data.get("message", ""),
                        severity=alert_data.get("severity", "info"),
                    )

                    db.add(alert)
                    new_alerts.append(alert_data)
                    _monitor_state["alerts_triggered"] += 1

            db.commit()

            print(f"Screenshot {screenshot.id} | Change: {change_score:.2%} | Importance: {importance} | Rule Alerts: {len(new_alerts)}")
            return {"status": "processed", "screenshot_id": screenshot.id, "change_score": change_score, "alerts": len(new_alerts)}

        finally:
            db.close()

    except Exception as e:
        print("Monitor error processing screenshot:", e)
        return {"status": "error", "message": str(e)}

# ---------------- CONTROL ----------------
def start_monitor():
    _monitor_state["is_running"] = True
    return True, "Monitor started"

def stop_monitor():
    _monitor_state["is_running"] = False
    return True, "Monitor stopped"