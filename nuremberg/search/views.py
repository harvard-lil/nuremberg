from nuremberg.documents.models import Document

from django.shortcuts import render
from django.views.generic import View

class Search(View):
    template_name = 'search/results.html'
    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', None)
        if query:
            results = Document.objects
            for word in query.split(' '):
                results = results.filter(title__icontains=word)
        else:
            results = []
        return render(request, self.template_name, {'query': query, 'results': results})
