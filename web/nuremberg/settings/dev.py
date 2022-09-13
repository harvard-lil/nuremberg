from .generic import *

SECRET_KEY = 'supersecret'
DEBUG = True
COMPRESS_ENABLED = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

STATIC_PRECOMPILER_COMPILERS = (
    ('static_precompiler.compilers.LESS', {
      "executable": "lessc",
      "sourcemap_enabled": True,
    }),
)

# MIDDLEWARE_CLASSES.append('django_cprofile_middleware.middleware.ProfilerMiddleware')
