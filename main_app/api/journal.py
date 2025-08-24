from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
from database.config import get_db
from models import JournalEntry, User

router = APIRouter()

class JournalEntryCreate(BaseModel):
    user_id: int
    date: date
    title: Optional[str] = None
    location: Optional[str] = None
    context: str
    parental_input: Optional[str] = None
    ai_analysis: Optional[str] = None
    tags: Optional[str] = None

class JournalEntryUpdate(BaseModel):
    date: Optional[date] = None
    title: Optional[str] = None
    location: Optional[str] = None
    context: Optional[str] = None
    parental_input: Optional[str] = None
    ai_analysis: Optional[str] = None
    tags: Optional[str] = None

class JournalEntryResponse(BaseModel):
    id: int
    user_id: int
    date: date
    title: Optional[str]
    location: Optional[str]
    context: str
    parental_input: Optional[str]
    ai_analysis: Optional[str]
    tags: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[JournalEntryResponse])
async def get_journal_entries(
    user_id: Optional[int] = Query(None),
    tags: Optional[str] = Query(None, description="Filter by tag (conflict, achievement, etc.)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(JournalEntry)
    if user_id:
        query = query.filter(JournalEntry.user_id == user_id)
    if tags:
        # Simple contains filter for tag searching
        query = query.filter(JournalEntry.tags.contains(tags))
    if start_date:
        query = query.filter(JournalEntry.date >= start_date)
    if end_date:
        query = query.filter(JournalEntry.date <= end_date)
    return query.order_by(JournalEntry.date.desc()).all()

@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry

@router.post("/", response_model=JournalEntryResponse)
async def create_journal_entry(entry: JournalEntryCreate, db: Session = Depends(get_db)):
    # Verify user exists
    user = db.query(User).filter(User.id == entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_entry = JournalEntry(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.put("/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(entry_id: int, entry: JournalEntryUpdate, db: Session = Depends(get_db)):
    db_entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    # Update only provided fields
    update_data = entry.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_entry, field, value)
    
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.delete("/{entry_id}")
async def delete_journal_entry(entry_id: int, db: Session = Depends(get_db)):
    db_entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    db.delete(db_entry)
    db.commit()
    return {"message": "Journal entry deleted successfully"}