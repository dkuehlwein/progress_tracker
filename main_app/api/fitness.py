from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database.config import get_db
from models import FitnessEntry, FitnessStatus, FitnessType, User

router = APIRouter()

class FitnessEntryCreate(BaseModel):
    user_id: int
    title: str
    activity_type: Optional[FitnessType] = None
    description: Optional[str] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    planned_duration: Optional[float] = None
    distance_km: Optional[float] = None
    calories_burned: Optional[int] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    intensity_level: Optional[str] = None
    perceived_effort: Optional[int] = None
    location: Optional[str] = None
    weather: Optional[str] = None
    equipment_used: Optional[str] = None
    status: FitnessStatus = FitnessStatus.PLANNED
    notes: Optional[str] = None
    achievements: Optional[str] = None
    next_goals: Optional[str] = None

class FitnessEntryUpdate(BaseModel):
    title: Optional[str] = None
    activity_type: Optional[FitnessType] = None
    description: Optional[str] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    planned_duration: Optional[float] = None
    distance_km: Optional[float] = None
    calories_burned: Optional[int] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    intensity_level: Optional[str] = None
    perceived_effort: Optional[int] = None
    location: Optional[str] = None
    weather: Optional[str] = None
    equipment_used: Optional[str] = None
    status: Optional[FitnessStatus] = None
    notes: Optional[str] = None
    achievements: Optional[str] = None
    next_goals: Optional[str] = None

class FitnessEntryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    activity_type: Optional[FitnessType]
    description: Optional[str]
    activity_date: Optional[datetime]
    duration_minutes: Optional[float]
    planned_duration: Optional[float]
    distance_km: Optional[float]
    calories_burned: Optional[int]
    heart_rate_avg: Optional[int]
    heart_rate_max: Optional[int]
    intensity_level: Optional[str]
    perceived_effort: Optional[int]
    location: Optional[str]
    weather: Optional[str]
    equipment_used: Optional[str]
    status: FitnessStatus
    notes: Optional[str]
    achievements: Optional[str]
    next_goals: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[FitnessEntryResponse])
async def get_fitness_entries(
    user_id: Optional[int] = Query(None),
    status: Optional[FitnessStatus] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(FitnessEntry)
    if user_id:
        query = query.filter(FitnessEntry.user_id == user_id)
    if status:
        query = query.filter(FitnessEntry.status == status)
    return query.order_by(FitnessEntry.created_at.desc()).all()

@router.get("/{entry_id}", response_model=FitnessEntryResponse)
async def get_fitness_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(FitnessEntry).filter(FitnessEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Fitness entry not found")
    return entry

@router.post("/", response_model=FitnessEntryResponse)
async def create_fitness_entry(entry: FitnessEntryCreate, db: Session = Depends(get_db)):
    # Verify user exists
    user = db.query(User).filter(User.id == entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_entry = FitnessEntry(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.put("/{entry_id}", response_model=FitnessEntryResponse)
async def update_fitness_entry(
    entry_id: int, 
    entry_update: FitnessEntryUpdate, 
    db: Session = Depends(get_db)
):
    entry = db.query(FitnessEntry).filter(FitnessEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Fitness entry not found")
    
    update_data = entry_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/{entry_id}")
async def delete_fitness_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(FitnessEntry).filter(FitnessEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Fitness entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": "Fitness entry deleted"}