from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import shutil
import uuid
from pathlib import Path
from database.config import get_db
from models import DrawingEntry, DrawingStatus, DrawingMedium, User

router = APIRouter()

class DrawingEntryCreate(BaseModel):
    user_id: int
    title: str
    subject: Optional[str] = None
    medium: Optional[DrawingMedium] = None
    context: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_hours: Optional[float] = None
    sessions_count: Optional[int] = None
    process_description: Optional[str] = None
    template_used: Optional[str] = None
    assistance_level: Optional[str] = None
    technical_notes: Optional[str] = None
    materials_count: Optional[int] = None
    complexity_level: Optional[str] = None
    status: DrawingStatus = DrawingStatus.PLANNED
    completion_notes: Optional[str] = None
    continuation_plans: Optional[str] = None
    reference_link: Optional[str] = None
    image_url: Optional[str] = None
    image_filename: Optional[str] = None

class DrawingEntryUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    medium: Optional[DrawingMedium] = None
    context: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_hours: Optional[float] = None
    sessions_count: Optional[int] = None
    process_description: Optional[str] = None
    template_used: Optional[str] = None
    assistance_level: Optional[str] = None
    technical_notes: Optional[str] = None
    materials_count: Optional[int] = None
    complexity_level: Optional[str] = None
    status: Optional[DrawingStatus] = None
    completion_notes: Optional[str] = None
    continuation_plans: Optional[str] = None
    reference_link: Optional[str] = None
    image_url: Optional[str] = None
    image_filename: Optional[str] = None

class DrawingEntryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    subject: Optional[str]
    medium: Optional[DrawingMedium]
    context: Optional[str]
    location: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    duration_hours: Optional[float]
    sessions_count: Optional[int]
    process_description: Optional[str]
    template_used: Optional[str]
    assistance_level: Optional[str]
    technical_notes: Optional[str]
    materials_count: Optional[int]
    complexity_level: Optional[str]
    status: DrawingStatus
    completion_notes: Optional[str]
    continuation_plans: Optional[str]
    reference_link: Optional[str]
    image_url: Optional[str]
    image_filename: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[DrawingEntryResponse])
async def get_drawing_entries(
    user_id: Optional[int] = Query(None),
    status: Optional[DrawingStatus] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(DrawingEntry)
    if user_id:
        query = query.filter(DrawingEntry.user_id == user_id)
    if status:
        query = query.filter(DrawingEntry.status == status)
    return query.order_by(DrawingEntry.created_at.desc()).all()

@router.get("/{entry_id}", response_model=DrawingEntryResponse)
async def get_drawing_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(DrawingEntry).filter(DrawingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Drawing entry not found")
    return entry

@router.post("/", response_model=DrawingEntryResponse)
async def create_drawing_entry(entry: DrawingEntryCreate, db: Session = Depends(get_db)):
    # Verify user exists
    user = db.query(User).filter(User.id == entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_entry = DrawingEntry(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.put("/{entry_id}", response_model=DrawingEntryResponse)
async def update_drawing_entry(
    entry_id: int, 
    entry_update: DrawingEntryUpdate, 
    db: Session = Depends(get_db)
):
    entry = db.query(DrawingEntry).filter(DrawingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Drawing entry not found")
    
    update_data = entry_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/{entry_id}")
async def delete_drawing_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(DrawingEntry).filter(DrawingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Drawing entry not found")
    
    # Delete associated image file if it exists
    if entry.image_filename:
        image_path = Path("web/static/uploads") / entry.image_filename
        if image_path.exists():
            image_path.unlink()
    
    db.delete(entry)
    db.commit()
    return {"message": "Drawing entry deleted"}

# Image upload endpoint
@router.post("/upload-image")
async def upload_drawing_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("web/static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Return the URL and filename
    image_url = f"/static/uploads/{unique_filename}"
    
    return {
        "image_url": image_url,
        "image_filename": unique_filename,
        "message": "Image uploaded successfully"
    }