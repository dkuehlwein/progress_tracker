#!/usr/bin/env python3
"""
Progress Tracker MCP Bridge
Connects Claude Desktop to the Progress Tracker API
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx
from fastmcp import FastMCP
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MAIN_APP_URL = os.getenv("MAIN_APP_URL", "http://localhost:8000")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP("Progress Tracker 📊", version="1.0.0")
logger.info("MCP Bridge initialized")

# Pydantic models for data validation
class User(BaseModel):
    id: int
    name: str
    display_name: str

class ReadingEntry(BaseModel):
    title: str
    author: Optional[str] = None
    isbn: Optional[str] = None
    reading_type: str = "physical_book"
    length_pages: Optional[int] = None
    length_duration: Optional[int] = None
    status: str = "pending"
    progress_fraction: Optional[float] = None
    started_date: Optional[str] = None
    paused_date: Optional[str] = None
    completed_date: Optional[str] = None
    notes: Optional[str] = None
    pause_reason: Optional[str] = None
    series_info: Optional[str] = None

class DrawingEntry(BaseModel):
    title: str
    subject: Optional[str] = None
    medium: Optional[str] = None
    context: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_hours: Optional[float] = None
    sessions_count: Optional[int] = None
    process_description: Optional[str] = None
    template_used: Optional[str] = None
    assistance_level: Optional[str] = None
    technical_notes: Optional[str] = None
    materials_count: Optional[int] = None
    complexity_level: Optional[str] = None
    status: str = "planned"
    completion_notes: Optional[str] = None
    continuation_plans: Optional[str] = None
    reference_link: Optional[str] = None

class FitnessEntry(BaseModel):
    title: str
    activity_type: Optional[str] = None
    description: Optional[str] = None
    activity_date: Optional[str] = None
    duration_minutes: Optional[float] = None
    planned_duration: Optional[float] = None
    distance_km: Optional[float] = None
    calories_burned: Optional[int] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    intensity_level: Optional[str] = None
    perceived_effort: Optional[int] = None
    location: Optional[str] = None
    weather: Optional[str] = None
    equipment_used: Optional[str] = None
    status: str = "planned"
    notes: Optional[str] = None
    achievements: Optional[str] = None
    next_goals: Optional[str] = None

# Helper functions
async def api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make HTTP request to the main app API with proper error handling"""
    url = f"{MAIN_APP_URL}{endpoint}"
    
    try:
        logger.debug(f"Making {method} request to {url}")
        if data:
            logger.debug(f"Request data: {data}")
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Response data: {result}")
            return result
            
    except httpx.TimeoutException:
        logger.error(f"Request timeout for {method} {url}")
        raise Exception(f"Request timeout - the main app may be down")
    except httpx.ConnectError:
        logger.error(f"Connection error for {method} {url}")
        raise Exception(f"Cannot connect to main app at {MAIN_APP_URL}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} for {method} {url}")
        try:
            error_detail = e.response.json()
            raise Exception(f"API Error: {error_detail.get('detail', 'Unknown error')}")
        except:
            raise Exception(f"HTTP {e.response.status_code} error")
    except Exception as e:
        logger.error(f"Unexpected error for {method} {url}: {str(e)}")
        raise Exception(f"Request failed: {str(e)}")

async def get_users() -> List[User]:
    """Get all users from the API"""
    try:
        logger.debug("Fetching users from API")
        data = await api_request("GET", "/api/users/")
        users = [User(**user) for user in data]
        logger.debug(f"Found {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Failed to fetch users: {str(e)}")
        raise

async def get_user_by_name(name: str) -> Optional[User]:
    """Get user by name"""
    try:
        logger.debug(f"Looking up user by name: {name}")
        users = await get_users()
        for user in users:
            if user.name.lower() == name.lower():
                logger.debug(f"Found user: {user.display_name}")
                return user
        logger.debug(f"User not found: {name}")
        return None
    except Exception as e:
        logger.error(f"Failed to get user by name '{name}': {str(e)}")
        raise

# MCP Tools
@mcp.tool
async def list_users() -> str:
    """List all users in the progress tracker"""
    try:
        users = await get_users()
        if not users:
            return "No users found. You may need to create users first."
        
        result = "Available users:\n"
        for user in users:
            result += f"- {user.display_name} ({user.name})\n"
        return result
    except Exception as e:
        return f"Error listing users: {str(e)}"

