"""FastAPI application entry point.

The implementation lives in backend/main.py. Keeping this file allows the
project to run with the familiar command: uvicorn main:app --reload
"""

from backend.main import app


__all__ = ["app"]
