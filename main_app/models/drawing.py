from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base
from enums import DrawingStatus, DrawingMedium

class DrawingEntry(Base):
    __tablename__ = "drawing_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Index for user queries
    
    # Basic information
    title = Column(String, nullable=False, index=True)  # Index for title searches
    subject = Column(String, index=True)  # "Rainbow snake design", "Nature composition"
    medium = Column(DrawingMedium.as_sql_enum(), index=True)  # Index for medium filtering
    
    # Context and setting
    context = Column(Text)  # "Multi-day home project, working alongside almost-8-year-old peer"
    location = Column(String)  # "Home", "Kosta Glassworks, Sweden"
    
    # Time and dates - indexed for date range queries
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, index=True)
    duration_hours = Column(Float)  # Total time spent
    
    # Process and technique
    process_description = Column(Text)  # "1:1 template copying from laptop screen"
    template_used = Column(String)  # "whale book", "sunflower template"
    assistance_level = Column(String)  # "occasional assistance", "significant parental support"
    
    # Technical details
    technical_notes = Column(Text)  # AI analysis of drawing techniques, composition, development
    
    # Progress and completion
    status = Column(DrawingStatus.as_sql_enum(), default=DrawingStatus.PLANNED, index=True)  # Index for status filtering
    completion_notes = Column(Text)
    continuation_plans = Column(Text)  # "Expressed intention to continue work next day"
    
    # Links and references
    reference_link = Column(String)  # "View Completed Bead Work"
    image_url = Column(String)  # URL to uploaded image
    image_filename = Column(String)  # Filename of uploaded image
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Index for ordering
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="drawing_entries")