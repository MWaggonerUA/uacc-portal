import os
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse
import dash
import dash_bootstrap_components as dbc

# Initialize logging first
import backend.core.logging_config  # noqa: F401

# Import routers
from backend.api.admin_uploads import router as admin_uploads_router
from backend.api.clinical_trials import router as clinical_trials_router

# Import database initialization
from backend.services.db import init_db, close_db

# Import Dash app for admin uploads
from frontend.core.app import dash_app
from frontend.modules.admin.upload_page import upload_layout

# Import Clinical Trials Dash layout
from frontend.modules.clinical_trials.upload_page import clinical_trials_layout

# Import configuration
from backend.core.config import settings

# Create separate Dash app for Clinical Trials
# Each Dash app needs its own instance with unique prefix
clinical_trials_dash_app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    routes_pathname_prefix='/',
    requests_pathname_prefix='/clinicaltrialsupload/'
)

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
    dash_app.layout = upload_layout
    
    # Set the layout for the clinical trials upload page
    clinical_trials_dash_app.layout = clinical_trials_layout
    
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

app.include_router(
    clinical_trials_router,
    prefix="/clinical-trials",
    tags=["clinical-trials"]
)

# Mount Dash apps under their respective paths
# Dash uses Flask (WSGI), so we need WSGIMiddleware to mount them
app.mount("/adminupload", WSGIMiddleware(dash_app.server))
app.mount("/clinicaltrialsupload", WSGIMiddleware(clinical_trials_dash_app.server))


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "environment": settings.APP_ENV}


@app.get("/welcome", response_class=HTMLResponse)
def welcome():
    """Welcome page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to UACC Portal</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #0C234B 0%, #1a3d6b 50%, #AB0520 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                padding: 60px 40px;
                max-width: 600px;
                width: 100%;
                text-align: center;
            }
            h1 {
                color: #0C234B;
                margin-bottom: 20px;
                font-size: 2.5em;
                font-weight: 700;
            }
            .subtitle {
                color: #666;
                font-size: 1.2em;
                margin-bottom: 40px;
                line-height: 1.6;
            }
            .links {
                display: flex;
                flex-direction: column;
                gap: 15px;
                margin-top: 40px;
            }
            a {
                display: inline-block;
                padding: 15px 30px;
                background: linear-gradient(135deg, #0C234B 0%, #AB0520 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            a:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(12, 35, 75, 0.5);
            }
            .footer {
                margin-top: 40px;
                color: #999;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to UACC Portal</h1>
            <p class="subtitle">
                Internal modular web application for UACC metrics, dashboards, and tools.
            </p>
            <div class="links">
                <a href="/adminupload">Admin Data Upload</a>
                <a href="/clinicaltrialsupload">Clinical Trials Data Upload</a>
                <a href="/docs">API Documentation</a>
            </div>
            <div class="footer">
                <p>UACC Portal v1.0.0</p>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "UACC portal is alive",
        "api_docs": "/docs",
        "admin_upload": "/adminupload",
        "clinical_trials_upload": "/clinicaltrialsupload",
        "welcome": "/welcome"
    }

