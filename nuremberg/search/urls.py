from django.conf.urls import include, url, re_path
from . import views

app_name = 'search'
urlpatterns = [
    # re_path(r'$', views.Search.as_view(), name='search'),
    re_path(r'$', views.Search.as_view(), name='search')
]
