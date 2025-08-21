from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base
import enum

class ReadingStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class ReadingType(enum.Enum):
    PHYSICAL_BOOK = "physical_book"
    AUDIOBOOK = "audiobook"
    EBOOK = "ebook"
    MAGAZINE = "magazine"
    COMIC = "comic"

class ReadingEntry(Base):
    __tablename__ = "reading_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic information
    title = Column(String, nullable=False)
    author = Column(String)
    isbn = Column(String)
    
    # Type and length
    reading_type = Column(Enum(ReadingType), default=ReadingType.PHYSICAL_BOOK)
    length_pages = Column(Integer)
    length_duration = Column(String)  # For audiobooks: "2h 34m"
    
    # Progress tracking
    status = Column(Enum(ReadingStatus), default=ReadingStatus.PENDING)
    progress_fraction = Column(Float)  # 0.0 to 1.0 (e.g., 2/3 = 0.67)
    
    # Dates
    started_date = Column(DateTime)
    paused_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # Notes and context
    notes = Column(Text)
    pause_reason = Column(String)  # "too scary for Simon"
    series_info = Column(String)   # "Band 8 der beliebten Kinderbuch-Reihe"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reading_entries")