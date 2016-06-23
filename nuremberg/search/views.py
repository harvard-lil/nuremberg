from nuremberg.documents.models import Document
from .lib.digg_paginator import DiggPaginator
from django.shortcuts import render
from haystack.generic_views import SearchView, FacetedSearchView, FacetedSearchMixin
from .forms import DocumentSearchForm
from .lib.solr_grouping_backend import GroupedSearchQuerySet

class Search(FacetedSearchView):
    """
    This is a subclass of the default Haystack faceted search view to implement
    our modifications, including pagination, shorter query parameters, custom
    sorting, and labeled facets.

    You can add a search facet to the list simply by placing it in `facet_labels`.

    See `forms.py` for the faceting and fielded search logic itself.
    """
    load_all = False
    queryset = GroupedSearchQuerySet()

    # page numbers like [1, 2 ... 6, 7, 8, 9, 10, ... 19, 20]
    paginator_class = DiggPaginator
    paginate_by = 15
    context_pages = 4
    edge_pages = 2

    form_class = DocumentSearchForm
    search_field = 'q'
    filter_field = 'f'
    material_field = 'm'
    sort_field = 'sort'
    default_sort = 'relevance'

    facet_labels = (
        ('Material Type', 'material_type'),
        ('Trial', 'case_names'),
        ('Defendant', 'defendants'),
        ('Date', 'date_year'),
        ('Author', 'authors'),
        ('Language', 'language'),
        ('Source', 'source'),
        ('Trial Issues', 'trial_activities'),
    )
    facet_to_label = {field: label for (label, field) in facet_labels}
    facet_fields = [label[1] for label in facet_labels]

    def form_invalid(self, form):
        # override SearchView to give a blank search by default
        # TODO: this seems unnecessary
        self.queryset = form.search()
        context = self.get_context_data(**{
            self.form_name: form,
            'object_list': self.get_queryset()
        })
        return self.render_to_response(context)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'sort_results': self.request.GET.get(self.sort_field, self.default_sort),
            'selected_facets': self.request.GET.getlist(self.filter_field),
            'facet_to_label': self.facet_to_label
        })
        return kwargs

    def get_queryset(self):
        # override FacetedSearchMixin
        qs = super(FacetedSearchMixin, self).get_queryset()
        for field in self.facet_fields:
            sort = 'count'
            qs = qs.facet(field, missing=True, sort=sort, mincount=1)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # pull the query out of form so it is pre-processed
        context['query'] = context['form'].data.get('q')
        if context['facets']:
            labeled_facets = []
            for (label, field) in self.facet_labels:
                counts = context['facets']['fields'].get(field, [])
                # missing ignores mincount and sorting
                if (None, 0) in counts:
                    counts.remove((None, 0))
                else:
                    pass
                    # sort missing into the other facet values
                    # counts.sort(key=lambda field: field[1], reverse=True)
                labeled_facets.append({
                    'field': field,
                    'label': label,
                    'counts': counts
                })
            context.update({'labeled_facets': labeled_facets})
        if context['form']:
            context['facet_lookup'] = {}
            for (field, value, facet) in context['form'].applied_filters:
                context['facet_lookup'][facet] = True
        return context

    def get_paginator(self, *args, **kwargs):
        return self.paginator_class(*args, body=self.context_pages, tail=self.edge_pages, **kwargs)
