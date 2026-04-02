"""
core/security.py
================
API key authentication with role-based access control.

Roles:
  admin     → full access (GET + POST + DELETE)
  read_only → GET endpoints only
"""

from enum import Enum
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from core.config import get_settings

settings   = get_settings()
_api_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=True)


class Role(str, Enum):
    admin     = "admin"
    read_only = "read_only"


def _resolve_role(api_key: str) -> Role:
    if api_key == settings.API_KEY_ADMIN:
        return Role.admin
    if api_key == settings.API_KEY_READONLY:
        return Role.read_only
    raise HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail      = "Invalid or missing API key.",
        headers     = {"WWW-Authenticate": "ApiKey"},
    )


def require_api_key(api_key: str = Security(_api_header)) -> Role:
    """Dependency: any valid API key."""
    return _resolve_role(api_key)


def require_admin(api_key: str = Security(_api_header)) -> Role:
    """Dependency: admin role only."""
    role = _resolve_role(api_key)
    if role != Role.admin:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Admin access required.",
        )
    return role
