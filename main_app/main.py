from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from api import reading, drawing, fitness, users, web
from database.config import engine, Base
from config import APP_NAME, APP_DESCRIPTION, APP_VERSION, DEBUG
from utils.logging import setup_logging, get_logger

# Setup logging
log_level = "DEBUG" if DEBUG else "INFO"
setup_logging(level=log_level)
logger = get_logger(__name__)

# Create database tables
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

app = FastAPI(
    title=f"{APP_NAME} API",
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

logger.info(f"Starting {APP_NAME} API v{APP_VERSION}")

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web/templates")

# Include API routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(reading.router, prefix="/api/reading", tags=["reading"])
app.include_router(drawing.router, prefix="/api/drawing", tags=["drawing"])
app.include_router(fitness.router, prefix="/api/fitness", tags=["fitness"])

# Include web interface
app.include_router(web.router)

@app.get("/", response_class=HTMLResponse)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/web")

if __name__ == "__main__":
    import argparse
    import uvicorn
    from config import HOST, PORT, DEBUG
    
    parser = argparse.ArgumentParser(description="Progress Tracker API")
    parser.add_argument("--dev", action="store_true", help="Use development database")
    args = parser.parse_args()
    
    if args.dev:
        import os
        os.environ["USE_DEV_DB"] = "true"
        logger.info("Using development database")
    
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)