@mcp.tool
async def add_reading_entry(
    user_name: str,
    title: str,
    author: Optional[str] = None,
    isbn: Optional[str] = None,
    reading_type: str = "physical_book",
    length_pages: Optional[str] = None,  # Accept as string, convert to int
    length_duration: Optional[str] = None,  # Accept as string, convert to int
    status: str = "pending",
    progress_fraction: Optional[str] = None,  # Accept as string, convert to float
    started_date: Optional[str] = None,  # Date format: 2024-08-15
    completed_date: Optional[str] = None,  # Date format: 2024-08-15
    paused_date: Optional[str] = None,  # Pause or abandon date format: 2024-08-15
    notes: Optional[str] = None,
    pause_reason: Optional[str] = None,
    series_info: Optional[str] = None
) -> str:
    """Add a new reading progress entry
    
    Args:
        user_name: Username (daniel or simon)
        title: Book title
        author: Book author
        isbn: ISBN number
        reading_type: Type of book (physical_book, audiobook, ebook, magazine, comic)
        length_pages: Number of pages (for physical books) - accepts string, converts to int
        length_duration: Duration in minutes (e.g., "154" for 2h 34m)
        status: Current status (pending, in_progress, paused, completed, abandoned)
        progress_fraction: Progress as decimal string (e.g., "0.67" for 2/3 completed)
        started_date: Started date in YYYY-MM-DD format (e.g., "2024-08-15")
        completed_date: Completed date in YYYY-MM-DD format (e.g., "2024-08-15")
        paused_date: Pause or abandon date in YYYY-MM-DD format (e.g., "2024-08-15")
        notes: Additional notes
        pause_reason: Paused or abandon reason
        series_info: Series information
    """
    try:
        # Get user
        user = await get_user_by_name(user_name)
        if not user:
            return f"User '{user_name}' not found. Available users: {', '.join([u.name for u in await get_users()])}"
        
        # Convert string inputs to proper types
        length_pages_int = None
        if length_pages is not None:
            try:
                length_pages_int = int(length_pages)
            except (ValueError, TypeError):
                return f"❌ Error: length_pages must be a valid integer, got '{length_pages}'"
        
        length_duration_int = None
        if length_duration is not None:
            try:
                length_duration_int = int(length_duration)
            except (ValueError, TypeError):
                return f"❌ Error: length_duration must be a valid integer, got '{length_duration}'"
        
        progress_fraction_float = None
        if progress_fraction is not None:
            try:
                progress_fraction_float = float(progress_fraction)
                if not (0.0 <= progress_fraction_float <= 1.0):
                    return f"❌ Error: progress_fraction must be between 0.0 and 1.0, got {progress_fraction_float}"
            except (ValueError, TypeError):
                return f"❌ Error: progress_fraction must be a valid decimal number, got '{progress_fraction}'"
        
        # Prepare data
        entry_data = {
            "user_id": user.id,
            "title": title,
            "author": author,
            "isbn": isbn,
            "reading_type": reading_type,
            "length_pages": length_pages_int,
            "length_duration": length_duration_int,
            "status": status,
            "progress_fraction": progress_fraction_float,
            "notes": notes,
            "pause_reason": pause_reason,
            "series_info": series_info
        }
        
        # Add dates from parameters or auto-set based on status
        if started_date:
            try:
                # Validate YYYY-MM-DD format and convert to start of day
                datetime.strptime(started_date, '%Y-%m-%d')
                entry_data["started_date"] = started_date + 'T00:00:00'
            except ValueError:
                return f"❌ Error: started_date must be in YYYY-MM-DD format (e.g., '2024-08-15'), got '{started_date}'"
        
        if completed_date:
            try:
                # Validate YYYY-MM-DD format and convert to end of day
                datetime.strptime(completed_date, '%Y-%m-%d')
                entry_data["completed_date"] = completed_date + 'T23:59:59'
            except ValueError:
                return f"❌ Error: completed_date must be in YYYY-MM-DD format (e.g., '2024-08-15'), got '{completed_date}'"
        
        if paused_date:
            try:
                # Validate YYYY-MM-DD format and convert to noon
                datetime.strptime(paused_date, '%Y-%m-%d')
                entry_data["paused_date"] = paused_date + 'T12:00:00'
            except ValueError:
                return f"❌ Error: paused_date must be in YYYY-MM-DD format (e.g., '2024-08-15'), got '{paused_date}'"
        
        # Auto-set dates based on status if not manually provided
        current_time = datetime.now().isoformat()
        if status == "in_progress" and "started_date" not in entry_data:
            entry_data["started_date"] = current_time
        elif status == "paused":
            if "started_date" not in entry_data:
                entry_data["started_date"] = current_time
            if "paused_date" not in entry_data:
                entry_data["paused_date"] = current_time
        elif status == "completed":
            if "started_date" not in entry_data:
                entry_data["started_date"] = current_time
            if "completed_date" not in entry_data:
                entry_data["completed_date"] = current_time
        
        # Remove None values
        entry_data = {k: v for k, v in entry_data.items() if v is not None}
        
        response = await api_request("POST", "/api/reading/", entry_data)
        
        return f"✅ Reading entry added successfully!\nID: {response['id']}\nTitle: {title}\nUser: {user.display_name}\nStatus: {status}\n\n💡 You can edit this entry using: edit_reading_entry(entry_id={response['id']}, ...)"
        
    except Exception as e:
        return f"❌ Error adding reading entry: {str(e)}"

