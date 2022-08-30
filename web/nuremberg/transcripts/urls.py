from django.conf.urls import url, re_path
from . import views

app_name = 'transcripts'
urlpatterns = [
    re_path(r'^(?P<transcript_id>\d+)-(?P<slug>[\-\w]+)?/search$', views.Search.as_view(), name='search'),
    re_path(r'^(?P<transcript_id>\d+)[^/]*/search$', views.Search.as_view()),
    re_path(r'^(?P<transcript_id>\d+)-(?P<slug>[\-\w]+)?$', views.Show.as_view(), name='show'),
    re_path(r'^(?P<transcript_id>\d+)][^/]*$', views.Show.as_view(), name='show'),

]
