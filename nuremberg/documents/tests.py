from nuremberg.core.tests.acceptance_helpers import *

def document(document_id):
    response = client.get(url('documents:show', kwargs={'document_id': document_id}))
    return PyQuery(response.content)

def test_document_1():
    page = document(1)

    page('h3').text().should.contain('List of Case 1 documents, prosecution and defense, in English.')

    images = page('.document-image')
    images.length.should.be(20)
    images.attr['data-screen-url'].should.contain('HLSL_NUR_00001001.jpg')

    select = page('.page-buttons select')
    select.find('option').length.should.be(20)
    select.text().should.contain('Sequence No. 20')

    info = page('.document-info').text()
    info.should.contain('NMT 1')
    info.should.contain('Date Unknown')
    info.should.contain('Total Pages: 20')
    info.should.contain('Language of Text: English')
    info.should.contain('Source of Text: Case Files/English')
    info.should.contain('HLSL Item No.: 1')


def test_document_2():
    page = document(2)

    page('h3').text().should.contain('Argument: prosecution closing argument against all defendants')

    images = page('.document-image')
    images.length.should.be(78)
    images.attr['data-screen-url'].should.contain('HLSL_NUR_00002001.jpg')

    page.text().should.contain("Missing Image No. 13")

    info = page('.document-info').text()
    info.should.contain('NMT 1')
    info.should.contain('14 July 1947')
    info.should.contain('Total Pages: 78')
    info.should.contain('Language of Text: English')
    info.should.contain('Source of Text: Case Files/English')
    info.should.contain('HLSL Item No.: 2')

def test_document_400():
    page = document(400)

    page('h3').text().should.contain('Decree concerning the administration of Polish territories')

    images = page('.document-image')
    images.length.should.be(3)
    images.attr['data-screen-url'].should.contain('HLSL_NUR_00400001.jpg')

    info = page('.document-info').text()
    info.should.contain('NMT 1')
    info.should.contain('24 October 1939')
    info.should.contain('Defendants Karl Gebhardt')
    info.should.contain('Authors Adolf Hitler')
    info.should.contain('Total Pages: 3')
    info.should.contain('Language of Text: English')
    info.should.contain('Source of Text: Case Files/English')
    info.should.contain('HLSL Item No.: 400')
    info.should.contain('Trial Activities Sulfanilamide experiments')


def test_document_3799():
    page = document(3799)

    page('h3').text().should.contain('Journal and office records of Hans Frank, Governor General of Poland, 1939-1944')

    images = page('.document-image img')
    images.length.should.equal(492)
    PyQuery(images[491]).attr['src'].should.contain('HLSL_NUR_03799492.jpg')

    info = page('.document-info').text()
    info.should_not.contain('NMT 1')
    info.should.contain('02 December 1939')
    info.should.contain('Author Hans Frank')
    info.should.contain('Total Pages: 492')
    info.should.contain('Language of Text: German')
    info.should.contain('Source of Text: Photostat')
    info.should.contain('HLSL Item No.: 3799')
    info.should_not.contain('Trial Activities')