@mcp.tool
async def edit_reading_entry(
    entry_id: int,
    title: Optional[str] = None,
    author: Optional[str] = None,
    isbn: Optional[str] = None,
    reading_type: Optional[str] = None,
    length_pages: Optional[str] = None,
    length_duration: Optional[str] = None,
    status: Optional[str] = None,
    progress_fraction: Optional[str] = None,
    started_date: Optional[str] = None,
    completed_date: Optional[str] = None,
    paused_date: Optional[str] = None,
    notes: Optional[str] = None,
    pause_reason: Optional[str] = None,
    series_info: Optional[str] = None
) -> str:
    """Edit an existing reading entry
    
    Args:
        entry_id: ID of the reading entry to edit
        title: Book title
        author: Book author
        isbn: ISBN number
        reading_type: Type of book (physical_book, audiobook, ebook, magazine, comic)
        length_pages: Number of pages (for physical books)
        length_duration: Duration in minutes (for audiobooks)
        status: Current status (pending, in_progress, paused, completed, abandoned)
        progress_fraction: Progress as decimal string (e.g., "0.67" for 2/3 completed)
        started_date: Started date in YYYY-MM-DD format (e.g., "2024-08-15")
        completed_date: Completed date in YYYY-MM-DD format (e.g., "2024-08-15")
        paused_date: Pause or abandon date in YYYY-MM-DD format (e.g., "2024-08-15")
        notes: Additional notes
        pause_reason: Paused or abandon reason
        series_info: Series information
    """
    try:
        # Get current entry
        current_entry = await api_request("GET", f"/api/reading/{entry_id}")
        
        # Prepare update data with only non-None values
        update_data = {}
        
        if title is not None:
            update_data["title"] = title
        if author is not None:
            update_data["author"] = author
        if isbn is not None:
            update_data["isbn"] = isbn
        if reading_type is not None:
            update_data["reading_type"] = reading_type
            
        # Convert string inputs to proper types
        if length_pages is not None:
            try:
                update_data["length_pages"] = int(length_pages) if length_pages.strip() else None
            except (ValueError, TypeError):
                return f"❌ Error: length_pages must be a valid integer, got '{length_pages}'"
        
        if length_duration is not None:
            try:
                update_data["length_duration"] = int(length_duration) if length_duration.strip() else None
            except (ValueError, TypeError):
                return f"❌ Error: length_duration must be a valid integer, got '{length_duration}'"
        
        if status is not None:
            update_data["status"] = status
            
        if progress_fraction is not None:
            try:
                pf = float(progress_fraction) if progress_fraction.strip() else None
                if pf is not None and not (0.0 <= pf <= 1.0):
                    return f"❌ Error: progress_fraction must be between 0.0 and 1.0, got {pf}"
                update_data["progress_fraction"] = pf
            except (ValueError, TypeError):
                return f"❌ Error: progress_fraction must be a valid decimal number, got '{progress_fraction}'"
        
        # Handle dates
        date_mappings = [
            ("started_date", started_date, "T00:00:00"),
            ("completed_date", completed_date, "T23:59:59"),
            ("paused_date", paused_date, "T12:00:00")
        ]
        
        for date_field, date_value, time_suffix in date_mappings:
            if date_value is not None:
                if date_value.strip():
                    try:
                        # Validate YYYY-MM-DD format
                        datetime.strptime(date_value, '%Y-%m-%d')
                        update_data[date_field] = date_value + time_suffix
                    except ValueError:
                        return f"❌ Error: {date_field} must be in YYYY-MM-DD format (e.g., '2024-08-15'), got '{date_value}'"
                else:
                    update_data[date_field] = None
        
        if notes is not None:
            update_data["notes"] = notes
        if pause_reason is not None:
            update_data["pause_reason"] = pause_reason
        if series_info is not None:
            update_data["series_info"] = series_info
        
        # Update the entry
        response = await api_request("PUT", f"/api/reading/{entry_id}", update_data)
        
        return f"✅ Reading entry updated successfully!\nID: {response['id']}\nTitle: {response['title']}\nStatus: {response['status']}"
        
    except Exception as e:
        return f"❌ Error editing reading entry: {str(e)}"

