"""
Development settings for restaurant_manager project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Override CORS_ALLOWED_ORIGINS from base (not needed when CORS_ALLOW_ALL_ORIGINS is True)
# But we need to ensure it's not set incorrectly
CORS_ALLOWED_ORIGINS = []

# Database - can use SQLite for local dev if needed
# Uncomment if you want to use SQLite instead of PostgreSQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

