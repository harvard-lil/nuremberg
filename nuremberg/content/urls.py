from django.conf.urls import url, re_path
from .views import ContentView

app_name = 'content'
urlpatterns = [
    re_path(r'^$', ContentView.as_view(template_name='content/landing.html', context={'query': ''}), name="landing"),
    re_path(r'^trials$', ContentView.as_view(template_name='content/trials.html'), name="trials"),
    re_path(r'^approaches$', ContentView.as_view(template_name='content/approaches.html'), name="approaches"),
    re_path(r'^history$', ContentView.as_view(template_name='content/history.html'), name="history"),
    re_path(r'^about$', ContentView.as_view(template_name='content/about.html'), name="about"),

    re_path(r'^people$', ContentView.as_view(template_name='content/people.html'), name="people"),
    re_path(r'^intro$', ContentView.as_view(template_name='content/about.html'), name="intro"),
    re_path(r'^funding$', ContentView.as_view(template_name='content/funding.html'), name="funding"),
    re_path(r'^additional$', ContentView.as_view(template_name='content/history.html'), name="additional"),
    re_path(r'^documents$', ContentView.as_view(template_name='content/documents.html'), name="documents"),
    re_path(r'^nmt_1_intro$', ContentView.as_view(template_name='content/nmt_1_intro.html'), name="nmt_1_intro"),
    re_path(r'^nmt_2_intro$', ContentView.as_view(template_name='content/nmt_2_intro.html'), name="nmt_2_intro"),
    re_path(r'^nmt_3_intro$', ContentView.as_view(template_name='content/nmt_3_intro.html'), name="nmt_3_intro"),
    re_path(r'^nmt_4_intro$', ContentView.as_view(template_name='content/nmt_4_intro.html'), name="nmt_4_intro"),
    re_path(r'^nmt_7_intro$', ContentView.as_view(template_name='content/nmt_7_intro.html'), name="nmt_7_intro")
]
