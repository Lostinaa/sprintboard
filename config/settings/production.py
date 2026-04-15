"""
Production settings — extends base.
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# Security hardening
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)  # noqa: F405
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Ensure SECRET_KEY is set in production
assert SECRET_KEY != "insecure-dev-key-change-me", (  # noqa: F405
    "You must set a real SECRET_KEY in production!"
)
