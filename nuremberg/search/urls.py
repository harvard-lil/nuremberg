from django.conf.urls import include, url
from . import views

app_name = 'search'
urlpatterns = [
    # url(r'$', views.Search.as_view(), name='search'),
    url(r'$', views.Search.as_view(), name='search')
]
