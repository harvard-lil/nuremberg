from django.conf.urls import url
from django.views.generic import TemplateView

app_name = 'content'
urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='content/landing.html'), name="landing"),
    url(r'^trials$', TemplateView.as_view(template_name='content/trials.html'), name="trials"),
    url(r'^approaches$', TemplateView.as_view(template_name='content/approaches.html'), name="approaches"),
    url(r'^history$', TemplateView.as_view(template_name='content/history.html'), name="history"),
    url(r'^about$', TemplateView.as_view(template_name='content/about.html'), name="about"),
]
