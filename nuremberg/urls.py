from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^transcripts/', include('nuremberg.transcripts.urls')),
    url(r'^documents/', include('nuremberg.documents.urls')),
    url(r'^search/', include('nuremberg.search.urls')),
    url(r'^', include('nuremberg.content.urls')),
]
