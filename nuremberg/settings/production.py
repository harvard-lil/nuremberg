import sys
from .generic import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = [".herokuapp.com", ".law.harvard.edu"]

COMPRESS_ENABLED = True

# such that the precompiler will only auto-compile on manage.py compress
STATIC_PRECOMPILER_DISABLE_AUTO_COMPILE = False
COMPRESS_OFFLINE = True

DATABASES['default'] = dj_database_url.config(env='CLEARDB_DATABASE_URL')
del DATABASES['default']['OPTIONS']['reconnect'] # not supported by mysqlclient apparently

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'nuremberg.search.lib.solr_grouping_backend.GroupedSolrEngine',
        'URL': os.environ.get('OPENSOLR_URL', ''),
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console':{
            'level':'INFO',
            'class':'logging.StreamHandler',
            'stream': sys.stdout
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