@mcp.tool
async def add_drawing_entry(
    user_name: str,
    title: str,
    subject: Optional[str] = None,
    medium: Optional[str] = None,
    context: Optional[str] = None,
    duration_hours: Optional[float] = None,
    sessions_count: Optional[int] = None,
    materials_count: Optional[int] = None,
    status: str = "planned",
    technical_notes: Optional[str] = None,
    complexity_level: Optional[str] = None
) -> str:
    """Add a new drawing progress entry
    
    Args:
        user_name: Username (daniel or simon)
        title: Drawing project title
        subject: What was drawn (e.g., "Rainbow snake design")
        medium: Medium used (colored_pencils, crayons, markers, watercolor, digital, beads, mixed_media)
        context: Context of the work (e.g., "Multi-day home project")
        duration_hours: Total time spent in hours
        sessions_count: Number of work sessions
        materials_count: Number of materials used (e.g., 2000+ beads)
        status: Current status (planned, in_progress, completed, abandoned, continued_next_day)
        technical_notes: Technical achievements and notes
        complexity_level: Complexity (beginner, intermediate, advanced)
    """
    try:
        # Get user
        user = await get_user_by_name(user_name)
        if not user:
            return f"User '{user_name}' not found. Available users: {', '.join([u.name for u in await get_users()])}"
        
        # Prepare data
        entry_data = {
            "user_id": user.id,
            "title": title,
            "subject": subject,
            "medium": medium,
            "context": context,
            "duration_hours": duration_hours,
            "sessions_count": sessions_count,
            "materials_count": materials_count,
            "status": status,
            "technical_notes": technical_notes,
            "complexity_level": complexity_level
        }
        
        # Set dates based on status
        current_time = datetime.now().isoformat()
        if status == "in_progress":
            entry_data["start_date"] = current_time
        elif status == "completed":
            entry_data["start_date"] = current_time
            entry_data["end_date"] = current_time
        
        # Remove None values
        entry_data = {k: v for k, v in entry_data.items() if v is not None}
        
        await api_request("POST", "/api/drawing/", entry_data)
        
        return f"🎨 Drawing entry added successfully!\nTitle: {title}\nUser: {user.display_name}\nStatus: {status}"
        
    except Exception as e:
        return f"❌ Error adding drawing entry: {str(e)}"

@mcp.tool
async def add_fitness_entry(
    user_name: str,
    title: str,
    activity_type: Optional[str] = None,
    description: Optional[str] = None,
    duration_minutes: Optional[float] = None,
    distance_km: Optional[float] = None,
    intensity_level: Optional[str] = None,
    location: Optional[str] = None,
    status: str = "planned",
    notes: Optional[str] = None
) -> str:
    """Add a new fitness progress entry
    
    Args:
        user_name: Username (daniel or simon)
        title: Activity title
        activity_type: Type of activity (cardio, strength, flexibility, sports, walking, running, cycling, swimming, yoga, other)
        description: Activity description
        duration_minutes: Duration in minutes
        distance_km: Distance in kilometers
        intensity_level: Intensity (low, moderate, high, very high)
        location: Where the activity took place
        status: Current status (planned, in_progress, completed, skipped, cancelled)
        notes: Additional notes
    """
    try:
        # Get user
        user = await get_user_by_name(user_name)
        if not user:
            return f"User '{user_name}' not found. Available users: {', '.join([u.name for u in await get_users()])}"
        
        # Prepare data
        entry_data = {
            "user_id": user.id,
            "title": title,
            "activity_type": activity_type,
            "description": description,
            "duration_minutes": duration_minutes,
            "distance_km": distance_km,
            "intensity_level": intensity_level,
            "location": location,
            "status": status,
            "notes": notes
        }
        
        # Set activity date based on status
        current_time = datetime.now().isoformat()
        if status in ["in_progress", "completed"]:
            entry_data["activity_date"] = current_time
        
        # Remove None values
        entry_data = {k: v for k, v in entry_data.items() if v is not None}
        
        await api_request("POST", "/api/fitness/", entry_data)
        
        return f"💪 Fitness entry added successfully!\nTitle: {title}\nUser: {user.display_name}\nStatus: {status}"
        
    except Exception as e:
        return f"❌ Error adding fitness entry: {str(e)}"

