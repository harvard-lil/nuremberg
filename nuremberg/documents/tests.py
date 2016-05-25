from nuremberg.core.tests.acceptance_helpers import *

def test_document_viewer():
    document_id = 350
    response = client.get(url('documents:show', kwargs={'document_id': document_id}))
    page = PyQuery(response.content)

    page('h3').text().should.contain('Affidavit concerning the euthanasia program')

    images = page('img')
    images.length.should.be(3)
    images.attr['src'].should.equal('http://nuremberg.law.harvard.edu/imagedir/HLSL_NMT01/HLSL_NUR_00350001.jpg')

    info = page('.document-info').text()
    info.should.contain('Language of text: English')
    info.should.contain('Source of Text: Case Files/English')
    info.should.contain('HLSL Item No.: 350')
