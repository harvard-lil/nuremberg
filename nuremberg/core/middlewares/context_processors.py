from django.conf import settings
def show_mockups(request):
    if settings.DEBUG and request.GET.get('mockup'):
        return {'show_mockup': True}
    else:
        return {'show_mockup': False}
