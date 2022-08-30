from nuremberg.core.tests.acceptance_helpers import *
from nuremberg.search.templatetags.search_url import url_with_query
from nuremberg.transcripts.models import Transcript, TranscriptPage
from django.core.management import call_command
from datetime import datetime
from os import path

@pytest.fixture
def seq():
    def get_seq(seq=1):
        transcript = Transcript.objects.get(id=1)
        return go_to(url_with_query('transcripts:show', transcript.id, transcript.slug(), seq=seq))
    return get_seq

def test_transcript_viewer(seq):
    page = seq(1)

    assert 'Transcript for NMT 1: Medical Case' in page('h1').text()
    assert 'This is a corrected copy of transcript for 5 December 1946.' in page('p').text()

def test_transcript_search(seq):
    page = go_to(url('transcripts:search', kwargs={'transcript_id':1}))

    search_bar = page('input[type="search"]')
    assert search_bar
    assert search_bar.val() == "*"

    assert not page('mark').text()
    assert page('a').with_text('Page 26')

    page = go_to(search_bar.submit_value('exhibit'))

    search_bar = page('input[type="search"]')
    assert search_bar
    assert search_bar.val() == "exhibit"

    assert "2333 pages with results" in page.text()

    assert "exhibit" in page('mark').text()

    page_link = page('a').with_text('Page 88')
    assert page_link

    page = follow_link(page_link)

    search_bar = page('input[type="search"]')
    assert search_bar
    assert search_bar.val() == "exhibit"

    assert "Page 88" in page.text()


def test_transcript_joins(seq):
    page = seq(1)

    text = page.text()

    assert "HLSL Seq. No. 1" in text

    # There should be four page joins in the first ten pages:

    assert "purely speculative diffi culties.\nHLSL Seq. No. 5" in text
    assert "Wehrmacht, the Medical Service of the SS" in text  # This page break moves to:
    assert "and so forth.\nHLSL Seq. No. 7" in text

    assert "have to look through each individual document" in text
    assert "carry this out in practice.\nHLSL Seq. No. 9" in text

    assert " probably very relevant and important ones.\nHLSL Seq. No. 10" in text

    # it should contain each page number once
    handles = page('.page-handle')
    assert handles.length == 10
    print(handles.outerHtml())
    print([handles.text()])
    assert len(handles.with_text('HLSL SEQ. NO. 1 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 2 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 3 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 4 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 5 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 6 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 7 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 8 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 9 ')) == 1
    assert len(handles.with_text('HLSL SEQ. NO. 10 ')) == 1

    # test not repeating page numbers after
    page = seq(330)
    assert len(page('.page-handle')) == 20
    assert len(page('.page-handle').with_text('HLSL SEQ. NO. 340')) == 1
    text = page('.page-handle').text()
    for i in range(321,341):
        assert "HLSL Seq. No. {}".format(i) in text
    page = seq(150)
    assert len(page('.page-handle').with_text('HLSL SEQ. NO. 160')) == 1

def test_seq_alignment(seq):
    # the first seq load for 40 and 49 should be the same
    page = seq(40)
    assert "Seq. No. 31" in page('.page-handle').nth(0).text()

    page = seq(49)
    assert 'Seq. No. 31' in page('.page-handle').nth(0).text()

    # it begins on a join and should not have the first incomplete sentence from seq 31
    assert 'directly responsible to Hitler himself is the defendant Karl Brandt' not in page.text()

    # the batch previous should end on the same join
    page = seq(25)
    assert "Seq. No. 30" in page('.page-handle').nth(-1).text()
    assert 'The only defendant in the dock who was directly responsible to Hitler himself is the defendant Karl Brandt.' in page.text()

def test_go_to_date(seq):
    page = seq(100)

    assert page('.page-handle').with_text('10 DECEMBER 1946')
    assert page('select option').with_text('10 December 1946').attr('selected')

    date_link = page('select option').with_text('29 January 1947')
    assert date_link
    page = go_to(date_link.submit_value())

    assert page('.page-handle').with_text('29 JANUARY 1947')

