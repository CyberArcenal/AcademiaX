import logging
import dj_database_url
import os
from .base import *
from .logger import *

LOGGER = logging.getLogger(__name__)
DEBUG = True
DOCKER_MODE = False
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

if DOCKER_MODE:
    REDIS_URL = REDIS_URL
else:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}


if DOCKER_MODE:
    DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": "db",
        "PORT": 5432,
    }
}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }


"""
Development settings for Huddle Platform. This configuration is optimized for local development and testing, with features like debug mode enabled, relaxed security settings, and simplified database configuration. It is not suitable for production use.
"""
