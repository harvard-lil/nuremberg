from django import template
from django.utils.safestring import SafeString
from django.core.urlresolvers import reverse
from django.http.request import QueryDict
from urllib.parse import quote_plus


register = template.Library()

def cleaned_params(context):
    params = context['request'].GET.copy()
    if 'partial' in params: del params['partial']
    return params

@register.simple_tag
def encode_string(string):
    return quote_plus(string, ':')

def encode_query(querydict):
    """
    Encode a querydict as form params, using '+'' for ' '.
    """
    if not isinstance(querydict, QueryDict):
        temp = querydict
        querydict = QueryDict('', mutable=True)
        querydict.update(temp)
    return querydict.urlencode(': ').replace(' ', '+')

@register.simple_tag
def search_url(query):
    return url_with_query('search:search', q=query)

@register.simple_tag
def search_query(*args, **kwargs):
    query = ' '.join(args)
    query += ' '.join(['{}:({})'.format(field, value) for field, value in kwargs.items()])
    return search_url(query)

@register.simple_tag
def url_with_query(url, *args, **kwargs):
    root_url = reverse(url, args=args)
    kwargs = {k: v for k, v in kwargs.items() if v != None}
    return '{}?{}'.format(root_url, encode_query(kwargs))

@register.simple_tag(takes_context=True)
def result_page(context, page):
    params = cleaned_params(context)
    params['page'] = page
    if not page: del params['page']
    return '?{}'.format(encode_query(params))

@register.simple_tag(takes_context=True)
def add_facet(context, field, value):
    params = cleaned_params(context)
    if 'page' in params: del params['page']
    facet = '{}:{}'.format(field, value)
    if field.startswith('date_year'):
        if 'year_min' in params: del params['year_min']
        if 'year_max' in params: del params['year_max']
    if not facet in params.getlist('f'):
        params.update({'f': '{}:{}'.format(field, value)})
    return '?{}'.format(encode_query(params))

@register.simple_tag(takes_context=True)
def facet_exists(context, field, value):
    facet_lookup = context['facet_lookup']
    facet = '{}:{}'.format(field, value)
    return facet_lookup.get(facet) and facet


@register.simple_tag(takes_context=True)
def sort_results(context, sort):
    params = cleaned_params(context)
    params['sort'] = sort
    return '?{}'.format(encode_query(params))

@register.simple_tag(takes_context=True)
def remove_facet(context, facet):
    params = cleaned_params(context)
    if 'page' in params: del params['page']
    values = params.getlist('f')
    if facet in values:
        values.remove(facet)
    if facet.startswith('date_year'):
        if 'year_min' in params: del params['year_min']
        if 'year_max' in params: del params['year_max']
    params.setlist('f', values)
    return '?{}'.format(encode_query(params))

@register.simple_tag(takes_context=True)
def clear_facets(context):
    params = cleaned_params(context)
    if 'page' in params: del params['page']
    params.setlist('f', [])
    params.setlist('year_min', [])
    params.setlist('year_max', [])
    return '?{}'.format(encode_query(params))

@register.simple_tag
def group_merge(results, key):
    values = set()
    for result in results: values.update(getattr(result, key, None) or [])
    return list(values)

@register.filter
def trim_snippet(snippet):
    return SafeString(snippet.split('<end of text>', 1)[0])
