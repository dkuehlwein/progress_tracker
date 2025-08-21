from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base
import enum

class FitnessStatus(enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class FitnessType(enum.Enum):
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

class FitnessEntry(Base):
    __tablename__ = "fitness_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Index for user queries
    
    # Basic information
    title = Column(String, nullable=False, index=True)  # Index for title searches
    activity_type = Column(Enum(FitnessType), index=True)  # Index for activity type filtering
    description = Column(Text)
    
    # Time and duration
    activity_date = Column(DateTime, index=True)  # Index for date range queries
    duration_minutes = Column(Float)
    planned_duration = Column(Float)
    
    # Metrics
    distance_km = Column(Float)
    calories_burned = Column(Integer)
    heart_rate_avg = Column(Integer)
    heart_rate_max = Column(Integer)
    
    # Intensity and effort
    intensity_level = Column(String, index=True)  # "low", "moderate", "high", "very high" - indexed for filtering
    perceived_effort = Column(Integer)  # 1-10 scale
    
    # Location and context
    location = Column(String, index=True)  # "Home", "Gym", "Park" - indexed for location filtering
    weather = Column(String)  # For outdoor activities
    equipment_used = Column(String)
    
    # Progress and notes
    status = Column(Enum(FitnessStatus), default=FitnessStatus.PLANNED, index=True)  # Index for status filtering
    notes = Column(Text)
    achievements = Column(Text)  # Personal records, milestones
    next_goals = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Index for ordering
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="fitness_entries")