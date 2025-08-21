"""Dashboard data service"""
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from models import (
    User, ReadingEntry, DrawingEntry, FitnessEntry,
    ReadingStatus, DrawingStatus, FitnessStatus
)
from config import SIMON_USER_NAME, STATS_HISTORY_MONTHS, RECENT_ENTRIES_LIMIT, DASHBOARD_ENTRIES_LIMIT


def get_monthly_stats_for_user(db: Session, user: User) -> Dict[str, Any]:
    """Calculate monthly statistics for a specific user"""
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if user.name == SIMON_USER_NAME:
        return _get_simon_monthly_stats(db, user.id, start_of_month)
    else:
        return _get_daniel_monthly_stats(db, user.id, start_of_month)


def get_historical_data_for_user(db: Session, user: User) -> Dict[str, List]:
    """Get historical chart data for a user"""
    now = datetime.now()
    history_start = now - timedelta(days=STATS_HISTORY_MONTHS * 30)
    
    if user.name == SIMON_USER_NAME:
        return _get_simon_historical_data(db, user.id, history_start)
    else:
        return _get_daniel_historical_data(db, user.id, history_start)


def get_recent_entries_for_user(db: Session, user: User) -> Dict[str, List]:
    """Get recent entries for dashboard display"""
    if user.name == SIMON_USER_NAME:
        return {
            "recent_reading": db.query(ReadingEntry)
                .filter(ReadingEntry.user_id == user.id)
                .order_by(ReadingEntry.created_at.desc())
                .limit(RECENT_ENTRIES_LIMIT)
                .all(),
            "recent_drawing": db.query(DrawingEntry)
                .filter(DrawingEntry.user_id == user.id)
                .order_by(DrawingEntry.created_at.desc())
                .limit(RECENT_ENTRIES_LIMIT)
                .all(),
            "recent_fitness": []
        }
    else:
        return {
            "recent_reading": db.query(ReadingEntry)
                .filter(ReadingEntry.user_id == user.id)
                .order_by(ReadingEntry.created_at.desc())
                .limit(DASHBOARD_ENTRIES_LIMIT)
                .all(),
            "recent_drawing": [],
            "recent_fitness": db.query(FitnessEntry)
                .filter(FitnessEntry.user_id == user.id)
                .order_by(FitnessEntry.created_at.desc())
                .limit(RECENT_ENTRIES_LIMIT)
                .all()
        }


def get_all_users_recent_entries(db: Session) -> Dict[str, List]:
    """Get recent entries across all users for default dashboard"""
    return {
        "recent_reading": db.query(ReadingEntry)
            .order_by(ReadingEntry.created_at.desc())
            .limit(DASHBOARD_ENTRIES_LIMIT)
            .all(),
        "recent_drawing": db.query(DrawingEntry)
            .order_by(DrawingEntry.created_at.desc())
            .limit(DASHBOARD_ENTRIES_LIMIT)
            .all(),
        "recent_fitness": db.query(FitnessEntry)
            .order_by(FitnessEntry.created_at.desc())
            .limit(DASHBOARD_ENTRIES_LIMIT)
            .all()
    }


def _get_simon_monthly_stats(db: Session, user_id: int, start_of_month: datetime) -> Dict[str, Any]:
    """Get Simon's monthly stats (reading and drawing focused)"""
    monthly_reading = db.query(ReadingEntry).filter(
        ReadingEntry.user_id == user_id,
        ReadingEntry.created_at >= start_of_month
    ).all()
    
    monthly_drawing = db.query(DrawingEntry).filter(
        DrawingEntry.user_id == user_id,
        DrawingEntry.created_at >= start_of_month
    ).all()
    
    return {
        "reading_count": len(monthly_reading),
        "reading_completed": len([r for r in monthly_reading if r.status.value == "completed"]),
        "drawing_count": len(monthly_drawing),
        "drawing_completed": len([d for d in monthly_drawing if d.status.value == "completed"]),
        "total_drawing_hours": sum([d.duration_hours or 0 for d in monthly_drawing])
    }


def _get_daniel_monthly_stats(db: Session, user_id: int, start_of_month: datetime) -> Dict[str, Any]:
    """Get Daniel's monthly stats (fitness focused)"""
    monthly_fitness = db.query(FitnessEntry).filter(
        FitnessEntry.user_id == user_id,
        FitnessEntry.created_at >= start_of_month
    ).all()
    
    return {
        "fitness_count": len(monthly_fitness),
        "fitness_completed": len([f for f in monthly_fitness if f.status.value == "completed"]),
        "total_minutes": sum([f.duration_minutes or 0 for f in monthly_fitness]),
        "total_distance": sum([f.distance_km or 0 for f in monthly_fitness])
    }


def _get_simon_historical_data(db: Session, user_id: int, history_start: datetime) -> Dict[str, List]:
    """Get Simon's historical chart data"""
    reading_history = db.query(
        extract('year', ReadingEntry.completed_date).label('year'),
        extract('month', ReadingEntry.completed_date).label('month'),
        func.count(ReadingEntry.id).label('count')
    ).filter(
        ReadingEntry.user_id == user_id,
        ReadingEntry.completed_date >= history_start,
        ReadingEntry.status == ReadingStatus.COMPLETED
    ).group_by('year', 'month').all()
    
    drawing_history = db.query(
        extract('year', DrawingEntry.end_date).label('year'),
        extract('month', DrawingEntry.end_date).label('month'),
        func.count(DrawingEntry.id).label('count')
    ).filter(
        DrawingEntry.user_id == user_id,
        DrawingEntry.end_date >= history_start,
        DrawingEntry.status == DrawingStatus.COMPLETED
    ).group_by('year', 'month').all()
    
    return {
        "reading_history": reading_history,
        "drawing_history": drawing_history,
        "fitness_history": []
    }


def _get_daniel_historical_data(db: Session, user_id: int, history_start: datetime) -> Dict[str, List]:
    """Get Daniel's historical chart data"""
    fitness_history = db.query(
        extract('year', FitnessEntry.activity_date).label('year'),
        extract('month', FitnessEntry.activity_date).label('month'),
        func.count(FitnessEntry.id).label('count')
    ).filter(
        FitnessEntry.user_id == user_id,
        FitnessEntry.activity_date >= history_start,
        FitnessEntry.status == FitnessStatus.COMPLETED
    ).group_by('year', 'month').all()
    
    return {
        "reading_history": [],
        "drawing_history": [],
        "fitness_history": fitness_history
    }