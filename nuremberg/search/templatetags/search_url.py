from django import template
from django.utils.safestring import SafeString
from django.core.urlresolvers import reverse
from django.http.request import QueryDict
from urllib.parse import quote_plus


register = template.Library()

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
    query += ' '.join(['{}:{}'.format(field, value) for field, value in kwargs.items()])
    return search_url(query)

@register.simple_tag
def url_with_query(url, *args, **kwargs):
    root_url = reverse(url, args=args)
    kwargs = {k: v for k, v in kwargs.items() if v != None}
    return '{}?{}'.format(root_url, encode_query(kwargs))

@register.simple_tag(takes_context=True)
def result_page(context, page):
    params = context['request'].GET.copy()
    params['page'] = page
    if not page:
        del params['page']
    return '?{}'.format(encode_query(params))

@register.simple_tag(takes_context=True)
def add_facet(context, field, value):
    params = context['request'].GET.copy()
    if 'page' in params: del params['page']
    params.update({'f': '{}:{}'.format(field, value)})
    return '?{}'.format(encode_query(params))


@register.simple_tag(takes_context=True)
def sort_results(context, sort):
    params = context['request'].GET.copy()
    params['sort'] = sort
    return '?{}'.format(encode_query(params))

@register.simple_tag(takes_context=True)
def remove_facet(context, facet):
    params = context['request'].GET.copy()
    if 'page' in params: del params['page']
    values = params.getlist('f')
    values.remove(facet)
    params.setlist('f', values)
    return '?{}'.format(encode_query(params))

@register.simple_tag(takes_context=True)
def clear_facets(context):
    params = context['request'].GET.copy()
    if 'page' in params: del params['page']
    params.setlist('f', [])
    return '?{}'.format(encode_query(params))

@register.filter
def trim_snippet(snippet):
    return SafeString(snippet.split('<end of text>', 1)[0])
