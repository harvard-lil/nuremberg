import pytest
pytestmark = pytest.mark.django_db

import re
import pyquery
from lxml.html import FormElement
from django.test import Client
from django.urls import reverse as url
from django.http import QueryDict
from urllib.parse import urlencode, urlparse

def go_to(url, expected_status=200, follow_redirects=True):
    response = client.get(url, follow=follow_redirects)
    assert response.status_code == expected_status, \
        "Got status code {} for URL (expected {}): {}".format(response.status_code, expected_status, url)
    page = PyQuery(response.content)
    page.pathname = response.request['PATH_INFO']
    page.querystring = response.request['QUERY_STRING']
    return page

def follow_link(element):
    a_tag = element.closest('a')
    assert len(a_tag) >= 1, \
        "Can't find any A tag enclosing element: {}".format(element.outerHtml() or '[empty selection]')
    href = element.attr('href')
    assert href, \
        "Element has no `href` attribute: {}.".format(a_tag.outerHtml() or '[empty selection]')
    return go_to(a_tag.absolute_url(href))

class PyQuery(pyquery.PyQuery):
    """
    Simple PyQuery subclass that can "follow" links correctly.
    """
    pathname = None
    querystring = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'parent' in kwargs:
            self.pathname = kwargs['parent'].pathname
            self.querystring = kwargs['parent'].querystring

    def with_text(self, text):
        """
        Filter the selection to elements containing `text`.
        """
        return self.filter(lambda n, el: text.lower() in PyQuery(el).text().lower())

    def with_regex(self, rx):
        """
        Filter the selection to elements containing `text`.
        """
        return self.filter(lambda n, el: re.search(rx, PyQuery(el).text()))

    def absolute_url(self, url):
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            if not parsed_url.path or not parsed_url.path.startswith('/'):
                url = self.pathname + url
        return url

    def submit_url(self, params={}, defaults=True):
        """
        Return a form submit url with the given params.
        """
        action = self.attr('action')
        values = QueryDict('', mutable=True)
        if defaults:
            for el in self.find('input'):
                if el.get('type') in ('checkbox', 'radio'):
                    if el.get('checked'):
                        values.appendlist(el.name, el.value or '')
                else:
                    values.appendlist(el.name, el.value or '')
        #overwrite the querydict
        if isinstance(params, QueryDict):
            values.update(params)
        else:
            for key, val in params.items():
                if val is None:
                    del values[key]
                else:
                    values[key] = val
        return self.absolute_url(action or '') + '?' + values.urlencode()

    def submit_value(self, val=None):
        """
        Return a url like typing into this input and pressing return.
        """
        name = self.attr('name')
        if len(self) and self[0].tag == 'option':
            name = self.closest('select').attr('name')
        assert name, \
            "Element has no `name` attribute: {}.".format(self.outerHtml() or '[empty selection]')
        return self.closest('form').submit_url({name: val or self.val()})

    def nth(self, n):
        return PyQuery(self[n])

client = Client()
