from django import template
from django.core.urlresolvers import reverse
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def search_url(query):
    return url_with_query('search:search', query=query)

@register.simple_tag
def url_with_query(url, *args, **kwargs):
    root_url = reverse(url, args=args)
    return '{}?{}'.format(root_url, urlencode(kwargs))