@mcp.tool
async def get_entry_details(
    entry_id: int,
    category: str
) -> str:
    """Get detailed information about a specific entry for editing
    
    Args:
        entry_id: ID of the entry to view
        category: Entry category (reading, drawing, fitness)
    """
    try:
        # Validate category
        if category not in ["reading", "drawing", "fitness"]:
            return f"❌ Invalid category: {category}. Must be one of: reading, drawing, fitness"
        
        # Get the entry
        try:
            entry = await api_request("GET", f"/api/{category}/{entry_id}")
        except Exception as e:
            if "404" in str(e):
                return f"❌ Entry with ID {entry_id} not found in {category} category"
            raise e
        
        # Get user info
        users = await get_users()
        user_name = next((u.display_name for u in users if u.id == entry.get('user_id')), "Unknown User")
        
        # Format the entry details
        category_emoji = {"reading": "📚", "drawing": "🎨", "fitness": "💪"}
        emoji = category_emoji.get(category, "ℹ️")
        
        result = f"{emoji} {category.title()} Entry Details (ID: {entry_id})\n"
        result += f"User: {user_name}\n"
        result += f"Title: {entry.get('title', 'No title')}\n"
        result += f"Status: {entry.get('status', 'Unknown')}\n"
        
        # Add category-specific details
        if category == "reading":
            if entry.get('author'): result += f"Author: {entry['author']}\n"
            if entry.get('isbn'): result += f"ISBN: {entry['isbn']}\n"
            if entry.get('reading_type'): result += f"Type: {entry['reading_type']}\n"
            if entry.get('length_pages'): result += f"Pages: {entry['length_pages']}\n"
            if entry.get('length_duration'): result += f"Duration (min): {entry['length_duration']}\n"
            if entry.get('progress_fraction'): result += f"Progress: {entry['progress_fraction']*100:.1f}%\n"
            if entry.get('notes'): result += f"Notes: {entry['notes']}\n"
            if entry.get('series_info'): result += f"Series: {entry['series_info']}\n"
        
        elif category == "drawing":
            if entry.get('subject'): result += f"Subject: {entry['subject']}\n"
            if entry.get('medium'): result += f"Medium: {entry['medium']}\n"
            if entry.get('context'): result += f"Context: {entry['context']}\n"
            if entry.get('duration_hours'): result += f"Duration: {entry['duration_hours']} hours\n"
            if entry.get('sessions_count'): result += f"Sessions: {entry['sessions_count']}\n"
            if entry.get('complexity_level'): result += f"Complexity: {entry['complexity_level']}\n"
            if entry.get('technical_notes'): result += f"Technical Notes: {entry['technical_notes']}\n"
            if entry.get('materials_count'): result += f"Materials Count: {entry['materials_count']}\n"
        
        else:  # fitness
            if entry.get('activity_type'): result += f"Activity Type: {entry['activity_type']}\n"
            if entry.get('description'): result += f"Description: {entry['description']}\n"
            if entry.get('duration_minutes'): result += f"Duration: {entry['duration_minutes']} minutes\n"
            if entry.get('distance_km'): result += f"Distance: {entry['distance_km']} km\n"
            if entry.get('intensity_level'): result += f"Intensity: {entry['intensity_level']}\n"
            if entry.get('location'): result += f"Location: {entry['location']}\n"
            if entry.get('notes'): result += f"Notes: {entry['notes']}\n"
        
        # Add timestamps
        if entry.get('created_at'):
            result += f"Created: {entry['created_at']}\n"
        if entry.get('updated_at'):
            result += f"Updated: {entry['updated_at']}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error getting entry details: {str(e)}"

