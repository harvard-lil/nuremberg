from django.conf.urls import url
from . import views

app_name = 'transcripts'
urlpatterns = [
    url(r'^(?P<transcript_id>\d+)-(?P<slug>[\-\w]+)?/search$', views.Search.as_view(), name='search'),
    url(r'^(?P<transcript_id>\d+)/search$', views.Search.as_view()),
    url(r'^(?P<transcript_id>\d+)-?(?P<slug>[\-\w]+)?$', views.Show.as_view(), name='show'),
]
