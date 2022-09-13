from haystack import indexes
from nuremberg.documents.models import Document
from nuremberg.transcripts.models import TranscriptPage

class DocumentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    material_type = indexes.CharField(default='Document', faceted=True)
    grouping_key = indexes.FacetCharField(facet_for='grouping_key') # not really a facet, just an exact key

    slug = indexes.CharField(model_attr='slug', indexed=False)
    title = indexes.CharField(model_attr='title')
    literal_title = indexes.CharField(model_attr='literal_title', null=True)

    total_pages = indexes.IntegerField(model_attr='image_count', default=0, null=True)
    date = indexes.CharField(faceted=True, null=True)
    date_year = indexes.CharField(faceted=True, null=True)
    date_sort = indexes.DateTimeField(model_attr='date', null=True)

    language = indexes.CharField(model_attr='language__name', faceted=True, null=True)
    source = indexes.CharField(model_attr='source__name', faceted=True, null=True)

    authors = indexes.MultiValueField(faceted=True, null=True)
    defendants = indexes.MultiValueField(faceted=True, null=True)
    case_names = indexes.MultiValueField(faceted=True, null=True)
    case_tags = indexes.MultiValueField(faceted=True, null=True)

    evidence_codes = indexes.MultiValueField(null=True)
    exhibit_codes = indexes.MultiValueField(null=True)

    trial_activities = indexes.MultiValueField(faceted=True, null=True)

    def get_model(self):
        return Document

    def get_updated_field(self):
        return 'updated_at'

    def index_queryset(self, using=None):
        return Document.objects \
            .select_related() \
            .prefetch_related('dates') \
            .prefetch_related('cases') \
            .prefetch_related('personal_authors') \
            .prefetch_related('group_authors') \
            .prefetch_related('defendants') \
            .all()

    def prepare_grouping_key(self, document):
        # This is a hack to group transcripts but not documents in a single query.
        # Transcripts get a group key, documents get a unique key.
        # This can be changed to make grouping work on volume or something else.
        return 'Document_{}'.format(document.id)

    def prepare_authors(self, document):
        return [author.short_name() for author in document.group_authors.all()] + \
            [author.full_name() for author in document.personal_authors.all()]


    def prepare_trial_activities(self, document):
        return [activity.short_name for activity in document.activities.all()]

    def prepare_date(self, document):
        date = document.date()
        if date:
            return date.strftime('%d %B %Y')

    def prepare_date_year(self, document):
        date = document.date()
        if date:
            return date.year

    def prepare_defendants(self, document):
        return [defendant.full_name() for defendant in document.defendants.all()]

    def prepare_case_names(self, document):
        return [case.short_name() for case in document.cases.all()]

    def prepare_case_tags(self, document):
        return [case.tag_name for case in document.cases.all()]

    def prepare_evidence_codes(self, document):
        return [str(code) for code in document.evidence_codes.all()]

    def prepare_exhibit_codes(self, document):
        codes = []
        for code in document.exhibit_codes.all():
            if str(code): codes.append(str(code))
        return codes
