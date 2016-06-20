from datetime import datetime
from django.shortcuts import render
from django.http.response import JsonResponse
from django.views.generic import View
from nuremberg.search.views import Search as GenericSearchView
from .models import Transcript
from .xml import TranscriptPageJoiner
import json

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
    page_alignment = 10

    def get(self, request, transcript_id, *args, **kwargs):
        transcript = Transcript.objects.get(id=transcript_id)
        total_pages = transcript.pages.count()

        seq_number = int(request.GET.get('seq', 1))
        page_number = int(request.GET.get('page', 0))
        if page_number:
            seq_number = transcript.get_seq_from_page_number(page_number, seq_number)

        page_date = request.GET.get('date')
        if page_date:
            seq_number = transcript.get_seq_from_page_date(page_date, seq_number)

        from_seq, to_seq = self.get_request_seq_range(request, seq_number)

        from_seq = transcript.clamp_seq(from_seq)
        to_seq = transcript.clamp_seq(to_seq)

        pages = transcript.pages.filter(seq_number__gte=from_seq, seq_number__lte=to_seq).all()
        joiner = TranscriptPageJoiner(pages, include_first=from_seq == 1, include_last=to_seq == total_pages)
        joiner.build_html()

        if request.GET.get('partial'):
            return JsonResponse({'html': joiner.html, 'from_seq': joiner.from_seq, 'to_seq': joiner.to_seq, 'seq': seq_number})

        current_page = next(page for page in pages if page.seq_number == seq_number)
        return render(request, self.template_name, {
            'transcript': transcript,
            'joiner': joiner,
            'seq': seq_number,
            'total_pages': total_pages,
            'dates': transcript.dates(),
            'current_page': current_page,
            'query': request.GET.get('q'),
            })

    def get_request_seq_range(self, request, seq_number):
        # so that page ranges are generally cacheable, we align initial page loads to 10-page strides, plus 1
        # e.g. requesting seq=10, 13, or 19 will get you pages 1 - 30 inclusive,
        # so all future range requests will be aligned to 31 - 40 and so on.
        from_seq = int(request.GET.get('from_seq', (seq_number // self.page_alignment) * self.page_alignment - self.page_alignment))
        to_seq = int(request.GET.get('to_seq', (seq_number // self.page_alignment) * self.page_alignment + self.page_alignment + 1))

        return (from_seq, to_seq)
