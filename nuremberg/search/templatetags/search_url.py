from django import template
from django.core.urlresolvers import reverse
from django.http import QueryDict

register = template.Library()

@register.simple_tag
def search_url(query):
    root_url = reverse('search:search')
    query_dict = QueryDict(mutable=True)
    query_dict['query'] = query
    return '{}?{}'.format(root_url, query_dict.urlencode())
