"""Configuración de GameMarket. Los secretos se leen desde variables de entorno."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'gamemarket_dev.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
