from nuremberg.core.tests.acceptance_helpers import *

def test_landing_page():
    response = client.get('/')
    page = PyQuery(response.content)
    page('h1').text().should.contain('Nuremberg')

    def link_should_exist(name):
        page('a[href="{}"]'.format(url(name))).should.not_be.empty

    link_should_exist('content:trials')
    link_should_exist('content:about')

    search_form = page('form[action="{}"]'.format(url('search:search')))
    search_form.should.not_be.empty
    search_form.find('input[type="search"]').should.not_be.empty
