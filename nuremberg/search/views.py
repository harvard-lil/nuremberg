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
            results = results[0:9]
        else:
            results = []
        current_page = 5
        total_pages = 50
        pagination = {
            'current_page': current_page,
            'total_pages': total_pages,
            'page_numbers_to_display': range(max(1, current_page - 5), min(current_page + 5, total_pages)),
        }
        return render(request, self.template_name, {'query': query, 'results': results, 'pagination': pagination})
