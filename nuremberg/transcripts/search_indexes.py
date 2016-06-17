from haystack import indexes
from nuremberg.documents.models import Document
from nuremberg.transcripts.models import TranscriptPage

class TranscriptPageIndex(indexes.SearchIndex, indexes.Indexable):
    sentinel = '\x03'
    text = indexes.CharField(document=True, use_template=True)
    material_type = indexes.CharField(default='Transcript', faceted=True)
    grouping_key = indexes.CharField()

    slug = indexes.CharField(model_attr='transcript__slug', indexed=False)
    transcript_id = indexes.CharField(model_attr='transcript__id')
    title = indexes.CharField(model_attr='transcript__title')

    language = indexes.CharField(default='English', faceted=True)
    source = indexes.CharField(default='Trial Transcript', faceted=True)

    seq_number = indexes.IntegerField(model_attr='seq_number')
    volume_number = indexes.CharField(model_attr='volume__volume_number')
    volume_seq_number = indexes.CharField(model_attr='volume_seq_number')
    page_label = indexes.CharField(model_attr='page_label', null=True)

    date = indexes.CharField(faceted=True, null=True)
    date_year = indexes.CharField(faceted=True, null=True)

    authors = indexes.MultiValueField(faceted=True, null=True)
    defendants = indexes.MultiValueField(faceted=True, null=True)
    case_names = indexes.CharField(model_attr='transcript__case__short_name')
    case_tags = indexes.CharField(model_attr='transcript__case__tag_name')

    def get_model(self):
        return TranscriptPage

    def get_updated_field(self):
        return 'updated_at'

    def prepare_grouping_key(self, document):
        # This is a hack to group transcripts but not documents in a single query.
        # Transcripts get a group key, documents get a unique key.
        # This can be changed to make grouping work on volume or something else.
        return 'Transcript_{}'.format(document.transcript.id)

    def prepare_date(self, document):
        if document.date:
            return document.date.strftime('%d %B %Y')

    def prepare_date_year(self, document):
        if document.date:
            return document.date.year

    def prepare_defendants(self, document):
        return []

    def prepare_authors(self, document):
        return []
