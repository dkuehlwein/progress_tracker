from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from api import reading, drawing, fitness, users, web
from database.config import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Progress Tracker API",
    description="Track reading, drawing, and fitness progress for multiple users",
    version="1.0.0"
)

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
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)