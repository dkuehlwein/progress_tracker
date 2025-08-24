from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Basic information
    date = Column(Date, nullable=False, index=True)  # Index for date queries
    title = Column(String, index=True)  # Optional quick reference
    location = Column(String)  # "Home, Bonn", "Botanical garden"
    
    # Main content
    context = Column(Text, nullable=False)  # Required: situation and timing details
    parental_input = Column(Text)  # Optional: parent observations/notes
    ai_analysis = Column(Text)  # Optional: structured analysis
    
    # Tags for filtering and overview insights
    tags = Column(String)  # Comma-separated: "conflict,achievement"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="journal_entries")