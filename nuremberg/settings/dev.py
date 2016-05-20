from nuremberg.settings.generic import *

DEBUG = True;
DATABASES['default'] = {
  'ENGINE': 'django.db.backends.mysql',
  'NAME': 'nuremberg_dev',
  'USER': 'nuremberg',
  'HOST': 'localhost',
}
