# config/settings/prod.py

import os
import dj_database_url
from .base import *

DEBUG = False

ALLOWED_HOSTS = [os.getenv("RENDER_EXTERNAL_HOSTNAME", "")]
CSRF_TRUSTED_ORIGINS = [f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', '')}"]

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# Redis-backed channel layer — required once you're not on a single dev process.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL")],
        },
    }
}

# Static files served via WhiteNoise
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True