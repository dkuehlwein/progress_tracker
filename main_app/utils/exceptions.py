"""Custom exceptions for the application"""
from fastapi import HTTPException
from typing import Optional, Dict, Any


class ValidationError(HTTPException):
    """Custom validation error for forms"""
    def __init__(self, details: Dict[str, str]):
        super().__init__(
            status_code=422,
            detail={
                "error": "Validation Error",
                "details": details
            }
        )


class FileUploadError(HTTPException):
    """Custom error for file upload issues"""
    def __init__(self, message: str):
        super().__init__(
            status_code=400,
            detail={
                "error": "File Upload Error",
                "message": message
            }
        )


class DatabaseError(HTTPException):
    """Custom error for database issues"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            status_code=500,
            detail={
                "error": "Database Error", 
                "message": message
            }
        )


class NotFoundError(HTTPException):
    """Custom not found error"""
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            status_code=404,
            detail={
                "error": "Not Found",
                "message": message
            }
        )