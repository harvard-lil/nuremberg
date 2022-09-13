from nuremberg.core.tests.acceptance_helpers import *

def document(document_id):
    response = client.get(url('documents:show', kwargs={'document_id': document_id}))
    return PyQuery(response.content)

def test_document_1():
    page = document(1)

    assert 'List of Case 1 files, prosecution and defense, in English' in page('h1').text()

    images = page('.document-image')
    assert len(images) == 20
    assert 'HLSL_NUR_00001001.jpg' in images.attr['data-screen-url']

    select = page('.page-buttons select')
    len(select.find('option')) == 20
    assert 'Sequence No. 20' in select.text()

    info = page('.document-info').text()
    assert "NMT 1" in info
    assert 'Date Unknown' in info
    assert 'Total Pages: 20' in info
    assert 'Language of Text: English' in info
    assert 'Source of Text: Case Files/English' in info
    assert 'HLSL Item No.: 1' in info


def test_document_2():
    page = document(2)

    assert 'Argument: prosecution closing argument against all defendants' in page('h1').text()

    images = page('.document-image')
    assert len(images) == 78
    assert 'HLSL_NUR_00002001.jpg' in images.attr['data-screen-url']

    assert "Missing Image No. 13" in page.text()

    info = page('.document-info').text()
    assert 'NMT 1' in info
    assert '14 July 1947' in info
    assert 'Total Pages: 78' in info
    assert 'Language of Text: English' in info
    assert 'Source of Text: Case Files/English' in info
    assert 'HLSL Item No.: 2' in info

def test_document_400():
    page = document(400)

    assert 'Decree concerning the administration of Polish territories' in page('h1').text()

    images = page('.document-image')
    assert len(images) == 3
    assert 'HLSL_NUR_00400001.jpg' in images.attr['data-screen-url']

    info = page('.document-info').text()
    assert 'NMT 1' in info
    assert '24 October 1939' in info
    assert 'Defendants\nKarl Gebhardt' in info
    assert 'Authors\nAdolf Hitler' in info
    assert 'Total Pages: 3' in info
    assert 'Language of Text: English' in info
    assert 'Source of Text: Case Files/English' in info
    assert 'HLSL Item No.: 400' in info
    assert 'Trial Issue\nSulfanilamide experiments' in info


def test_document_3799():
    page = document(3799)

    assert 'Journal and office records of Hans Frank, Governor General of Poland, 1939-1944' in page('h1').text()

    images = page('.document-image img')
    assert len(images) == 492
    assert 'HLSL_NUR_03799492.jpg' in PyQuery(images[491]).attr['src']

    info = page('.document-info').text()
    assert 'NMT 1' not in info
    assert '02 December 1939' in info
    assert 'Author\nHans Frank' in info
    assert 'Total Pages: 492' in info
    assert 'Language of Text: German' in info
    assert 'Source of Text: Photostat' in info
    assert 'HLSL Item No.: 3799' in info
