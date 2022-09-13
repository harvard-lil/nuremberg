from django.conf.urls import url, re_path
from . import views

app_name = 'photographs'
urlpatterns = [
    re_path(r'^(?P<photograph_id>\d+)-(?P<slug>[-\w]+)?$', views.Show.as_view(), name='show'),
    re_path(r'^(?P<photograph_id>\d+)[-\w]*$', views.Show.as_view()),
]
