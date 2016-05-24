from .generic import *

SECRET_KEY = '@xf59!g4b(=z==*@#(0hdjc$_q5taw-t-1m#9@o!nzx_h1z@r9'
DEBUG = True
COMPRESS_ENABLED = False
DATABASES['default'] = {
  'ENGINE': 'django.db.backends.mysql',
  'NAME': 'nuremberg_dev',
  'USER': 'nuremberg',
  'HOST': 'localhost',
}

STATIC_PRECOMPILER_COMPILERS = (
    ('static_precompiler.compilers.LESS', {
      "executable": "lessc",
      "sourcemap_enabled": True,
    }),
)
