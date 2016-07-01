from django.conf.urls import url
from .views import ContentView

app_name = 'content'
urlpatterns = [
    url(r'^$', ContentView.as_view(template_name='content/landing.html', context={'query': ''}), name="landing"),
    url(r'^trials$', ContentView.as_view(template_name='content/trials.html'), name="trials"),
    url(r'^approaches$', ContentView.as_view(template_name='content/approaches.html'), name="approaches"),
    url(r'^history$', ContentView.as_view(template_name='content/history.html'), name="history"),
    url(r'^about$', ContentView.as_view(template_name='content/about.html'), name="about"),

    url(r'^people$', ContentView.as_view(template_name='content/trials.html'), name="people"),
    url(r'^intro$', ContentView.as_view(template_name='content/trials.html'), name="intro"),
    url(r'^funding$', ContentView.as_view(template_name='content/trials.html'), name="funding"),
    url(r'^additional$', ContentView.as_view(template_name='content/trials.html'), name="additional"),
]
