# Vercel Serverless Function entry point for the FastAPI AI service.
#
# Vercel looks for an ASGI application inside /api, so this file exposes the
# FastAPI "app" object defined in main.py, which stays at the project root.
#
# Run locally with:
#   uvicorn api.index:app --reload --port 8000
# or
#   uvicorn main:app --reload --port 8000

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app  # noqa: E402,F401