def test_go_to_page(seq):
    page = seq(500)
    assert page('.page-handle').with_text('PAGE 482')

    page = go_to(page('form').with_text('Go to page:').find('input[type=number]').submit_value(4820))
    assert page('.page-handle').with_text('PAGE 4,820')

    # test guesstimation: page 5000 is unlabeled
    page = go_to(page('form').with_text('Go to page:').find('input[type=number]').submit_value(5000))
    assert not page('.page-handle').with_text('PAGE 5,000')

    assert page('.page-handle').with_text('PAGE 4,999')
    assert page('.page-handle').with_text('PAGE 5,001')

def test_evidence_links(seq):
    # evidence file number
    page = seq(136)
    page = follow_link(page('a').with_text('NO-417'))

    assert 'Results 1-2 of 2 for * evidence:"NO-417"' in page.text()
    assert 'Organizational chart of the SS Medical Service (from September 1943)' in page.text()

    page = follow_link(page('.document-row').with_text('Transcript for NMT 1: Medical Case').find('a'))
    assert '3 pages with results' in page.text()

def test_exhibit_links(seq):
    # prosecution exhibit number
    page = seq(210)
    page = follow_link(page('a').with_text('61'))

    assert 'Results 1-7 of 7 for * exhibit:"Prosecution 61"' in page.text()
    assert 'Letter to Heinrich Himmler, sending report on high altitude experiments' in page.text()

    page = follow_link(page('.document-row').with_text('Transcript for NMT 1: Medical Case').find('a'))
    assert '1 page with results' in page.text()

    # defense exhibit number
    page = seq(6267)
    page = follow_link(page('a').with_text('8'))

    assert 'Results 1-2 of 2 for * exhibit:"Rose 8"' in page.text()
    assert 'Extract from a report of a conference of consulting specialists, concerning dysentery' in page.text()

    page = follow_link(page('.document-row').with_text('Transcript for NMT 1: Medical Case').find('a'))
    assert '2 pages with results' in page.text()


def test_xml_import():
    abspath = path.dirname(path.abspath(__file__))
    transcript_page = TranscriptPage.objects.get(transcript_id=1, volume_id=1, volume_seq_number=136)
    assert transcript_page.seq_number == 136
    assert transcript_page.date.replace(tzinfo=None) == datetime(1946, 12, 10)
    assert transcript_page.page_number == 121

    # ingest a dummy xml file
    out = call_command('ingest_transcript_xml', path.join(abspath, 'bad/NRMB-NMT01-01_00136_0.xml'))

    transcript_page = TranscriptPage.objects.get(transcript_id=1, volume_id=1, volume_seq_number=136)
    assert transcript_page.seq_number == 99999
    assert transcript_page.date.replace(tzinfo=None) == datetime(1999, 1, 1)
    assert transcript_page.page_number == 99999
    assert 'No text in here' in transcript_page.text()
    assert not transcript_page.extract_evidence_codes()
    assert not transcript_page.extract_exhibit_codes()

    # ingest the correct xml file
    call_command('ingest_transcript_xml', path.join(abspath, 'good/NRMB-NMT01-01_00136_0.xml'))

    transcript_page = TranscriptPage.objects.get(transcript_id=1, volume_id=1, volume_seq_number=136)
    assert transcript_page.seq_number == 136
    assert transcript_page.date.replace(tzinfo=None) == datetime(1946, 12, 10)
    assert transcript_page.page_number == 121
    assert 'The defendants Karl Brandt, Genzken, Gebhardt, Rudolf Brandt' in transcript_page.text()
    assert transcript_page.extract_evidence_codes() == ['NO-416', 'NO-417']
    assert transcript_page.extract_exhibit_codes() == ['Prosecution 22']
