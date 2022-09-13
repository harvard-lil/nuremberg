from haystack import indexes
from nuremberg.photographs.models import Photograph

class PhotographId(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    highlight = indexes.CharField(model_attr='description')
    material_type = indexes.CharField(default='Photograph', faceted=True)
    grouping_key = indexes.FacetCharField(facet_for='grouping_key') # not really a facet, just an exact key

    slug = indexes.CharField(model_attr='slug', indexed=False)
    title = indexes.CharField(model_attr='title')
    literal_title = indexes.CharField(model_attr='description', null=True)

    thumb_url = indexes.CharField(model_attr='thumb_url', indexed=False, null=True)

    date = indexes.CharField(model_attr='year_taken', faceted=True, null=True)
    date_sort = indexes.DateTimeField(model_attr='date', null=True)
    date_year = indexes.CharField(model_attr='date_year', faceted=True, null=True)
    source = indexes.CharField(default='Photographic Archive', faceted=True, null=True)

    total_pages = indexes.IntegerField(default=1, null=True)

    def get_model(self):
        return Photograph

    def prepare_grouping_key(self, photo):
        # This is a hack to group transcripts but not documents in a single query.
        # Transcripts get a group key, documents get a unique key.
        # This can be changed to make grouping work on volume or something else.
        return 'Photograph_{}'.format(photo.id)
