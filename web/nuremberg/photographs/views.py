from .models import Photograph

from django.shortcuts import render
from django.views.generic import View

class Show(View):
    template_name = 'photographs/show.html'
    def get(self, request, photograph_id, *args, **kwargs):
        document = Photograph.objects.get(id=photograph_id)

        return render(request, self.template_name,
            {'document': document,
            'query': request.GET.get('q'),
        })
