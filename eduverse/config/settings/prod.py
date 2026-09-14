from .base import *

DEBUG = False

# Production database
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "mydb",
#         "USER": "myuser",
#         "PASSWORD": "securepassword",
#         "HOST": "db.example.com",
#         "PORT": "5432",
#     }
# }

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# --- Uncomment this instead, once you have Redis available ---
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")],
#         },
#     }
# }