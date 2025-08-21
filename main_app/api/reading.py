from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database.config import get_db
from models import ReadingEntry, ReadingStatus, ReadingType, User

router = APIRouter()

class ReadingEntryCreate(BaseModel):
    user_id: int
    title: str
    author: Optional[str] = None
    isbn: Optional[str] = None
    reading_type: ReadingType = ReadingType.PHYSICAL_BOOK
    length_pages: Optional[int] = None
    length_duration: Optional[str] = None
    status: ReadingStatus = ReadingStatus.PENDING
    progress_fraction: Optional[float] = None
    started_date: Optional[datetime] = None
    paused_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None
    pause_reason: Optional[str] = None
    series_info: Optional[str] = None

class ReadingEntryUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    reading_type: Optional[ReadingType] = None
    length_pages: Optional[int] = None
    length_duration: Optional[str] = None
    status: Optional[ReadingStatus] = None
    progress_fraction: Optional[float] = None
    started_date: Optional[datetime] = None
    paused_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None
    pause_reason: Optional[str] = None
    series_info: Optional[str] = None

class ReadingEntryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    author: Optional[str]
    isbn: Optional[str]
    reading_type: ReadingType
    length_pages: Optional[int]
    length_duration: Optional[str]
    status: ReadingStatus
    progress_fraction: Optional[float]
    started_date: Optional[datetime]
    paused_date: Optional[datetime]
    completed_date: Optional[datetime]
    notes: Optional[str]
    pause_reason: Optional[str]
    series_info: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[ReadingEntryResponse])
async def get_reading_entries(
    user_id: Optional[int] = Query(None),
    status: Optional[ReadingStatus] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ReadingEntry)
    if user_id:
        query = query.filter(ReadingEntry.user_id == user_id)
    if status:
        query = query.filter(ReadingEntry.status == status)
    return query.order_by(ReadingEntry.created_at.desc()).all()

@router.get("/{entry_id}", response_model=ReadingEntryResponse)
async def get_reading_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(ReadingEntry).filter(ReadingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Reading entry not found")
    return entry

@router.post("/", response_model=ReadingEntryResponse)
async def create_reading_entry(entry: ReadingEntryCreate, db: Session = Depends(get_db)):
    # Verify user exists
    user = db.query(User).filter(User.id == entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_entry = ReadingEntry(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.put("/{entry_id}", response_model=ReadingEntryResponse)
async def update_reading_entry(
    entry_id: int, 
    entry_update: ReadingEntryUpdate, 
    db: Session = Depends(get_db)
):
    entry = db.query(ReadingEntry).filter(ReadingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Reading entry not found")
    
    update_data = entry_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/{entry_id}")
async def delete_reading_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(ReadingEntry).filter(ReadingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Reading entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": "Reading entry deleted"}