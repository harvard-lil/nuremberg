from django.conf.urls import url
from .views import ContentView

app_name = 'content'
urlpatterns = [
    url(r'^$', ContentView.as_view(template_name='content/landing.html', context={'query': ''}), name="landing"),
    url(r'^trials$', ContentView.as_view(template_name='content/trials.html'), name="trials"),
    url(r'^approaches$', ContentView.as_view(template_name='content/approaches.html'), name="approaches"),
    url(r'^history$', ContentView.as_view(template_name='content/history.html'), name="history"),
    url(r'^about$', ContentView.as_view(template_name='content/about.html'), name="about"),

    url(r'^people$', ContentView.as_view(template_name='content/people.html'), name="people"),
    url(r'^intro$', ContentView.as_view(template_name='content/about.html'), name="intro"),
    url(r'^funding$', ContentView.as_view(template_name='content/funding.html'), name="funding"),
    url(r'^additional$', ContentView.as_view(template_name='content/history.html'), name="additional"),
    url(r'^documents$', ContentView.as_view(template_name='content/documents.html'), name="documents"),
    url(r'^nmt_1_intro$', ContentView.as_view(template_name='content/nmt_1_intro.html'), name="nmt_1_intro"),
    url(r'^nmt_2_intro$', ContentView.as_view(template_name='content/nmt_2_intro.html'), name="nmt_2_intro"),
    url(r'^nmt_3_intro$', ContentView.as_view(template_name='content/nmt_3_intro.html'), name="nmt_3_intro"),
    url(r'^nmt_4_intro$', ContentView.as_view(template_name='content/nmt_4_intro.html'), name="nmt_4_intro"),
    url(r'^nmt_7_intro$', ContentView.as_view(template_name='content/nmt_7_intro.html'), name="nmt_7_intro")
]