@mcp.tool
async def edit_entry(
    entry_id: int,
    category: str,
    user_name: Optional[str] = None,
    title: Optional[str] = None,
    status: Optional[str] = None,
    # Reading fields
    author: Optional[str] = None,
    isbn: Optional[str] = None,
    reading_type: Optional[str] = None,
    length_pages: Optional[str] = None,
    length_duration: Optional[str] = None,
    progress_fraction: Optional[str] = None,
    notes: Optional[str] = None,
    pause_reason: Optional[str] = None,
    series_info: Optional[str] = None,
    # Drawing fields
    subject: Optional[str] = None,
    medium: Optional[str] = None,
    context: Optional[str] = None,
    location: Optional[str] = None,
    duration_hours: Optional[str] = None,
    sessions_count: Optional[str] = None,
    process_description: Optional[str] = None,
    technical_notes: Optional[str] = None,
    materials_count: Optional[str] = None,
    complexity_level: Optional[str] = None,
    completion_notes: Optional[str] = None,
    continuation_plans: Optional[str] = None,
    reference_link: Optional[str] = None,
    # Fitness fields
    activity_type: Optional[str] = None,
    description: Optional[str] = None,
    duration_minutes: Optional[str] = None,
    distance_km: Optional[str] = None,
    intensity_level: Optional[str] = None,
    achievements: Optional[str] = None,
    next_goals: Optional[str] = None,
    # Additional fitness fields
    calories_burned: Optional[str] = None,
    heart_rate_avg: Optional[str] = None,
    heart_rate_max: Optional[str] = None,
    perceived_effort: Optional[str] = None,
    weather: Optional[str] = None,
    equipment_used: Optional[str] = None
) -> str:
    """Edit an existing progress entry
    
    Args:
        entry_id: ID of the entry to edit
        category: Entry category (reading, drawing, fitness)
        user_name: Optional - verify entry belongs to this user
        title: Optional - new title
        status: Optional - new status
        
    Reading fields: author, isbn, reading_type, length_pages, length_duration, 
                   progress_fraction, notes, pause_reason, series_info
    Drawing fields: subject, medium, context, location, duration_hours, sessions_count,
                   process_description, technical_notes, materials_count, complexity_level,
                   completion_notes, continuation_plans, reference_link
    Fitness fields: activity_type, description, duration_minutes, distance_km,
                   intensity_level, notes, achievements, next_goals, calories_burned,
                   heart_rate_avg, heart_rate_max, perceived_effort, weather, equipment_used
    """
    try:
        # Validate category
        if category not in ["reading", "drawing", "fitness"]:
            return f"❌ Invalid category: {category}. Must be one of: reading, drawing, fitness"
        
        # First, get the existing entry to verify it exists and get user info
        try:
            existing_entry = await api_request("GET", f"/api/{category}/{entry_id}")
        except Exception as e:
            if "404" in str(e):
                return f"❌ Entry with ID {entry_id} not found in {category} category"
            raise e
        
        # If user_name provided, verify the entry belongs to that user
        if user_name:
            users = await get_users()
            target_user = next((u for u in users if u.name.lower() == user_name.lower()), None)
            if not target_user:
                return f"❌ User '{user_name}' not found"
            if existing_entry.get('user_id') != target_user.id:
                return f"❌ Entry {entry_id} does not belong to user '{user_name}'"
        
        # Build update data - only include non-None values
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if status is not None:
            update_data["status"] = status
        
        # Collect all possible field parameters
        all_fields = {
            # Reading fields
            'author': author, 'isbn': isbn, 'reading_type': reading_type,
            'length_pages': length_pages, 'length_duration': length_duration,
            'progress_fraction': progress_fraction, 'notes': notes,
            'pause_reason': pause_reason, 'series_info': series_info,
            # Drawing fields  
            'subject': subject, 'medium': medium, 'context': context,
            'location': location, 'duration_hours': duration_hours,
            'sessions_count': sessions_count, 'process_description': process_description,
            'technical_notes': technical_notes, 'materials_count': materials_count,
            'complexity_level': complexity_level, 'completion_notes': completion_notes,
            'continuation_plans': continuation_plans, 'reference_link': reference_link,
            # Fitness fields
            'activity_type': activity_type, 'description': description,
            'duration_minutes': duration_minutes, 'distance_km': distance_km,
            'intensity_level': intensity_level, 'achievements': achievements,
            'next_goals': next_goals, 'calories_burned': calories_burned,
            'heart_rate_avg': heart_rate_avg, 'heart_rate_max': heart_rate_max,
            'perceived_effort': perceived_effort, 'weather': weather,
            'equipment_used': equipment_used
        }
        
        # Add category-specific fields
        for field, value in all_fields.items():
            if value is not None:
                # Handle numeric conversions
                if field in ['length_pages', 'length_duration', 'sessions_count', 'materials_count', 'calories_burned', 'heart_rate_avg', 'heart_rate_max', 'perceived_effort']:
                    try:
                        update_data[field] = int(value)
                    except (ValueError, TypeError):
                        return f"❌ Error: {field} must be a valid integer, got '{value}'"
                elif field in ['progress_fraction', 'duration_hours', 'duration_minutes', 'distance_km']:
                    try:
                        float_value = float(value)
                        if field == 'progress_fraction' and not (0.0 <= float_value <= 1.0):
                            return f"❌ Error: progress_fraction must be between 0.0 and 1.0, got {float_value}"
                        update_data[field] = float_value
                    except (ValueError, TypeError):
                        return f"❌ Error: {field} must be a valid number, got '{value}'"
                else:
                    update_data[field] = value
        
        if not update_data:
            return f"❌ No fields to update. Please provide at least one field to modify."
        
        # Make the update request
        updated_entry = await api_request("PUT", f"/api/{category}/{entry_id}", update_data)
        
        # Get user info for response
        users = await get_users()
        user_name_display = next((u.display_name for u in users if u.id == updated_entry.get('user_id')), "Unknown User")
        
        # Format success message
        category_emoji = {"reading": "📚", "drawing": "🎨", "fitness": "💪"}
        emoji = category_emoji.get(category, "✅")
        
        return f"{emoji} {category.title()} entry updated successfully!\nID: {entry_id}\nTitle: {updated_entry.get('title', 'Unknown')}\nUser: {user_name_display}\nStatus: {updated_entry.get('status', 'Unknown')}"
        
    except Exception as e:
        return f"❌ Error editing {category} entry: {str(e)}"

