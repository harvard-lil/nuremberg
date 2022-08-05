import pytest

@pytest.fixture()
def django_db_setup(settings):
    settings.DATABASES["default"] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'nuremberg_dev.db',
        'USER': 'nuremberg',
        'HOST': 'localhost',
    }
