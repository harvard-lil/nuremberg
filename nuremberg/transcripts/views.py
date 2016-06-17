from django.shortcuts import render
from django.views.generic import View
from nuremberg.search.views import Search as GenericSearchView
from .models import Transcript

class Search(GenericSearchView):
    template_name = 'transcripts/search.html'

    paginate_by = 10
    default_sort = 'page'

    def get(self, request, transcript_id, *args, **kwargs):
        self.transcript = Transcript.objects.get(id=transcript_id)
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'transcript_id': self.transcript.id
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'transcript': self.transcript})
        return context

class Show(View):
    template_name = 'transcripts/show.html'
    page_count = 100
    def get(self, request, transcript_id, *args, **kwargs):
        # document = Document.objects.get(id=document_id)
        transcript = Transcript.objects.get(id=transcript_id)
        seq_number = int(request.GET.get('seq', 1))
        pages = transcript.pages.filter(seq_number__gte=seq_number, seq_number__lte=seq_number+self.page_count)
        return render(request, self.template_name, {'transcript': transcript, 'pages': pages})
