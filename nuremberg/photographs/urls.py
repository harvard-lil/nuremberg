from django.conf.urls import url
from . import views

app_name = 'photographs'
urlpatterns = [
    url(r'^(?P<photograph_id>\d+)-(?P<slug>[-\w]+)?$', views.Show.as_view(), name='show'),
    url(r'^(?P<photograph_id>\d+)[-\w]*$', views.Show.as_view()),
]
