from nuremberg.tests.acceptance_helpers import *
from nuremberg.search.templatetags.search_url import url_with_query

def test_transcript_viewer():
    transcript_id = 350
    response = client.get(url('transcripts:show', kwargs={'transcript_id': transcript_id}))
    page = PyQuery(response.content)

    page('h3').text().should.contain('(USA v. Karl Brandt et al. 1946-47)')

    page('p').text().should.contain('THE SECRETARY GENERAL: All of the defendants are present and accounted for.')

def test_transcript_search():
    query = 'transcript'
    response = client.get(url_with_query('transcripts:search', 300, query=query))
    page = PyQuery(response.content)

    search_bar = page('input[type="search"]')
    search_bar.should.not_be.empty
    search_bar.val().should.match('transcript')

    page('label').text().should.contain('3 results')

    results = page('.result-row')
    results.length.should.be(3)

    page('mark').text().should.contain('Rudolf Brandt')
