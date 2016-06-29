from django.conf import settings

def show_mockups(request):
    if settings.DEBUG and request.GET.get('mockup'):
        return {'show_mockup': True}
    else:
        return {'show_mockup': False}

def settings_variables(request):
    if not settings.COMPRESS_ENABLED:
        return {
            'COMPRESS_ENABLED': settings.COMPRESS_ENABLED
        }
    else:
        return {}
