from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base
import enum

class DrawingStatus(enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    CONTINUED_NEXT_DAY = "continued_next_day"

class DrawingMedium(enum.Enum):
    COLORED_PENCILS = "colored_pencils"
    CRAYONS = "crayons"
    MARKERS = "markers"
    WATERCOLOR = "watercolor"
    DIGITAL = "digital"
    BEADS = "beads"
    MIXED_MEDIA = "mixed_media"

class DrawingEntry(Base):
    __tablename__ = "drawing_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic information
    title = Column(String, nullable=False)
    subject = Column(String)  # "Rainbow snake design", "Nature composition"
    medium = Column(Enum(DrawingMedium))
    
    # Context and setting
    context = Column(Text)  # "Multi-day home project, working alongside almost-8-year-old peer"
    location = Column(String)  # "Home", "Kosta Glassworks, Sweden"
    
    # Time and dates
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    duration_hours = Column(Float)  # Total time spent
    sessions_count = Column(Integer)  # Number of work sessions
    
    # Process and technique
    process_description = Column(Text)  # "1:1 template copying from laptop screen"
    template_used = Column(String)  # "whale book", "sunflower template"
    assistance_level = Column(String)  # "occasional assistance", "significant parental support"
    
    # Technical details
    technical_notes = Column(Text)  # Complex pattern matching, color gradient management, etc.
    materials_count = Column(Integer)  # Number of beads, etc.
    complexity_level = Column(String)  # "advanced", "beginner", "intermediate"
    
    # Progress and completion
    status = Column(Enum(DrawingStatus), default=DrawingStatus.PLANNED)
    completion_notes = Column(Text)
    continuation_plans = Column(Text)  # "Expressed intention to continue work next day"
    
    # Links and references
    reference_link = Column(String)  # "View Completed Bead Work"
    image_url = Column(String)  # URL to uploaded image
    image_filename = Column(String)  # Filename of uploaded image
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="drawing_entries")