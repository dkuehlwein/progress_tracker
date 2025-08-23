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
from utils.validation import parse_optional_int, parse_optional_float, parse_optional_date, clean_optional_string

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
    started_date: Optional[str] = Form(None),
    completed_date: Optional[str] = Form(None),
    paused_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    pause_reason: Optional[str] = Form(None),
    series_info: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    entry_data = {
        "user_id": user_id,
        "title": title,
        "author": clean_optional_string(author),
        "isbn": clean_optional_string(isbn),
        "reading_type": reading_type,
        "length_pages": parse_optional_int(length_pages),
        "length_duration": clean_optional_string(length_duration),
        "status": status,
        "progress_fraction": parse_optional_float(progress_fraction),
        "notes": clean_optional_string(notes),
        "pause_reason": clean_optional_string(pause_reason),
        "series_info": clean_optional_string(series_info)
    }
    
    # Parse and add dates from form input (date-only format)
    if started_date:
        try:
            # Parse YYYY-MM-DD format and set to start of day
            entry_data["started_date"] = datetime.fromisoformat(started_date + 'T00:00:00')
        except ValueError:
            pass
            
    if completed_date:
        try:
            # Parse YYYY-MM-DD format and set to end of day
            entry_data["completed_date"] = datetime.fromisoformat(completed_date + 'T23:59:59')
        except ValueError:
            pass
            
    if paused_date:
        try:
            # Parse YYYY-MM-DD format and set to noon
            entry_data["paused_date"] = datetime.fromisoformat(paused_date + 'T12:00:00')
        except ValueError:
            pass
    
    # Auto-set dates based on status if not manually provided
    current_time = datetime.now()
    if status == "in_progress" and "started_date" not in entry_data:
        entry_data["started_date"] = current_time
    elif status == "paused":
        if "started_date" not in entry_data:
            entry_data["started_date"] = current_time
        if "paused_date" not in entry_data:
            entry_data["paused_date"] = current_time
    elif status == "completed":
        if "started_date" not in entry_data:
            entry_data["started_date"] = current_time
        if "completed_date" not in entry_data:
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
        "drawing_mediums": [medium.value for medium in DrawingMedium]
    })

@router.get("/web/drawing/add", response_class=HTMLResponse)
async def add_drawing_form(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("add_drawing.html", {
        "request": request,
        "users": users,
        "drawing_statuses": [status.value for status in DrawingStatus],
        "drawing_mediums": [medium.value for medium in DrawingMedium]
    })

@router.post("/web/drawing/add")
async def add_drawing_web(
    user_id: int = Form(...),
    title: str = Form(...),
    subject: Optional[str] = Form(None),
    medium: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    duration_hours: Optional[str] = Form(None),
    status: str = Form("planned"),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    technical_notes: Optional[str] = Form(None),
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
        "subject": clean_optional_string(subject),
        "medium": medium if medium else None,
        "context": clean_optional_string(context),
        "duration_hours": parse_optional_float(duration_hours),
        "status": status,
        "technical_notes": clean_optional_string(technical_notes),
        "reference_link": clean_optional_string(reference_link),
        "image_url": image_url,
        "image_filename": image_filename
    }
    
    # Parse and add dates from form input (date-only format)
    if start_date:
        try:
            # Parse YYYY-MM-DD format and set to start of day
            entry_data["start_date"] = datetime.fromisoformat(start_date + 'T00:00:00')
        except ValueError:
            pass
            
    if end_date:
        try:
            # Parse YYYY-MM-DD format and set to end of day
            entry_data["end_date"] = datetime.fromisoformat(end_date + 'T23:59:59')
        except ValueError:
            pass
    
    # Set dates based on status if not manually provided
    current_date = datetime.now().date()
    if status == "in_progress" and "start_date" not in entry_data:
        entry_data["start_date"] = datetime.combine(current_date, datetime.min.time())
    elif status == "completed":
        if "start_date" not in entry_data:
            entry_data["start_date"] = datetime.combine(current_date, datetime.min.time())
        if "end_date" not in entry_data:
            entry_data["end_date"] = datetime.combine(current_date, datetime.max.time().replace(microsecond=0))
    
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
        "fitness_types": [type.value for type in FitnessType]
    })