@mcp.tool
async def list_entries(
    user_name: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> str:
    """List progress entries with optional filtering
    
    Args:
        user_name: Filter by username (daniel or simon)
        category: Filter by category (reading, drawing, fitness)
        status: Filter by status
        limit: Maximum number of entries to return
    """
    try:
        user_filter = ""
        if user_name:
            user = await get_user_by_name(user_name)
            if user:
                user_filter = f"?user_id={user.id}"
            else:
                return f"User '{user_name}' not found."
        
        status_param = f"&status={status}" if status else "" if user_filter else f"?status={status}" if status else ""
        
        results = []
        
        # Get entries based on category filter
        categories = [category] if category else ["reading", "drawing", "fitness"]
        
        for cat in categories:
            try:
                endpoint = f"/api/{cat}/{user_filter}{status_param}"
                data = await api_request("GET", endpoint)
                
                # Limit results
                limited_data = data[:limit] if len(data) > limit else data
                
                if limited_data:
                    results.append(f"\n📚 {cat.title()} Entries:")
                    for entry in limited_data:
                        title = entry.get('title', 'Untitled')
                        status = entry.get('status', 'Unknown')
                        user_id = entry.get('user_id')
                        
                        # Get user name
                        users = await get_users()
                        user_name = next((u.display_name for u in users if u.id == user_id), "Unknown User")
                        
                        # Format entry based on type
                        if cat == "reading":
                            author = entry.get('author', '')
                            author_str = f" by {author}" if author else ""
                            results.append(f"  • {title}{author_str} [{status}] - {user_name}")
                        elif cat == "drawing":
                            subject = entry.get('subject', '')
                            subject_str = f" ({subject})" if subject else ""
                            results.append(f"  • {title}{subject_str} [{status}] - {user_name}")
                        else:  # fitness
                            activity_type = entry.get('activity_type', '')
                            type_str = f" ({activity_type})" if activity_type else ""
                            results.append(f"  • {title}{type_str} [{status}] - {user_name}")
            except Exception as e:
                results.append(f"  ❌ Error fetching {cat} entries: {str(e)}")
        
        if not results:
            return "No entries found matching the criteria."
        
        return "".join(results)
        
    except Exception as e:
        return f"❌ Error listing entries: {str(e)}"

if __name__ == "__main__":
    mcp.run()