"""
Development settings — extends base.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

# Allow all hosts in dev
ALLOWED_HOSTS = ["*"]

# Disable throttling during development
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

# Use console email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS — allow everything in dev
CORS_ALLOW_ALL_ORIGINS = True

# Debug toolbar (optional, install django-debug-toolbar)
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
# INTERNAL_IPS = ["127.0.0.1"]
