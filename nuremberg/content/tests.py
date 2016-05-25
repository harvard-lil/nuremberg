from nuremberg.core.tests.acceptance_helpers import *

def test_landing_page():
    response = client.get('/')
    page = PyQuery(response.content)
    page('h1').text().should.contain('Nuremberg')

    def link_should_exist(name):
        page('a[href="{}"]'.format(url(name))).should.not_be.empty

    link_should_exist('content:approaches')
    link_should_exist('content:trials')
    link_should_exist('content:about')
    link_should_exist('content:history')

    search_form = page('form[action="{}"]'.format(url('search:search')))
    search_form.should.not_be.empty
    search_form.find('input[type="search"]').should.not_be.empty

def test_approaches():
    response = client.get(url('content:approaches'))
    page = PyQuery(response.content)
    page('h1').text().should.contain('Approaches')

    page('h2').text().should.contain('People')
    page('h2').text().should.contain('Issues')
    page('h2').text().should.contain('Documents')
