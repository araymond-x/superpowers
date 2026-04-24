"""Pytest configuration — adds Pydantic models to import path."""

import sys
from pathlib import Path

MODELS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "skills" / "scripts" / "models"
)
sys.path.insert(0, str(MODELS_DIR))
