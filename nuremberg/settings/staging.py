from .generic import *
import dj_database_url

DEBUG = True
DATABASES['default'] = dj_database_url.config(env='CLEARDB_DATABASE_URL')
del DATABASES['default']['OPTIONS']['reconnect'] # not supported by mysqlclient apparently

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
