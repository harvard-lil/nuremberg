from nuremberg.tests.acceptance_helpers import *

def test_transcript_viewer():
    transcript_id = 350
    response = client.get(url('transcripts:show', kwargs={'transcript_id': transcript_id}))
    page = PyQuery(response.content)

    page('h3').text().should.contain('(USA v. Karl Brandt et al. 1946-47)')

    page('p').text().should.contain('THE SECRETARY GENERAL: All of the defendants are present and accounted for.')
