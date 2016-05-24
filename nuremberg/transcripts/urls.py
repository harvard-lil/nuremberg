from django.conf.urls import url
from . import views

app_name = 'transcripts'
urlpatterns = [
    url(r'^(?P<transcript_id>\d+)(?:[-\w]+)?$', views.Show.as_view(), name='show'),
]
