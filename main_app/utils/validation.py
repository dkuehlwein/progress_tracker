"""Validation utilities for web forms and file uploads"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, date
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, ValidationError
from config import ALLOWED_IMAGE_EXTENSIONS, MAX_UPLOAD_SIZE


class ValidationErrorResponse(BaseModel):
    """Standardized validation error response"""
    error: str = "Validation Error"
    details: Dict[str, Any]
    status_code: int = 422


def validate_form_data(schema: BaseModel, form_data: Dict[str, Any]) -> BaseModel:
    """Validate form data against Pydantic schema"""
    try:
        # Clean form data - convert empty strings to None
        cleaned_data = {}
        for key, value in form_data.items():
            if isinstance(value, str) and value.strip() == "":
                cleaned_data[key] = None
            else:
                cleaned_data[key] = value
        
        return schema(**cleaned_data)
    except ValidationError as e:
        error_details = {}
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            error_details[field] = error['msg']
        
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Validation Error",
                "details": error_details
            }
        )


def validate_image_upload(file: Optional[UploadFile]) -> Optional[str]:
    """Validate uploaded image file
    
    Returns:
        Error message if validation fails, None if valid or no file
    """
    if not file or not file.filename:
        return None
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        return f"Invalid file type. Allowed extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
    
    # Check file size if available
    if hasattr(file, 'size') and file.size and file.size > MAX_UPLOAD_SIZE:
        return f"File too large. Maximum size: {MAX_UPLOAD_SIZE // (1024*1024)}MB"
    
    # Check content type
    if file.content_type and not file.content_type.startswith('image/'):
        return "File must be an image"
    
    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
    sanitized = ''.join(c if c in safe_chars else '_' for c in filename)
    
    # Ensure reasonable length
    if len(sanitized) > 100:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:90] + ext
    
    return sanitized


def parse_optional_int(value: Optional[str]) -> Optional[int]:
    """Parse optional integer from form input, handling empty strings"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_optional_float(value: Optional[str]) -> Optional[float]:
    """Parse optional float from form input, handling empty strings"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_optional_date(value: Optional[str]) -> Optional[date]:
    """Parse optional date from form input (YYYY-MM-DD format)"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        return datetime.fromisoformat(value).date()
    except (ValueError, TypeError):
        return None


def clean_optional_string(value: Optional[str]) -> Optional[str]:
    """Clean optional string from form input, converting empty strings to None"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    return value