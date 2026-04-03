"""
Configuration settings for the Co-op Support Application.
"""
import os

# Database configuration
DATABASE_PATH = 'instance/coop_app.db'

# Flask secret key for sessions (generate a random one for production)
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

# Debug mode (set to False in production)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
