"""
FastAPI dependencies for authentication, authorization, and shared utilities.

This module will be extended with RBAC dependencies as authentication is implemented.
"""
from fastapi import Depends, HTTPException, status
from typing import Optional


# Placeholder for future authentication dependency
async def get_current_user():
    """
    Placeholder for future authentication.
    
    This will eventually:
    - Extract user info from Shibboleth headers or JWT tokens
    - Return user object with role information
    - Be used as a dependency in protected routes
    """
    # TODO: Implement actual authentication
    return {"user_id": "admin", "role": "admin"}


# Placeholder for admin-only dependency
async def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency that ensures the current user has admin role.
    
    Usage:
        @router.post("/admin/uploads/raw-data", dependencies=[Depends(require_admin)])
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Placeholder for leadership role dependency
async def require_leadership(current_user: dict = Depends(get_current_user)):
    """
    Dependency that ensures the current user has leadership or admin role.
    """
    role = current_user.get("role")
    if role not in ["admin", "leadership"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Leadership access required"
        )
    return current_user

