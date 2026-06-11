from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.db_models import UserRule
from backend.schemas.schemas import  UserRuleCreate, UserRuleUpdate, UserRuleResponse

router = APIRouter(prefix="/api/rules", tags=["Rules"])


@router.get("/", response_model=List[UserRuleResponse])
def get_all_rules(db: Session = Depends(get_db)):
    """Get all user-defined monitoring rules."""
    return db.query(UserRule).order_by(UserRule.created_at.desc()).all()


@router.post("/", response_model=UserRuleResponse)
def create_rule(rule: UserRuleCreate, db: Session = Depends(get_db)):
    """Create a new monitoring rule."""
    db_rule = UserRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.put("/{rule_id}", response_model=UserRuleResponse)
def update_rule(rule_id: int, rule: UserRuleUpdate, db: Session = Depends(get_db)):
    """Update an existing rule."""
    db_rule = db.query(UserRule).filter(UserRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    for field, value in rule.model_dump(exclude_unset=True).items():
        setattr(db_rule, field, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a rule."""
    db_rule = db.query(UserRule).filter(UserRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(db_rule)
    db.commit()
    return {"message": "Rule deleted successfully"}