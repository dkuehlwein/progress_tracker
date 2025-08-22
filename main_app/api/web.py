from fastapi import APIRouter, Request, Depends, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import shutil
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional, List
from database.config import get_db
from models import User, ReadingEntry, DrawingEntry, FitnessEntry, ReadingStatus, DrawingStatus, FitnessStatus, ReadingType, DrawingMedium, FitnessType
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/web", response_class=HTMLResponse)
async def web_home(request: Request, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Main dashboard page - shows user-specific or all users' data"""
    from services.dashboard_service import (
        get_monthly_stats_for_user, get_historical_data_for_user,
        get_recent_entries_for_user, get_all_users_recent_entries
    )
    
    users = db.query(User).all()
    
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # User not found, fall back to all users view
            return await _render_all_users_dashboard(request, users, db)
        
        # Get user-specific dashboard data
        monthly_stats = get_monthly_stats_for_user(db, user)
        historical_data = get_historical_data_for_user(db, user)
        recent_entries = get_recent_entries_for_user(db, user)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "users": users,
            "selected_user_id": user_id,
            "selected_user": user,
            "monthly_stats": monthly_stats,
            **historical_data,  # reading_history, drawing_history, fitness_history
            **recent_entries   # recent_reading, recent_drawing, recent_fitness
        })
    
    # Default: show all users' data
    return await _render_all_users_dashboard(request, users, db)


async def _render_all_users_dashboard(request: Request, users: List[User], db: Session):
    """Render dashboard showing data from all users"""
    from services.dashboard_service import get_all_users_recent_entries
    
    recent_entries = get_all_users_recent_entries(db)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "users": users,
        "selected_user_id": None,
        "selected_user": None,
        **recent_entries
    })

@router.get("/web/user/{user_id}", response_class=HTMLResponse)
async def user_dashboard(request: Request, user_id: int, db: Session = Depends(get_db)):
    """User-specific dashboard page"""
    from services.dashboard_service import (
        get_monthly_stats_for_user, get_recent_entries_for_user
    )
    from utils.exceptions import NotFoundError
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User", str(user_id))
    
    # Get user-specific dashboard data using the same service
    monthly_stats = get_monthly_stats_for_user(db, user)
    recent_entries = get_recent_entries_for_user(db, user)
    
    return templates.TemplateResponse("user_dashboard.html", {
        "request": request,
        "user": user,
        "monthly_stats": monthly_stats,
        **recent_entries
    })

