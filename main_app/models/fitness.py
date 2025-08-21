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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic information
    title = Column(String, nullable=False)
    activity_type = Column(Enum(FitnessType))
    description = Column(Text)
    
    # Time and duration
    activity_date = Column(DateTime)
    duration_minutes = Column(Float)
    planned_duration = Column(Float)
    
    # Metrics
    distance_km = Column(Float)
    calories_burned = Column(Integer)
    heart_rate_avg = Column(Integer)
    heart_rate_max = Column(Integer)
    
    # Intensity and effort
    intensity_level = Column(String)  # "low", "moderate", "high", "very high"
    perceived_effort = Column(Integer)  # 1-10 scale
    
    # Location and context
    location = Column(String)  # "Home", "Gym", "Park"
    weather = Column(String)  # For outdoor activities
    equipment_used = Column(String)
    
    # Progress and notes
    status = Column(Enum(FitnessStatus), default=FitnessStatus.PLANNED)
    notes = Column(Text)
    achievements = Column(Text)  # Personal records, milestones
    next_goals = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="fitness_entries")