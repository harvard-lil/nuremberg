from haystack.forms import SearchForm, FacetedSearchForm
from haystack.inputs import AutoQuery, Raw
import re
from collections import deque

class EmptyFacetsSearchForm(SearchForm):
    applied_filters = []
    date_range = [None, None]

    def __init__(self, *args, **kwargs):
        self.facet_to_label = dict(kwargs.pop('facet_to_label'))
        self.selected_facets = kwargs.pop('selected_facets')
        super().__init__(*args, **kwargs)

    def search(self):
        sqs = super().search()
        self.applied_filters = []
        for facet in self.selected_facets:
            if ":" not in facet:
                continue

            field, value = facet.split(":", 1)

            field_label = self.facet_to_label[field]
            if not field_label:
                continue

            self.applied_filters.append((field_label, value, facet))

            if field == 'date_year' and '-' in value:
                self.date_range = value.split('-', 1)
                sqs = sqs.narrow(u'date_year_exact:[%s TO %s]' % (sqs.query.clean(self.date_range[0]), sqs.query.clean(self.date_range[1])))
                # sqs = sqs.filter(date_year__range=self.date_range)
            else:
                if value == 'None':
                    sqs = sqs.narrow(u'-%s_exact:[* TO *]' % (field))
                elif value:
                    sqs = sqs.narrow(u'%s_exact:"%s"' % (field, sqs.query.clean(value)))

        return sqs

class FieldedSearchForm(SearchForm):
    """
    This form enables natural fielded search with the format:
    general search terms field:field search terms -field:excluded field search terms
    """
    auto_query = None
    field_queries = []
    sort_fields = {
        'date-asc': 'date',
        'date-desc': '-date',
        'relevance': 'score',
        'pages': 'total_pages',
        'page': 'seq_number',
    }
    search_fields = {
        'all': 'text',
        'title': 'title',
        'author': 'authors',
        'authors': True,
        'defendant': 'defendants',
        'defendants': True,
        'case': 'case_names',
        'trial': 'case_names',
        'type': 'material_type',
        'date': True,
        'language': True,
        'source': True,
        'evidence': 'evidence_codes',
        'exhibit': 'exhibit_codes',
    }
    material_types = ('documents', 'transcripts', 'photographs')

    def __init__(self, *args, **kwargs):
        self.sort_results = kwargs.pop('sort_results')
        self.transcript_id = kwargs.pop('transcript_id', None)

        super().__init__(*args, **kwargs)
        if 'm' in self.data:
            included = self.data.getlist('m')
            self.data = self.data.copy()
            if len(included) < 3:
                self.data['q'] += ' type:{}'.format(', '.join(included))

    def search(self):
        sqs = self.searchqueryset \
        .order_by(self.sort_fields.get(self.sort_results, 'score'))

        if self.transcript_id:
            # we use snippets to count "occurrences" of a match in transcript search results
            sqs = sqs.filter(material_type='Transcript', transcript_id=self.transcript_id) \
            .highlight(**{'hl.snippets': 10, 'hl.fragsize':150, 'hl.fl':'text', 'hl.requireFieldMatch':'true', 'hl.simple.pre':'<mark>', 'hl.simple.post':'</mark>'})
        else:
            sqs = sqs.group_by('grouping_key') \
            .highlight(**{'hl.snippets': 1, 'hl.fragsize':150, 'hl.fl':'text', 'hl.requireFieldMatch':'true', 'hl.simple.pre':'<mark>', 'hl.simple.post':'</mark>'})

        if not self.is_valid() or not 'q' in self.cleaned_data:
            return sqs

        (self.auto_query, self.field_queries) = self.parse_query(self.cleaned_data['q'])

        if self.auto_query:
            sqs = sqs.filter(content=AutoQuery(self.auto_query))

        for field_query in self.field_queries:
            (field, value) = field_query

            if field[0] == '-':
                exclude = True
                field = field[1:]
            else:
                exclude = False

            field_key = self.search_fields.get(field)
            if field_key == True:
                field_key = field

            if field_key:
                # the solr backend aggressively quotes OR queries, so we must build it manually
                values = re.split(r'[|,]| OR ', value)
                query_list = []
                for value in values:
                    if re.match(r'^\s*(none|unknown)\s*$', value, re.IGNORECASE):
                        query_list.append('(-{}: [* TO *] AND *:*)'.format(field_key))
                    else:
                        # NOTE: field_key is whitelisted above
                        query_list.append('{}:({})'.format(field_key, AutoQuery(value).prepare(sqs.query)))
                raw_query = '({})'.format(' OR '.join(query_list))
                if exclude:
                    field_query.append('excluded')
                    raw_query = 'NOT {}'.format(raw_query)
                else:
                    field_query.append('included')
                sqs = sqs.raw_search(raw_query)
            else:
                field_query.append('ignored')

        if self.load_all:
            sqs = sqs.load_all()

        return sqs

    def parse_query(self, full_query):
        sections = deque(re.split('(\-?\w+)\:', full_query))
        auto_query = sections.popleft()
        field_queries = []
        while len(sections) >= 2:
            field_queries.append([sections.popleft(), sections.popleft()])
        return (auto_query, field_queries)

class DocumentSearchForm(EmptyFacetsSearchForm, FieldedSearchForm):
    pass
