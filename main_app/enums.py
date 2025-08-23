"""
Centralized enum definitions for the progress tracker application.

This module provides all enum types used across the application with consistent
SQLAlchemy integration and proper value handling.
"""
import enum
from sqlalchemy import Enum as SQLEnum


class AppEnum(enum.Enum):
    """Base enum class with SQLAlchemy integration helpers."""
    
    @classmethod
    def as_sql_enum(cls):
        """Return SQLAlchemy Enum configured for this enum class."""
        return SQLEnum(cls, values_callable=lambda obj: [e.value for e in obj])
    
    @classmethod
    def choices(cls):
        """Return list of (value, name) tuples for form choices."""
        return [(e.value, e.name.replace('_', ' ').title()) for e in cls]
    
    @classmethod
    def values(cls):
        """Return list of enum values."""
        return [e.value for e in cls]


class ReadingStatus(AppEnum):
    """Status of a reading entry."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ReadingType(AppEnum):
    """Type of reading material."""
    PHYSICAL_BOOK = "physical_book"
    AUDIOBOOK = "audiobook"
    EBOOK = "ebook"
    MAGAZINE = "magazine"
    COMIC = "comic"


class DrawingStatus(AppEnum):
    """Status of a drawing entry."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    CONTINUED_NEXT_DAY = "continued_next_day"


class DrawingMedium(AppEnum):
    """Drawing medium/material type."""
    COLORED_PENCILS = "colored_pencils"
    PENCIL = "pencil"
    CRAYONS = "crayons"
    MARKERS = "markers"
    WATERCOLOR = "watercolor"
    DIGITAL = "digital"
    BEADS = "beads"
    MIXED_MEDIA = "mixed_media"


class FitnessStatus(AppEnum):
    """Status of a fitness entry."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class FitnessType(AppEnum):
    """Type of fitness activity."""
    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    SPORTS = "sports"
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    YOGA = "yoga"
    OTHER = "other"