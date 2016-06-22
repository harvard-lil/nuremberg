import re
from io import BytesIO
from lxml import etree
from datetime import datetime
from django.utils.text import slugify

from django.db import models
from nuremberg.documents.models import DocumentCase
from .xml import TranscriptPageJoiner

class Transcript(models.Model):
    case = models.OneToOneField(DocumentCase, related_name='transcript', on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def slug(self):
        return slugify(self.title)

    def clamp_seq(self, seq):
        return min(max(seq, 1), self.pages.count())

    def dates(self):
        return self.pages.order_by().values_list('date', flat=True).distinct()



    def get_seq_from_page_date(self, page_date, seq_number):
        # find the seq number for provided date
        # assume dates are valid since they come from selection
        page_date = datetime.strptime(page_date, '%Y-%m-%d')
        page = self.pages.filter(date=page_date).order_by('seq_number').first()
        if page:
            return page.seq_number
        return seq_number

    def get_seq_from_page_number(self, page_number, seq_number):
        # find the seq number for provided page number
        # we have to be a bit tricky because page numbers can repeat
        page = self.pages.filter(page_number=page_number).extra(select={'distance': "ABS(seq_number - %s)"}, select_params=(seq_number,), order_by=('distance',)).first()
        if page:
            return page.seq_number
        else:
            # guesstimate
            page = self.pages.filter(page_number__lte=page_number).order_by('-page_number').first()
            if page:
                return page.seq_number + (page_number - page.page_number)

        return seq_number

class TranscriptVolume(models.Model):
    transcript = models.ForeignKey(Transcript, related_name='volumes', on_delete=models.PROTECT)

    volume_number = models.IntegerField()
    description = models.TextField(blank=True, null=True)

# class TranscriptPageQuerySet(models.QuerySet):
#     use_for_related_fields = True
#     def joined_text(self):
#         joiner = TranscriptPageJoiner(self.all())
#         return joiner.html()

class TranscriptPage(models.Model):
    # objects = TranscriptPageQuerySet.as_manager()

    transcript = models.ForeignKey(Transcript, related_name='pages', on_delete=models.PROTECT)
    volume = models.ForeignKey(TranscriptVolume, related_name='pages', on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    seq_number = models.IntegerField(db_index=True)
    volume_seq_number = models.IntegerField(db_index=True)

    date = models.DateTimeField(db_index=True, blank=True, null=True)
    page_number = models.IntegerField(blank=True, null=True)
    page_label = models.CharField(max_length=10, blank=True, null=True)

    image_url = models.TextField(blank=True, null=True)

    xml = models.TextField()

    def xml_tree(self):
        return etree.fromstring(self.xml.encode('utf8'))

    def populate_from_xml(self):
        for event, element in etree.iterwalk(self.xml_tree()):
            if event != 'end':
                continue
            if element.tag == 'seqNo':
                self.seq_number = int(element.text)
            elif element.tag == 'sessionDate':
                try:
                    self.date = datetime.strptime(element.get('n'), '%Y-%m-%d')
                except:
                    self.date = None
            elif element.tag == 'pageNum':
                self.page_label = element.get('n')
                page_int = re.sub(r'[^\d]', '', self.page_label)
                if page_int:
                    self.page_number = int(page_int)
                else:
                    self.page_number = None

    def text(self):
        text = ''
        for event, element in etree.iterwalk(self.xml_tree(), events=('start', 'end')):
            if element.tag == 'p' :
                if len(element) and element[0].tag == 'runningHead':
                    continue
                if event == 'start':
                    if element.text:
                        if len(element.text) < 20 and TranscriptPageJoiner.ignore_p.match(element.text):
                            continue
                        text += element.text
                else:
                    text += '\n\n'
            elif event == 'end' and element.tag == 'spkr':
                if element.text:
                    text += '<span class="speaker">{}</span> '.format(element.text)
                if element.tail: text += element.tail
            elif event == 'end' and element.tag in ('evidenceFileDoc', 'exhibitDocDef', 'exhibitDocPros'):
                if element.text: text += element.text
                if element.tail: text += element.tail
        return text

    def extract_evidence_codes(self):
        codes = []
        for event, element in etree.iterwalk(self.xml_tree()):
            if element.tag == 'evidenceFileDoc':
                codes.append(element.get('n'))
        return codes

    def extract_exhibit_codes(self):
        codes = []
        for event, element in etree.iterwalk(self.xml_tree()):
            if element.tag == 'exhibitDocPros':
                codes.append('Prosecution {}'.format(element.get('n')))
            elif element.tag == 'exhibitDocDef':
                codes.append('{} {}'.format(element.get('def') or 'Unknown Defendant', element.get('n')))
        return codes

    class Meta:
        unique_together = (
                ('transcript', 'seq_number'),
                ('volume', 'volume_seq_number')
            )
        index_together = (
                ('transcript', 'seq_number'),
                ('transcript', 'page_number'),
                ('transcript', 'date'),
                ('volume', 'volume_seq_number')
            )
