# UACC Portal Setup Guide

## Overview

This document describes the structure and setup of the UACC Portal application, which combines FastAPI (backend) and Dash (frontend) in a single deployable application.

## Architecture

- **Backend**: FastAPI with modular routers, services, and models
- **Frontend**: Dash application mounted under FastAPI at `/dash`
- **Database**: MySQL with async SQLAlchemy (ready for implementation)
- **Deployment**: Single ASGI application served by uvicorn

## Directory Structure

```
uacc-portal/
├── app.py                 # Main FastAPI app entry point
├── backend/
│   ├── api/              # FastAPI route handlers
│   │   └── admin_uploads.py
│   ├── core/             # Core utilities
│   │   ├── config.py     # Environment-aware configuration
│   │   └── dependencies.py  # FastAPI dependencies (RBAC placeholders)
│   ├── models/           # Pydantic models and schemas
│   │   └── upload_models.py
│   └── services/         # Business logic and data access
│       ├── db.py         # Database connection management
│       └── upload_service.py
├── frontend/
│   ├── core/
│   │   └── app.py        # Base Dash app
│   └── modules/
│       └── admin/
│           └── upload_page.py
└── requirements.txt
```

## Configuration

### Local Development

The app automatically loads configuration from (in priority order, highest to lowest):

1. **Environment variables** (always highest priority)
2. **User config file**: `~/.config/uacc/.env` (recommended for local development)
3. **Project `.env` file**: `.env` in the project root (if it exists)
4. **Server config**: `~/config/env/uacc_db.env` (if on server)
5. **Default values** (lowest priority)

**Recommended setup for local development:**
- Store your database credentials in `~/.config/uacc/.env`
- This keeps credentials out of the project directory and git

### Server Deployment

The app automatically detects server deployment by checking for `~/config/env/uacc_db.env`.

**Configuration Priority** (highest to lowest):
1. Environment variables
2. User config `~/.config/uacc/.env` (if exists)
3. Project `.env` file (if exists)
4. Server `~/config/env/uacc_db.env` (deployment)
5. Default values

### Environment Variables

- `DB_HOST`: MySQL host
- `DB_PORT`: MySQL port (default: 3306)
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `APP_ENV`: Environment (development/staging/production)
- `TEMP_DIR`: Temporary file storage path (default: `~/data/tmp`)
- `API_BASE_URL`: Base URL for API (used by Dash frontend)

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up local configuration (if developing locally):
   - Ensure your database credentials are in `~/.config/uacc/.env`
   - The app will automatically load from this location
   - Alternatively, you can create a `.env` file in the project root

3. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

## API Endpoints

### Admin Uploads

- `POST /admin/uploads/raw-data` - Upload and process CSV/Excel files
- `GET /admin/uploads/status` - Get upload status (placeholder)

### Other

- `GET /health` - Health check
- `GET /` - Root endpoint
- `GET /docs` - FastAPI interactive documentation

## Dash Frontend

The Dash application is mounted at `/dash` and can be accessed at:
- `http://localhost:8000/dash` - Admin upload page

## Database Setup

The database connection is configured but not yet initialized. To enable database operations:

1. Uncomment database initialization in `app.py`:
   ```python
   await init_db()
   ```

2. Create ORM models in `backend/models/` (e.g., `orm_models.py`)

3. Import models in `backend/services/db.py` before calling `init_db()`

4. Implement database write operations in `backend/services/upload_service.py`

## Future Enhancements

### RBAC (Role-Based Access Control)

Dependencies are already set up in `backend/core/dependencies.py`:
- `require_admin()` - Admin-only access
- `require_leadership()` - Leadership or admin access

To enable:
1. Implement `get_current_user()` to extract user from Shibboleth/JWT
2. Uncomment `Depends(require_admin)` in route decorators

### Additional Modules

To add new upload modules:
1. Create new service in `backend/services/`
2. Create new router in `backend/api/`
3. Include router in `app.py`
4. Create Dash page in `frontend/modules/[role]/`

### Separating Services

The architecture is designed to easily split Dash and FastAPI into separate services:
- Dash already calls FastAPI via HTTP (`API_BASE_URL`)
- No direct database access from Dash
- Services are cleanly separated

## Development Notes

- File uploads are saved to temporary storage, processed, then deleted
- Validation is currently basic (empty row check) - extend as needed
- Database writes are stubbed - implement when ready
- All database access goes through FastAPI endpoints (no direct DB access from Dash)


