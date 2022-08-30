from django.conf import settings
from django.conf.urls import include, url, re_path
from django.contrib import admin
from proxy.views import proxy_view
from django.views.generic.base import RedirectView
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from proxy.views import proxy_view

@csrf_exempt
def proxied(base_url):
    def proxy_handler(request, path):
    	remoteurl = base_url + path
    	return proxy_view(request, remoteurl)
    return proxy_handler

urlpatterns = [
    # re_path(r'^admin/', admin.site.urls),
    re_path(r'^transcripts/', include('nuremberg.transcripts.urls')),
    re_path(r'^documents/', include('nuremberg.documents.urls')),
    re_path(r'^photographs/', include('nuremberg.photographs.urls')),
    re_path(r'^search/', include('nuremberg.search.urls')),
    re_path(r'^', include('nuremberg.content.urls')),
    re_path(r'^proxy_image/printing/(?P<path>.*)$',
        # RedirectView.as_view(url='http://nuremberg.law.harvard.edu/imagedir/HLSL_NUR_printing/%(url)s')),
        proxied(base_url=settings.DOCUMENTS_PRINTING_URL)),
    re_path(r'^proxy_image/(?P<path>.*)$',
        # RedirectView.as_view(url='http://s3.amazonaws.com/nuremberg-documents/%(url)s'))
        proxied(base_url=settings.DOCUMENTS_URL), name='proxy_image'),
    re_path(r'^proxy_transcript/(?P<path>.*)$',
        proxied(base_url=settings.TRANSCRIPTS_URL), name='proxy_transcript'),
    re_path(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /search/", content_type="text/plain")),
]

handler400 = 'nuremberg.core.views.handler400'
handler403 = 'nuremberg.core.views.handler403'
handler404 = 'nuremberg.core.views.handler404'
handler500 = 'nuremberg.core.views.handler500'
