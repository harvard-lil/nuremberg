from haystack import indexes
from nuremberg.documents.models import Document
from nuremberg.transcripts.models import TranscriptPage

class TranscriptPageIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    highlight = indexes.CharField(model_attr='text')
    material_type = indexes.CharField(default='Transcript', faceted=True)
    grouping_key = indexes.FacetField(facet_for='grouping_key') # not really a facet, just an exact key

    slug = indexes.CharField(model_attr='transcript__slug', indexed=False)
    transcript_id = indexes.CharField(model_attr='transcript__id')
    title = indexes.CharField(model_attr='transcript__title')

    total_pages = indexes.IntegerField(model_attr='transcript__total_pages', default=0, null=True)
    language = indexes.CharField(default='English', faceted=True)
    source = indexes.CharField(default='Trial Transcript', faceted=True)

    seq_number = indexes.IntegerField(model_attr='seq_number')
    volume_number = indexes.CharField(model_attr='volume__volume_number')
    volume_seq_number = indexes.CharField(model_attr='volume_seq_number')
    page_label = indexes.CharField(model_attr='page_label', null=True)

    date = indexes.CharField(faceted=True, null=True)
    date_year = indexes.CharField(faceted=True, null=True)
    date_sort = indexes.DateTimeField(model_attr='date', null=True)

    authors = indexes.MultiValueField(faceted=True, null=True)
    defendants = indexes.MultiValueField(faceted=True, null=True)
    case_names = indexes.MultiValueField(model_attr='transcript__case__short_name', faceted=True)
    case_tags = indexes.MultiValueField(model_attr='transcript__case__tag_name', faceted=True)

    evidence_codes = indexes.MultiValueField(null=True)
    exhibit_codes = indexes.MultiValueField(null=True)

    trial_activities = indexes.MultiValueField(faceted=True, null=True)

    def get_model(self):
        return TranscriptPage

    def get_updated_field(self):
        return 'updated_at'

    def prepare_grouping_key(self, page):
        # This is a hack to group transcripts but not pages in a single query.
        # Transcripts get a group key, pages get a unique key.
        # This can be changed to make grouping work on volume or something else.
        return 'Transcript_{}'.format(page.transcript.id)

    def prepare_date(self, page):
        if page.date:
            return page.date.strftime('%d %B %Y')

    def prepare_date_year(self, page):
        if page.date:
            return page.date.year

    def prepare_defendants(self, page):
        return [defendant.full_name() for defendant in page.transcript.case.defendants.all()]

    def prepare_authors(self, page):
        # TODO
        return []

    def prepare_evidence_codes(self, page):
        return page.extract_evidence_codes()

    def prepare_exhibit_codes(self, page):
        return page.extract_exhibit_codes()

    def prepare_trial_activities(self, page):
        return [activity.short_name for activity in page.transcript.case.activities.all()]
