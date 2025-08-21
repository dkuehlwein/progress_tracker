# Progress Tracker App

A comprehensive progress tracking application for reading, drawing, and fitness activities with multi-user support and Claude Desktop integration via MCP.

## Architecture

- **Main App:** FastAPI + PostgreSQL standalone application
- **MCP Bridge:** FastMCP server that connects Claude Desktop to the main app
- **Database:** PostgreSQL with rich data models
- **Frontend:** Simple web interface for direct management

## Quick Start

### 1. Start the Database
```bash
docker-compose up -d postgres
```

### 2. Set up Main App
```bash
cd main_app
cp .env.example .env
uv venv
uv pip install -r requirements.txt
uv pip install 'psycopg[binary]'  # For PostgreSQL connection
```

### 3. Create Database Tables
```bash
# From main_app directory
uv run python -c "
import sys; sys.path.insert(0, '/home/daniel/progress_tracker')
from database.config import Base, engine
from models import User, ReadingEntry, DrawingEntry, FitnessEntry
Base.metadata.create_all(bind=engine)
print('Database tables created!')
"
```

### 4. Start Main App
```bash
# From main_app directory  
uv run python main.py
```

### 5. Create Users (First Time Setup)
```bash
# Create users via API
curl -X POST "http://127.0.0.1:8000/api/users/" \
  -H "Content-Type: application/json" \
  -d '{"name": "daniel", "display_name": "Daniel (Dad)"}'

curl -X POST "http://127.0.0.1:8000/api/users/" \
  -H "Content-Type: application/json" \
  -d '{"name": "simon", "display_name": "Simon (Kid)"}'
```

### 6. Set up MCP Bridge
```bash
cd mcp_bridge
cp .env.example .env
uv venv
uv pip install -r requirements.txt
```

### 7. Test Bridge
```bash
# From mcp_bridge directory
uv run python test_bridge.py
```

### 8. Configure Claude Desktop

Add this to your Claude Desktop configuration file:

**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "progress-tracker": {
      "command": "python",
      "args": ["C:\\path\\to\\your\\progress_tracker\\mcp_bridge\\server.py"],
      "env": {
        "MAIN_APP_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

**For Linux/WSL:** Adjust the path accordingly:
```json
{
  "mcpServers": {
    "progress-tracker": {
      "command": "python",
      "args": ["/home/daniel/progress_tracker/mcp_bridge/server.py"],
      "env": {
        "MAIN_APP_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

## Features

### Progress Tracking
- **Reading:** Track books with ISBN, authors, progress, status, and detailed notes
- **Drawing:** Monitor art projects with technical details, materials, and complexity
- **Fitness:** Log activities with metrics, duration, and achievements

### Multi-User Support
- Separate tracking for different users (no authentication needed)
- Pre-configured for parent/child usage
- Each user has their own progress entries

### Claude Desktop Integration
- **Add entries:** Voice commands to add reading, drawing, or fitness progress
- **List entries:** Query your progress with filters
- **Rich data:** Supports all the detailed fields from your examples

### MCP Tools Available in Claude Desktop
- `list_users()` - Show available users
- `add_reading_entry()` - Add book progress with full detail support
- `add_drawing_entry()` - Log drawing projects with technical notes
- `add_fitness_entry()` - Track fitness activities
- `list_entries()` - View progress with filtering options

## Usage Examples

### Via Claude Desktop (MCP)
- "Add a reading entry for Simon: Harry Potter by J.K. Rowling, currently in progress"
- "Log a drawing project: Rainbow bead snake, 2000+ beads, completed over 2 days"
- "Add fitness: 30-minute run in the park, moderate intensity"
- "List all reading entries for Daniel"

### Via Web Interface
Visit http://127.0.0.1:8000 for the web interface and API documentation at http://127.0.0.1:8000/api/docs

### Via Direct API
All endpoints support full CRUD operations with rich data models matching your detailed examples.

## File Structure
```
progress_tracker/
├── main_app/           # FastAPI application
│   ├── api/            # REST API endpoints
│   ├── models/         # SQLAlchemy database models
│   ├── database/       # DB configuration
│   └── main.py         # Application entry point
├── mcp_bridge/         # FastMCP server
│   ├── server.py       # MCP tools and bridge logic
│   └── test_bridge.py  # Integration test
├── docker-compose.yml  # PostgreSQL setup
└── README.md          # This file
```