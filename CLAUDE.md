# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

### Prerequisites
- PostgreSQL running via Docker: `docker-compose up -d postgres`
- Python environment with uv: `uv venv && uv pip install -r requirements.txt`

### Main App (FastAPI)
```bash
cd main_app
uv run python main.py  # Starts on http://127.0.0.1:8000
```

### Database Schema Management
```bash
# Create tables programmatically (from main_app directory)
uv run python -c "
import sys; sys.path.insert(0, '/home/daniel/progress_tracker')
from database.config import Base, engine
from models import User, ReadingEntry, DrawingEntry, FitnessEntry
Base.metadata.create_all(bind=engine)
print('Database tables created!')
"

# Alembic migrations (if needed)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### MCP Bridge Testing
```bash
cd mcp_bridge
uv run python test_bridge.py
```

## Architecture

This is a dual-component progress tracking system:

1. **Main App** (`main_app/`): FastAPI application with PostgreSQL backend
   - Models: User, ReadingEntry, DrawingEntry, FitnessEntry with rich field support
   - API endpoints: REST APIs for all CRUD operations
   - Web interface: Simple HTML templates for direct management
   - Database: PostgreSQL with SQLAlchemy ORM

2. **MCP Bridge** (`mcp_bridge/`): FastMCP server connecting Claude Desktop to main app
   - Tools: `list_users()`, `add_*_entry()`, `list_entries()` with filtering
   - Communication: HTTP client to main app API endpoints
   - Integration: Configured in Claude Desktop's `claude_desktop_config.json`

### Key Data Models
- **Users**: Simple name/display_name model (no authentication)
- **Reading**: Books with ISBN, progress tracking, status, detailed notes
- **Drawing**: Art projects with materials, complexity, technical details
- **Fitness**: Activities with metrics, duration, achievements

### Database Configuration
- Connection string in `.env`: `DATABASE_URL=postgresql://progress_user:progress_password@localhost:5432/progress_tracker`
- Models auto-create tables on startup via `Base.metadata.create_all(bind=engine)`
- Alembic available for schema migrations if needed

### MCP Integration Pattern
The MCP bridge acts as a translation layer between Claude Desktop and the main FastAPI app, making HTTP requests to `http://127.0.0.1:8000/api/*` endpoints and formatting responses for Claude.

### UI/UX Features
- **Modern Design System**: Custom CSS framework with CSS variables, consistent spacing, and responsive design
- **Compact Navigation**: Space-efficient header with inline navigation (no API docs link)
- **Progressive Disclosure**: Forms use collapsible sections for optional fields to reduce cognitive load
- **Image Upload & Display**: Drawing entries support image uploads with drag & drop, preview, and modal viewing
- **Character Encoding**: Proper UTF-8 support for German umlauts and international characters
- **Form Enhancements**: Auto-save drafts, real-time validation, loading states, and better UX patterns
- **Mobile-First**: Responsive design that works well on all screen sizes