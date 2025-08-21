#!/usr/bin/env python3
"""
Progress Tracker MCP Bridge
Connects Claude Desktop to the Progress Tracker API
"""

import asyncio
import os
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

# Initialize FastMCP
mcp = FastMCP("Progress Tracker 📊", version="1.0.0")

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
    length_duration: Optional[str] = None
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
    """Make HTTP request to the main app API"""
    url = f"{MAIN_APP_URL}{endpoint}"
    
    async with httpx.AsyncClient() as client:
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
        
        response.raise_for_status()
        return response.json()

async def get_users() -> List[User]:
    """Get all users from the API"""
    data = await api_request("GET", "/api/users/")
    return [User(**user) for user in data]

async def get_user_by_name(name: str) -> Optional[User]:
    """Get user by name"""
    users = await get_users()
    for user in users:
        if user.name.lower() == name.lower():
            return user
    return None

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
    length_pages: Optional[int] = None,
    length_duration: Optional[str] = None,
    status: str = "pending",
    progress_fraction: Optional[float] = None,
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
        length_pages: Number of pages (for physical books)
        length_duration: Duration like "2h 34m" (for audiobooks)
        status: Current status (pending, in_progress, paused, completed, abandoned)
        progress_fraction: Progress as decimal (e.g., 0.67 for 2/3 completed)
        notes: Additional notes
        pause_reason: Reason if paused
        series_info: Series information
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
            "author": author,
            "isbn": isbn,
            "reading_type": reading_type,
            "length_pages": length_pages,
            "length_duration": length_duration,
            "status": status,
            "progress_fraction": progress_fraction,
            "notes": notes,
            "pause_reason": pause_reason,
            "series_info": series_info
        }
        
        # Set dates based on status
        current_time = datetime.now().isoformat()
        if status == "in_progress":
            entry_data["started_date"] = current_time
        elif status == "paused":
            entry_data["started_date"] = current_time
            entry_data["paused_date"] = current_time
        elif status == "completed":
            entry_data["started_date"] = current_time
            entry_data["completed_date"] = current_time
        
        # Remove None values
        entry_data = {k: v for k, v in entry_data.items() if v is not None}
        
        result = await api_request("POST", "/api/reading/", entry_data)
        
        return f"✅ Reading entry added successfully!\nTitle: {title}\nUser: {user.display_name}\nStatus: {status}"
        
    except Exception as e:
        return f"❌ Error adding reading entry: {str(e)}"

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
        
        result = await api_request("POST", "/api/drawing/", entry_data)
        
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
        
        result = await api_request("POST", "/api/fitness/", entry_data)
        
        return f"💪 Fitness entry added successfully!\nTitle: {title}\nUser: {user.display_name}\nStatus: {status}"
        
    except Exception as e:
        return f"❌ Error adding fitness entry: {str(e)}"

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