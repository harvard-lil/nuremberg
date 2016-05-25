import pytest
pytestmark = pytest.mark.django_db

import sure
from django.test import Client
from django.core.urlresolvers import reverse as url
from pyquery import PyQuery

client = Client()
