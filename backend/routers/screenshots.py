from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models.db_models import Screenshot, AIAnalysis, Alert, UserRule
from backend.schemas.schemas import ScreenshotResponse, DashboardItem
from backend.services.monitor_service import process_uploaded_screenshot
from backend.config import settings
from datetime import datetime
import json
import os
import io

router = APIRouter(prefix="/api/screenshots", tags=["Screenshots"])


@router.get("/", response_model=List[ScreenshotResponse])
def get_screenshots(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get recent screenshots with pagination."""
    return (
        db.query(Screenshot)
        .order_by(Screenshot.captured_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/latest")
def get_latest_screenshot(db: Session = Depends(get_db)):
    """Get the latest screenshot for the dashboard."""
    latest = (
        db.query(Screenshot)
        .order_by(Screenshot.captured_at.desc())
        .first()
    )
    
    if not latest:
        return {
            "image_url": None,
            "message": "No screenshots available yet"
        }
    
    # Get the AI analysis associated with this screenshot
    analysis = db.query(AIAnalysis).filter(AIAnalysis.screenshot_id == latest.id).first()
    
    all_windows = []
    if latest.all_windows:
        try:
            all_windows = json.loads(latest.all_windows)
        except Exception:
            all_windows = []
            
    detected_apps = []
    if analysis and analysis.detected_apps:
        try:
            detected_apps = json.loads(analysis.detected_apps)
        except Exception:
            detected_apps = []
            
    return {
        "image_url": f"/uploads/screenshots/{latest.filename}",
        "screenshot_id": latest.id,
        "captured_at": latest.captured_at,
        "active_app": latest.active_app,
        "active_window": latest.active_window,
        "change_score": latest.change_score,
        "all_windows": all_windows,
        "detected_apps": detected_apps,
        "summary": analysis.summary if analysis else "",
        "description": analysis.description if analysis else ""
    }


@router.get("/dashboard", response_model=List[DashboardItem])
def get_dashboard(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Get screenshots with their AI analysis and alerts combined.
    This powers the main dashboard view.
    """
    screenshots = (
        db.query(Screenshot)
        .order_by(Screenshot.captured_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    result = []
    for screenshot in screenshots:
        analysis = db.query(AIAnalysis).filter(
            AIAnalysis.screenshot_id == screenshot.id
        ).first()
        
        alerts = db.query(Alert).filter(
            Alert.screenshot_id == screenshot.id
        ).all()
        
        result.append(DashboardItem(
            screenshot=screenshot,
            analysis=analysis,
            alerts=alerts
        ))
    
    return result


@router.post("/upload")
async def upload_screenshot(
    file: UploadFile = File(...),
    active_window: Optional[str] = Form("Browser Capture"),
    active_app: Optional[str] = Form("Browser"),
    width: Optional[int] = Form(1920),
    height: Optional[int] = Form(1080)
):
    """Upload a screenshot from the frontend and process it."""
    try:
        img_bytes = await file.read()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screen_{timestamp}.jpg"
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(img_bytes)
            
        result = process_uploaded_screenshot(
            img_bytes=img_bytes,
            filename=filename,
            filepath=filepath,
            width=width,
            height=height,
            active_window=active_window,
            active_app=active_app,
            all_windows=[]
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{screenshot_id}/image")
def get_screenshot_image(screenshot_id: int, db: Session = Depends(get_db)):
    """Serve the actual screenshot image file."""
    screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    if not os.path.exists(screenshot.filepath):
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    
    return FileResponse(screenshot.filepath, media_type="image/jpeg")