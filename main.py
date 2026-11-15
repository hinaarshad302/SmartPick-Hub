"""Vercel entry point for the canonical SmartPick Hub FastAPI application.

Keep application routes and configuration in backend/main.py so local and
hosted deployments use the same backend implementation.
"""

from backend.main import app

__all__ = ["app"]
