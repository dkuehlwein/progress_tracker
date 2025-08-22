"""Application configuration settings"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
def get_database_url():
    if os.getenv("USE_DEV_DB", "false").lower() == "true":
        return os.getenv(
            "DATABASE_URL_DEV",
            "postgresql+psycopg://progress_user_dev:progress_password_dev@localhost:5433/progress_tracker_dev"
        )
    return os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg://progress_user:progress_password@localhost:5432/progress_tracker"
    )

DATABASE_URL = get_database_url()

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# File Upload Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "web/static/uploads")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10MB default
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# Pagination Configuration
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", 10))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", 100))

# Application Constants
APP_NAME = "Progress Tracker"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Track reading, drawing, and fitness progress for family members"

# Date/Time Configuration
DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "Europe/Berlin")
STATS_HISTORY_MONTHS = int(os.getenv("STATS_HISTORY_MONTHS", 6))

# UI Configuration
RECENT_ENTRIES_LIMIT = int(os.getenv("RECENT_ENTRIES_LIMIT", 5))
DASHBOARD_ENTRIES_LIMIT = int(os.getenv("DASHBOARD_ENTRIES_LIMIT", 3))

# User-specific constants
SIMON_USER_NAME = "simon"
SIMON_EMOJI = "🧒"
DEFAULT_USER_EMOJI = "👨"

# Status Display Names
READING_STATUSES = ["pending", "in_progress", "paused", "completed", "abandoned"]
READING_TYPES = ["physical_book", "audiobook", "ebook", "magazine", "comic"]
DRAWING_STATUSES = ["planned", "in_progress", "completed", "abandoned", "continued_next_day"]
DRAWING_MEDIUMS = ["colored_pencils", "crayons", "markers", "watercolor", "digital", "beads", "mixed_media"]
FITNESS_STATUSES = ["planned", "in_progress", "completed", "skipped", "cancelled"]
FITNESS_TYPES = ["cardio", "strength", "flexibility", "sports", "walking", "running", "cycling", "swimming", "yoga", "other"]