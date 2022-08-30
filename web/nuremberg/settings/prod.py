import os
from .generic import *

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')

COMPRESS_OFFLINE = True
COMPRESS_ENABLED = True
