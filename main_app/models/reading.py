from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base
from enums import ReadingStatus, ReadingType

class ReadingEntry(Base):
    __tablename__ = "reading_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Index for user queries
    
    # Basic information
    title = Column(String, nullable=False, index=True)  # Index for title searches
    author = Column(String, index=True)  # Index for author searches
    isbn = Column(String, index=True)  # Index for ISBN lookups
    
    # Type and length
    reading_type = Column(ReadingType.as_sql_enum(), default=ReadingType.PHYSICAL_BOOK, index=True)
    length_pages = Column(Integer)
    length_duration = Column(Integer)  # For audiobooks: duration in minutes
    
    # Progress tracking
    status = Column(ReadingStatus.as_sql_enum(), default=ReadingStatus.PENDING, index=True)  # Index for status filtering
    progress_fraction = Column(Float)  # 0.0 to 1.0 (e.g., 2/3 = 0.67)
    
    # Dates - indexed for date range queries
    started_date = Column(DateTime, index=True)
    paused_date = Column(DateTime, index=True)
    completed_date = Column(DateTime, index=True)
    
    # Notes and context
    notes = Column(Text)
    pause_reason = Column(String)  # "too scary for Simon"
    series_info = Column(String)   # "Band 8 der beliebten Kinderbuch-Reihe"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Index for ordering
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reading_entries")