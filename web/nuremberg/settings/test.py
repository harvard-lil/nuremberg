from .dev import *

COMPRESS_ENABLED = False

ALLOWED_HOSTS = ['web', 'localhost']

# Needed for template coverage report
TEMPLATES[0]['OPTIONS']['debug'] = True

# disable cache during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