@router.get("/web/reading", response_class=HTMLResponse)
async def web_reading(request: Request, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    users = db.query(User).all()
    query = db.query(ReadingEntry)
    if user_id:
        query = query.filter(ReadingEntry.user_id == user_id)
    entries = query.order_by(ReadingEntry.created_at.desc()).all()
    
    return templates.TemplateResponse("reading.html", {
        "request": request,
        "users": users,
        "entries": entries,
        "selected_user_id": user_id,
        "reading_statuses": [status.value for status in ReadingStatus],
        "reading_types": ["physical_book", "audiobook", "ebook", "magazine", "comic"]
    })

@router.get("/web/reading/add", response_class=HTMLResponse)
async def add_reading_form(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("add_reading.html", {
        "request": request,
        "users": users
    })

@router.post("/web/reading/add")
async def add_reading_web(
    user_id: int = Form(...),
    title: str = Form(...),
    author: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    reading_type: str = Form("physical_book"),
    length_pages: Optional[str] = Form(None),
    length_duration: Optional[str] = Form(None),
    status: str = Form("pending"),
    progress_fraction: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    pause_reason: Optional[str] = Form(None),
    series_info: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Parse numeric fields properly, handling empty strings
    parsed_length_pages = None
    if length_pages and length_pages.strip():
        try:
            parsed_length_pages = int(length_pages)
        except ValueError:
            parsed_length_pages = None
    
    parsed_progress_fraction = None
    if progress_fraction and progress_fraction.strip():
        try:
            parsed_progress_fraction = float(progress_fraction)
        except ValueError:
            parsed_progress_fraction = None

    entry_data = {
        "user_id": user_id,
        "title": title,
        "author": author if author else None,
        "isbn": isbn if isbn else None,
        "reading_type": reading_type,
        "length_pages": parsed_length_pages,
        "length_duration": length_duration if length_duration else None,
        "status": status,
        "progress_fraction": parsed_progress_fraction,
        "notes": notes if notes else None,
        "pause_reason": pause_reason if pause_reason else None,
        "series_info": series_info if series_info else None
    }
    
    # Set dates based on status
    current_time = datetime.now()
    if status == "in_progress":
        entry_data["started_date"] = current_time
    elif status == "paused":
        entry_data["started_date"] = current_time
        entry_data["paused_date"] = current_time
    elif status == "completed":
        entry_data["started_date"] = current_time
        entry_data["completed_date"] = current_time
    
    # Remove None values
    entry_data = {k: v for k, v in entry_data.items() if v is not None}
    
    db_entry = ReadingEntry(**entry_data)
    db.add(db_entry)
    db.commit()
    
    return RedirectResponse(url="/web/reading", status_code=303)

@router.get("/web/drawing", response_class=HTMLResponse)
async def web_drawing(request: Request, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    users = db.query(User).all()
    query = db.query(DrawingEntry)
    if user_id:
        query = query.filter(DrawingEntry.user_id == user_id)
    entries = query.order_by(DrawingEntry.created_at.desc()).all()
    
    return templates.TemplateResponse("drawing.html", {
        "request": request,
        "users": users,
        "entries": entries,
        "selected_user_id": user_id,
        "drawing_statuses": [status.value for status in DrawingStatus],
        "drawing_mediums": ["colored_pencils", "crayons", "markers", "watercolor", "digital", "beads", "mixed_media"]
    })

@router.get("/web/drawing/add", response_class=HTMLResponse)
async def add_drawing_form(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("add_drawing.html", {
        "request": request,
        "users": users,
        "drawing_statuses": [status.value for status in DrawingStatus],
        "drawing_mediums": ["colored_pencils", "crayons", "markers", "watercolor", "digital", "beads", "mixed_media"]
    })

@router.post("/web/drawing/add")
async def add_drawing_web(
    user_id: int = Form(...),
    title: str = Form(...),
    subject: Optional[str] = Form(None),
    medium: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    duration_hours: Optional[float] = Form(None),
    sessions_count: Optional[int] = Form(None),
    materials_count: Optional[int] = Form(None),
    status: str = Form("planned"),
    technical_notes: Optional[str] = Form(None),
    complexity_level: Optional[str] = Form(None),
    reference_link: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Handle image upload
    image_url = None
    image_filename = None
    
    if image and image.filename and image.content_type.startswith('image/'):
        # Create uploads directory if it doesn't exist
        upload_dir = Path("web/static/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            image_url = f"/static/uploads/{unique_filename}"
            image_filename = unique_filename
        except Exception as e:
            print(f"Failed to save image: {e}")
    
    entry_data = {
        "user_id": user_id,
        "title": title,
        "subject": subject if subject else None,
        "medium": medium if medium else None,
        "context": context if context else None,
        "duration_hours": duration_hours,
        "sessions_count": sessions_count,
        "materials_count": materials_count,
        "status": status,
        "technical_notes": technical_notes if technical_notes else None,
        "complexity_level": complexity_level if complexity_level else None,
        "reference_link": reference_link if reference_link else None,
        "image_url": image_url,
        "image_filename": image_filename
    }
    
    # Set dates based on status
    current_time = datetime.now()
    if status == "in_progress":
        entry_data["start_date"] = current_time
    elif status == "completed":
        entry_data["start_date"] = current_time
        entry_data["end_date"] = current_time
    
    # Remove None values
    entry_data = {k: v for k, v in entry_data.items() if v is not None}
    
    db_entry = DrawingEntry(**entry_data)
    db.add(db_entry)
    db.commit()
    
    return RedirectResponse(url="/web/drawing", status_code=303)

@router.get("/web/fitness", response_class=HTMLResponse)
async def web_fitness(request: Request, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    users = db.query(User).all()
    query = db.query(FitnessEntry)
    if user_id:
        query = query.filter(FitnessEntry.user_id == user_id)
    entries = query.order_by(FitnessEntry.created_at.desc()).all()
    
    return templates.TemplateResponse("fitness.html", {
        "request": request,
        "users": users,
        "entries": entries,
        "selected_user_id": user_id,
        "fitness_statuses": [status.value for status in FitnessStatus],
        "fitness_types": ["cardio", "strength", "flexibility", "sports", "walking", "running", "cycling", "swimming", "yoga", "other"]
    })

@router.get("/web/fitness/add", response_class=HTMLResponse)
async def add_fitness_form(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("add_fitness.html", {
        "request": request,
        "users": users,
        "fitness_statuses": [status.value for status in FitnessStatus],
        "fitness_types": ["cardio", "strength", "flexibility", "sports", "walking", "running", "cycling", "swimming", "yoga", "other"]
    })

@router.post("/web/fitness/add")
async def add_fitness_web(
    user_id: int = Form(...),
    title: str = Form(...),
    activity_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    duration_minutes: Optional[float] = Form(None),
    distance_km: Optional[float] = Form(None),
    intensity_level: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    status: str = Form("planned"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    entry_data = {
        "user_id": user_id,
        "title": title,
        "activity_type": activity_type if activity_type else None,
        "description": description if description else None,
        "duration_minutes": duration_minutes,
        "distance_km": distance_km,
        "intensity_level": intensity_level if intensity_level else None,
        "location": location if location else None,
        "status": status,
        "notes": notes if notes else None
    }
    
    # Set activity date based on status
    current_time = datetime.now()
    if status in ["in_progress", "completed"]:
        entry_data["activity_date"] = current_time
    
    # Remove None values
    entry_data = {k: v for k, v in entry_data.items() if v is not None}
    
    db_entry = FitnessEntry(**entry_data)
    db.add(db_entry)
    db.commit()
    
    return RedirectResponse(url="/web/fitness", status_code=303)

# Edit routes
@router.get("/web/reading/edit/{entry_id}", response_class=HTMLResponse)
async def edit_reading_form(request: Request, entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(ReadingEntry).filter(ReadingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Reading entry not found")
    
    users = db.query(User).all()
    return templates.TemplateResponse("edit_reading.html", {
        "request": request,
        "entry": entry,
        "users": users,
        "reading_statuses": [status.name for status in ReadingStatus],
        "reading_types": [type.name for type in ReadingType]
    })

@router.post("/web/reading/edit/{entry_id}")
async def update_reading_entry(
    entry_id: int,
    user_id: int = Form(...),
    title: str = Form(...),
    author: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    reading_type: str = Form("PHYSICAL_BOOK"),
    length_pages: Optional[str] = Form(None),
    length_duration: Optional[str] = Form(None),
    status: str = Form("PENDING"),
    progress_fraction: Optional[str] = Form(None),
    started_date: Optional[str] = Form(None),
    completed_date: Optional[str] = Form(None),
    paused_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    pause_reason: Optional[str] = Form(None),
    series_info: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    entry = db.query(ReadingEntry).filter(ReadingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Reading entry not found")
    
    # Parse numeric fields properly, handling empty strings
    parsed_length_pages = None
    if length_pages and length_pages.strip():
        try:
            parsed_length_pages = int(length_pages)
        except ValueError:
            parsed_length_pages = None
    
    parsed_progress_fraction = None
    if progress_fraction and progress_fraction.strip():
        try:
            parsed_progress_fraction = float(progress_fraction)
        except ValueError:
            parsed_progress_fraction = None

    # Update fields
    entry.user_id = user_id
    entry.title = title
    entry.author = author if author else None
    entry.isbn = isbn if isbn else None
    entry.reading_type = reading_type
    entry.length_pages = parsed_length_pages
    entry.length_duration = length_duration if length_duration else None
    entry.status = status
    entry.progress_fraction = parsed_progress_fraction
    entry.notes = notes if notes else None
    entry.pause_reason = pause_reason if pause_reason else None
    entry.series_info = series_info if series_info else None
    
    # Parse and update dates from form input
    if started_date:
        try:
            entry.started_date = datetime.fromisoformat(started_date.replace('T', ' '))
        except ValueError:
            pass
    else:
        entry.started_date = None
        
    if completed_date:
        try:
            entry.completed_date = datetime.fromisoformat(completed_date.replace('T', ' '))
        except ValueError:
            pass
    else:
        entry.completed_date = None
        
    if paused_date:
        try:
            entry.paused_date = datetime.fromisoformat(paused_date.replace('T', ' '))
        except ValueError:
            pass
    else:
        entry.paused_date = None
    
    # Auto-set dates based on status if not manually provided
    current_time = datetime.now()
    if status == "IN_PROGRESS" and not entry.started_date:
        entry.started_date = current_time
    elif status == "PAUSED":
        if not entry.started_date:
            entry.started_date = current_time
        if not entry.paused_date:
            entry.paused_date = current_time
    elif status == "COMPLETED":
        if not entry.started_date:
            entry.started_date = current_time
        if not entry.completed_date:
            entry.completed_date = current_time
    
    db.commit()
    return RedirectResponse(url="/web/reading", status_code=303)

@router.get("/web/drawing/edit/{entry_id}", response_class=HTMLResponse)
async def edit_drawing_form(request: Request, entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(DrawingEntry).filter(DrawingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Drawing entry not found")
    
    users = db.query(User).all()
    return templates.TemplateResponse("edit_drawing.html", {
        "request": request,
        "entry": entry,
        "users": users,
        "drawing_statuses": [status.name for status in DrawingStatus],
        "drawing_mediums": [medium.name for medium in DrawingMedium]
    })

@router.post("/web/drawing/edit/{entry_id}")
async def update_drawing_entry(
    entry_id: int,
    user_id: int = Form(...),
    title: str = Form(...),
    subject: Optional[str] = Form(None),
    medium: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    duration_hours: Optional[float] = Form(None),
    sessions_count: Optional[int] = Form(None),
    materials_count: Optional[int] = Form(None),
    status: str = Form("PLANNED"),
    technical_notes: Optional[str] = Form(None),
    complexity_level: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    entry = db.query(DrawingEntry).filter(DrawingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Drawing entry not found")
    
    # Update fields
    entry.user_id = user_id
    entry.title = title
    entry.subject = subject if subject else None
    entry.medium = medium if medium else None
    entry.context = context if context else None
    entry.duration_hours = duration_hours
    entry.sessions_count = sessions_count
    entry.materials_count = materials_count
    entry.status = status
    entry.technical_notes = technical_notes if technical_notes else None
    entry.complexity_level = complexity_level if complexity_level else None
    
    # Update dates
    current_time = datetime.now()
    if status == "IN_PROGRESS" and not entry.start_date:
        entry.start_date = current_time
    elif status == "COMPLETED":
        if not entry.start_date:
            entry.start_date = current_time
        entry.end_date = current_time
    
    db.commit()
    return RedirectResponse(url="/web/drawing", status_code=303)

@router.get("/web/fitness/edit/{entry_id}", response_class=HTMLResponse)
async def edit_fitness_form(request: Request, entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(FitnessEntry).filter(FitnessEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Fitness entry not found")
    
    users = db.query(User).all()
    return templates.TemplateResponse("edit_fitness.html", {
        "request": request,
        "entry": entry,
        "users": users,
        "fitness_statuses": [status.name for status in FitnessStatus],
        "fitness_types": [type.name for type in FitnessType]
    })

@router.post("/web/fitness/edit/{entry_id}")
async def update_fitness_entry(
    entry_id: int,
    user_id: int = Form(...),
    title: str = Form(...),
    activity_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    duration_minutes: Optional[float] = Form(None),
    distance_km: Optional[float] = Form(None),
    intensity_level: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    status: str = Form("PLANNED"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    entry = db.query(FitnessEntry).filter(FitnessEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Fitness entry not found")
    
    # Update fields
    entry.user_id = user_id
    entry.title = title
    entry.activity_type = activity_type if activity_type else None
    entry.description = description if description else None
    entry.duration_minutes = duration_minutes
    entry.distance_km = distance_km
    entry.intensity_level = intensity_level if intensity_level else None
    entry.location = location if location else None
    entry.status = status
    entry.notes = notes if notes else None
    
    # Update activity date
    current_time = datetime.now()
    if status in ["IN_PROGRESS", "COMPLETED"]:
        entry.activity_date = current_time
    
    db.commit()
    return RedirectResponse(url="/web/fitness", status_code=303)

# Delete routes
@router.post("/web/reading/delete/{entry_id}")
async def delete_reading_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(ReadingEntry).filter(ReadingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Reading entry not found")
    
    db.delete(entry)
    db.commit()
    return RedirectResponse(url="/web/reading", status_code=303)

@router.post("/web/drawing/delete/{entry_id}")
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
    return RedirectResponse(url="/web/drawing", status_code=303)

@router.post("/web/fitness/delete/{entry_id}")
async def delete_fitness_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(FitnessEntry).filter(FitnessEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Fitness entry not found")
    
    db.delete(entry)
    db.commit()
    return RedirectResponse(url="/web/fitness", status_code=303)