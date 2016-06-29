from django.conf.urls import url
from . import views

app_name = 'documents'
urlpatterns = [
    url(r'^(?P<document_id>\d+)-(?P<slug>[-\w]+)?$', views.Show.as_view(), name='show'),
    url(r'^(?P<document_id>\d+)[-\w]*$', views.Show.as_view()),
]