@router.get("/web/fitness/add", response_class=HTMLResponse)
async def add_fitness_form(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("add_fitness.html", {
        "request": request,
        "users": users,
        "fitness_statuses": [status.value for status in FitnessStatus],
        "fitness_types": [type.value for type in FitnessType]
    })

@router.post("/web/fitness/add")
async def add_fitness_web(
    user_id: int = Form(...),
    title: str = Form(...),
    activity_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    duration_minutes: Optional[str] = Form(None),
    distance_km: Optional[str] = Form(None),
    intensity_level: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    status: str = Form("planned"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    entry_data = {
        "user_id": user_id,
        "title": title,
        "activity_type": clean_optional_string(activity_type),
        "description": clean_optional_string(description),
        "duration_minutes": parse_optional_float(duration_minutes),
        "distance_km": parse_optional_float(distance_km),
        "intensity_level": clean_optional_string(intensity_level),
        "location": clean_optional_string(location),
        "status": status,
        "notes": clean_optional_string(notes)
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
    reading_type: str = Form(ReadingType.PHYSICAL_BOOK.value),
    length_pages: Optional[str] = Form(None),
    length_duration: Optional[str] = Form(None),
    status: str = Form(ReadingStatus.PENDING.value),
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
    
    # Update fields
    entry.user_id = user_id
    entry.title = title
    entry.author = clean_optional_string(author)
    entry.isbn = clean_optional_string(isbn)
    entry.reading_type = reading_type
    entry.length_pages = parse_optional_int(length_pages)
    entry.length_duration = clean_optional_string(length_duration)
    entry.status = status
    entry.progress_fraction = parse_optional_float(progress_fraction)
    entry.notes = clean_optional_string(notes)
    entry.pause_reason = clean_optional_string(pause_reason)
    entry.series_info = clean_optional_string(series_info)
    
    # Parse and update dates from form input (date-only format)
    if started_date:
        try:
            # Parse YYYY-MM-DD format and set to start of day
            entry.started_date = datetime.fromisoformat(started_date + 'T00:00:00')
        except ValueError:
            pass
    else:
        entry.started_date = None
        
    if completed_date:
        try:
            # Parse YYYY-MM-DD format and set to end of day
            entry.completed_date = datetime.fromisoformat(completed_date + 'T23:59:59')
        except ValueError:
            pass
    else:
        entry.completed_date = None
        
    if paused_date:
        try:
            # Parse YYYY-MM-DD format and set to noon
            entry.paused_date = datetime.fromisoformat(paused_date + 'T12:00:00')
        except ValueError:
            pass
    else:
        entry.paused_date = None
    
    # Auto-set dates based on status if not manually provided
    current_time = datetime.now()
    if status == ReadingStatus.IN_PROGRESS.value and not entry.started_date:
        entry.started_date = current_time
    elif status == ReadingStatus.PAUSED.value:
        if not entry.started_date:
            entry.started_date = current_time
        if not entry.paused_date:
            entry.paused_date = current_time
    elif status == ReadingStatus.COMPLETED.value:
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
        "drawing_statuses": [status.value for status in DrawingStatus],
        "drawing_mediums": [medium.value for medium in DrawingMedium]
    })

@router.post("/web/drawing/edit/{entry_id}")
async def update_drawing_entry(
    entry_id: int,
    user_id: int = Form(...),
    title: str = Form(...),
    subject: Optional[str] = Form(None),
    medium: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    duration_hours: Optional[str] = Form(None),
    status: str = Form(DrawingStatus.PLANNED.value),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    technical_notes: Optional[str] = Form(None),
    reference_link: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    entry = db.query(DrawingEntry).filter(DrawingEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Drawing entry not found")
    
    # Handle image upload if provided
    if image and image.filename and image.content_type.startswith('image/'):
        # Delete old image if it exists
        if entry.image_filename:
            old_image_path = Path("web/static/uploads") / entry.image_filename
            if old_image_path.exists():
                old_image_path.unlink()
        
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
            
            entry.image_url = f"/static/uploads/{unique_filename}"
            entry.image_filename = unique_filename
        except Exception as e:
            print(f"Failed to save image: {e}")
    
    # Update fields
    entry.user_id = user_id
    entry.title = title
    entry.subject = clean_optional_string(subject)
    entry.medium = medium if medium else None
    entry.context = clean_optional_string(context)
    entry.duration_hours = parse_optional_float(duration_hours)
    entry.status = status
    entry.technical_notes = clean_optional_string(technical_notes)
    entry.reference_link = clean_optional_string(reference_link)
    
    # Parse and update dates from form input (date-only format)
    if start_date:
        try:
            # Parse YYYY-MM-DD format and set to start of day
            entry.start_date = datetime.fromisoformat(start_date + 'T00:00:00')
        except ValueError:
            pass
    else:
        entry.start_date = None
        
    if end_date:
        try:
            # Parse YYYY-MM-DD format and set to end of day
            entry.end_date = datetime.fromisoformat(end_date + 'T23:59:59')
        except ValueError:
            pass
    else:
        entry.end_date = None
    
    # Auto-set dates based on status if not manually provided
    current_time = datetime.now()
    if status == DrawingStatus.IN_PROGRESS.value and not entry.start_date:
        entry.start_date = current_time
    elif status == DrawingStatus.COMPLETED.value:
        if not entry.start_date:
            entry.start_date = current_time
        if not entry.end_date:
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
        "fitness_statuses": [status.value for status in FitnessStatus],
        "fitness_types": [type.value for type in FitnessType]
    })

@router.post("/web/fitness/edit/{entry_id}")
async def update_fitness_entry(
    entry_id: int,
    user_id: int = Form(...),
    title: str = Form(...),
    activity_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    duration_minutes: Optional[str] = Form(None),
    distance_km: Optional[str] = Form(None),
    intensity_level: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    status: str = Form(FitnessStatus.PLANNED.value),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    entry = db.query(FitnessEntry).filter(FitnessEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Fitness entry not found")
    
    # Update fields
    entry.user_id = user_id
    entry.title = title
    entry.activity_type = clean_optional_string(activity_type)
    entry.description = clean_optional_string(description)
    entry.duration_minutes = parse_optional_float(duration_minutes)
    entry.distance_km = parse_optional_float(distance_km)
    entry.intensity_level = clean_optional_string(intensity_level)
    entry.location = clean_optional_string(location)
    entry.status = status
    entry.notes = clean_optional_string(notes)
    
    # Update activity date
    current_time = datetime.now()
    if status in [FitnessStatus.IN_PROGRESS.value, FitnessStatus.COMPLETED.value]:
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