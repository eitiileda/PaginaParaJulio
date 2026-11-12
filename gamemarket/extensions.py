"""Extensiones compartidas por los módulos de la aplicación."""
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
