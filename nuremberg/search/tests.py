from nuremberg.core.tests.acceptance_helpers import *
from nuremberg.search.templatetags.search_url import search_url

def test_search_results():
    query = 'transcript'
    response = client.get(search_url(query))
    page = PyQuery(response.content)

    search_bar = page('input[type="search"]')
    search_bar.should.not_be.empty
    search_bar.val().should.match('transcript')

    page('p').text().should.contain('Results 1-9 of 1,289 for transcript')

    results = page('table tbody tr')
    results.length.should.be(9)

    result = PyQuery(results[0])
    result.find('h3').text().should.contain('Transcripts of conversation between Dr. Grawitz and Dr. Rascher')
    result.find('.date').text().should.match('13 January 1943')
    result.text().should.contain('Language of text: English')
    result.text().should.contain('Defendants: Helmut Poppendick Wolfram Sievers')
