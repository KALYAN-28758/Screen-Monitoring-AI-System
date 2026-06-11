from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.db_models import Alert
from backend.schemas.schemas import AlertResponse, AlertMarkRead

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all alerts, optionally filtering to unread only."""
    try:
        query = db.query(Alert).order_by(Alert.triggered_at.desc())
        
        if unread_only:
            query = query.filter(Alert.is_read == False)
        
        alerts = query.offset(skip).limit(limit).all()
        return alerts
    except Exception as e:
        print(f"Error fetching alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")


@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    """Get count of unread alerts for badge display."""
    count = db.query(Alert).filter(Alert.is_read == False).count()
    return {"unread_count": count}


@router.post("/mark-read")
def mark_alerts_read(body: AlertMarkRead, db: Session = Depends(get_db)):
    """Mark specific alerts as read."""
    db.query(Alert).filter(Alert.id.in_(body.alert_ids)).update(
        {"is_read": True}, synchronize_session=False
    )
    db.commit()
    return {"message": f"Marked {len(body.alert_ids)} alerts as read"}


@router.post("/mark-all-read")
def mark_all_read(db: Session = Depends(get_db)):
    """Mark all alerts as read."""
    db.query(Alert).filter(Alert.is_read == False).update(
        {"is_read": True}, synchronize_session=False
    )
    db.commit()
    return {"message": "All alerts marked as read"}


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete a single alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted"}