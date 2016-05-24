from django.conf.urls import url
from . import views

app_name = 'transcripts'
urlpatterns = [
    url(r'^(?P<transcript_id>\d+)(?:[-\w]+)?$', views.Show.as_view(), name='show'),
    url(r'^(?P<transcript_id>\d+)(?:[-\w]+)?/search$', views.Search.as_view(), name='search'),
]
