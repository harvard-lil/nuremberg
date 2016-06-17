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

class TranscriptVolume(models.Model):
    transcript = models.ForeignKey(Transcript, related_name='volumes', on_delete=models.PROTECT)

    volume_number = models.IntegerField()
    description = models.TextField(blank=True, null=True)

class TranscriptPageQuerySet(models.QuerySet):
    use_for_related_fields = True
    def joined_text(self):
        joiner = TranscriptPageJoiner(self.all())
        return joiner.html()

class TranscriptPage(models.Model):
    objects = TranscriptPageQuerySet.as_manager()

    transcript = models.ForeignKey(Transcript, related_name='pages', on_delete=models.PROTECT)
    volume = models.ForeignKey(TranscriptVolume, related_name='pages', on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    seq_number = models.IntegerField(db_index=True)
    volume_seq_number = models.IntegerField(db_index=True)

    date = models.DateTimeField(blank=True, null=True)
    page_number = models.IntegerField(blank=True, null=True)
    page_label = models.CharField(max_length=10, blank=True, null=True)

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
                page_int = re.sub(r'[^\d]', self.page_label, '')
                if page_int:
                    self.page_number = int(page_int)
                else:
                    self.page_number = None

    def text(self):
        text = ''
        for event, element in etree.iterwalk(self.xml_tree()):
            if event != 'end':
                continue
            if element.tag == 'p' :
                # print(element, element.text)
                if len(element) and element[0].tag == 'runningHead':
                    continue
                if element.text:
                    if len(element.text) < 20 and self.ignore_p.match(element.text):
                        continue
                    text += element.text
                text += '\n\n'
            elif element.tag == 'spkr':
                if element.text:
                    text += '<span class="speaker">{}</span>'.format(element.text)
                if element.tail:
                    text += element.tail
            elif element.tag in ('evidenceFileDoc', 'exhibitDocDef', 'exhibitDocPros'):
                text += element.text
                text += element.tail
        return text


    class Meta:
        unique_together = (
                ('transcript', 'seq_number'),
                ('volume', 'volume_seq_number')
            )
        index_together = (
                ('transcript', 'seq_number'),
                ('volume', 'volume_seq_number')
            )
