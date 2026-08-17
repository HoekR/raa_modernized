"""Minimal editorial auth (API key). Replace with session/OIDC in E2."""

from __future__ import annotations

from fastapi import Header, HTTPException

from raa_api.config import editorial_settings


def require_editor(
    x_editorial_api_key: str | None = Header(default=None, alias="X-Editorial-Api-Key"),
    authorization: str | None = Header(default=None),
) -> str:
    """Validate editor credentials; return editor id label for audit."""
    settings = editorial_settings()
    if not settings.enabled or not settings.api_key:
        raise HTTPException(
            status_code=503,
            detail="Editorial API disabled (set [editorial] in config.local.toml)",
        )
    token = x_editorial_api_key
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token or token != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return settings.editor_id
