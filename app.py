import os
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

# Initialize logging first
import backend.core.logging_config  # noqa: F401

# Import routers
from backend.api.admin_uploads import router as admin_uploads_router

# Import database initialization
from backend.services.db import init_db, close_db

# Import Dash app
from frontend.core.app import dash_app
from frontend.modules.admin.upload_page import upload_layout

# Import configuration
from backend.core.config import settings

app = FastAPI(
    title="UACC Portal",
    description="Internal modular web application for UACC metrics, dashboards, and tools",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.
    - Validate environment
    - Initialize database connections
    - Set up Dash app routing
    """
    # Validate environment (optional - config.py handles defaults)
    # Add any required validation here if needed
    
    # Initialize database tables (uncomment when ready)
    # await init_db()
    
    # Set the layout for the admin upload page
    # In the future, you can add routing logic here to switch between different module layouts
    dash_app.layout = upload_layout
    
    print(f"UACC Portal started in {settings.APP_ENV} mode")
    print(f"Temporary file directory: {settings.TEMP_DIR}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up on application shutdown.
    """
    # Close database connections
    await close_db()


# Include API routers
app.include_router(
    admin_uploads_router,
    prefix="/admin",
    tags=["admin"]
)

# Mount Dash app under /dash path
# Dash uses Flask (WSGI), so we need WSGIMiddleware to mount it
app.mount("/dash", WSGIMiddleware(dash_app.server))


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "environment": settings.APP_ENV}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "UACC portal is alive",
        "api_docs": "/docs",
        "dash_app": "/dash"
    }

