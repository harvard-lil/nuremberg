from .models import Document

from django.shortcuts import render
from django.views.generic import View

class Show(View):
    template_name = 'documents/show.html'
    def get(self, request, document_id, *args, **kwargs):
        document = Document.objects \
        .prefetch_related('images') \
        .select_related('language') \
        .select_related('source') \
        .get(id=document_id)

        return render(request, self.template_name,
            {'document': document,
            'query': request.GET.get('q'),
        })
