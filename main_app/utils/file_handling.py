"""File handling utilities"""
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
from utils.validation import validate_image_upload, sanitize_filename
from utils.exceptions import FileUploadError
from config import UPLOAD_DIR


def save_uploaded_image(image: Optional[UploadFile]) -> Tuple[Optional[str], Optional[str]]:
    """Save uploaded image file safely
    
    Returns:
        Tuple of (image_url, image_filename) or (None, None) if no file
        
    Raises:
        FileUploadError: If file validation or saving fails
    """
    if not image or not image.filename:
        return None, None
    
    # Validate the file
    validation_error = validate_image_upload(image)
    if validation_error:
        raise FileUploadError(validation_error)
    
    try:
        # Create uploads directory if it doesn't exist
        upload_path = Path(UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        original_filename = sanitize_filename(image.filename)
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_path / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Return URL and filename
        image_url = f"/static/uploads/{unique_filename}"
        return image_url, unique_filename
        
    except Exception as e:
        raise FileUploadError(f"Failed to save image: {str(e)}")


def delete_uploaded_image(filename: Optional[str]) -> bool:
    """Delete uploaded image file
    
    Returns:
        True if file was deleted or didn't exist, False if deletion failed
    """
    if not filename:
        return True
    
    try:
        image_path = Path(UPLOAD_DIR) / filename
        if image_path.exists():
            image_path.unlink()
        return True
    except Exception:
        return False