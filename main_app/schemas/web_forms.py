"""Pydantic schemas for web form validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from models import ReadingStatus, ReadingType, DrawingStatus, DrawingMedium, FitnessStatus, FitnessType


class ReadingFormSchema(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID must be positive")
    title: str = Field(..., min_length=1, max_length=500, description="Title is required")
    author: Optional[str] = Field(None, max_length=200)
    isbn: Optional[str] = Field(None, max_length=20, regex=r'^[\d\-X]*$')
    reading_type: str = Field("physical_book", description="Reading type")
    length_pages: Optional[int] = Field(None, ge=1, le=10000)
    length_duration: Optional[str] = Field(None, max_length=20, regex=r'^\d+h\s*\d*m?$|^\d+m$')
    status: str = Field("pending", description="Reading status")
    progress_fraction: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = Field(None, max_length=2000)
    pause_reason: Optional[str] = Field(None, max_length=500)
    series_info: Optional[str] = Field(None, max_length=500)
    
    @validator('reading_type')
    def validate_reading_type(cls, v):
        valid_types = [t.value for t in ReadingType]
        if v not in valid_types:
            raise ValueError(f'Invalid reading type. Must be one of: {valid_types}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = [s.value for s in ReadingStatus]
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v


class DrawingFormSchema(BaseModel):
    user_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=500)
    subject: Optional[str] = Field(None, max_length=500)
    medium: Optional[str] = Field(None)
    context: Optional[str] = Field(None, max_length=1000)
    duration_hours: Optional[float] = Field(None, ge=0, le=100)
    sessions_count: Optional[int] = Field(None, ge=1, le=100)
    materials_count: Optional[int] = Field(None, ge=1, le=1000000)
    status: str = Field("planned")
    technical_notes: Optional[str] = Field(None, max_length=2000)
    complexity_level: Optional[str] = Field(None, regex=r'^(beginner|intermediate|advanced)$')
    reference_link: Optional[str] = Field(None, max_length=500)
    
    @validator('medium')
    def validate_medium(cls, v):
        if v is None:
            return v
        valid_mediums = [m.value for m in DrawingMedium]
        if v not in valid_mediums:
            raise ValueError(f'Invalid medium. Must be one of: {valid_mediums}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = [s.value for s in DrawingStatus]
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v


class FitnessFormSchema(BaseModel):
    user_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=500)
    activity_type: Optional[str] = Field(None)
    description: Optional[str] = Field(None, max_length=1000)
    duration_minutes: Optional[float] = Field(None, ge=0, le=1440)  # Max 24 hours
    distance_km: Optional[float] = Field(None, ge=0, le=1000)
    intensity_level: Optional[str] = Field(None, regex=r'^(low|moderate|high|very high)$')
    location: Optional[str] = Field(None, max_length=200)
    status: str = Field("planned")
    notes: Optional[str] = Field(None, max_length=2000)
    
    @validator('activity_type')
    def validate_activity_type(cls, v):
        if v is None:
            return v
        valid_types = [t.value for t in FitnessType]
        if v not in valid_types:
            raise ValueError(f'Invalid activity type. Must be one of: {valid_types}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = [s.value for s in FitnessStatus]
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v