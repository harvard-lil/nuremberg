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
    page_count = 3
    page_alignment = 10
    def get(self, request, transcript_id, *args, **kwargs):
        # document = Document.objects.get(id=document_id)
        transcript = Transcript.objects.get(id=transcript_id)
        seq_number = int(request.GET.get('seq', 1))

        # find the seq number for provided page number
        # we have to be a bit tricky because page numbers can repeat
        page_number = int(request.GET.get('page', 0))
        if page_number:
            page = transcript.pages.filter(page_number=page_number).extra(select={'distance': "ABS(seq_number - %s)"}, select_params=(seq_number,), order_by=('distance',)).first()
            if page:
                seq_number = page.seq_number
            else:
                # guesstimate
                page = transcript.pages.filter(page_number__lte=page_number).order_by('-page_number').first()
                if page:
                    seq_number = page.seq_number + (page_number - page.page_number)

        # find the seq number for provided date
        # assume dates are valid since they come from selection
        page_date = request.GET.get('date')
        if page_date:
            page_date = datetime.strptime(page_date, '%Y-%m-%d')
            page = transcript.pages.filter(page_number=page_number).order_by('seq_number').first()
            if page:
                seq_number = page.seq_number

        # so that page ranges are generally cacheable, we align initial page loads to 10-page strides, plus 1
        # e.g. requesting seq=10, 13, or 19 will get you pages 1 - 30 inclusive,
        # so all future range requests will be aligned to 31 - 40 and so on.
        from_seq = int(request.GET.get('from_seq', (seq_number // self.page_alignment) * self.page_alignment - self.page_alignment))
        to_seq = int(request.GET.get('to_seq', (seq_number // self.page_alignment) * self.page_alignment + self.page_alignment + 1))

        from_seq = transcript.clamp_seq(from_seq)
        to_seq = transcript.clamp_seq(to_seq)

        print('joining pages >=',from_seq,', <=',to_seq)
        total_pages = transcript.pages.count()
        pages = transcript.pages.filter(seq_number__gte=from_seq, seq_number__lte=to_seq).all()

        joiner = TranscriptPageJoiner(pages, include_first=from_seq == 1, include_last=to_seq == total_pages)
        joiner.build_html()


        if request.GET.get('partial'):
            return JsonResponse({'html': joiner.html, 'from_seq': joiner.from_seq, 'to_seq': joiner.to_seq, 'seq': seq_number})

        current_page = next(page for page in pages if page.seq_number == seq_number)
        return render(request, self.template_name, {
            'transcript': transcript,
            'pages': pages,
            'joiner': joiner,
            'seq': seq_number,
            'page_count': self.page_count,
            'total_pages': total_pages,
            'dates': transcript.dates(),
            'current_page': current_page,
            'query': request.GET.get('query')
            })
