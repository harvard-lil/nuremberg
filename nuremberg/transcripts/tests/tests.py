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

    page('h3').text().should.contain('Case transcript for NMT 1: Medical Case')
    page('p').text().should.contain('This is a corrected copy of transcript for 5 December 1946.')

def test_transcript_search(seq):
    page = go_to(url('transcripts:search', kwargs={'transcript_id':1}))

    search_bar = page('input[type="search"]')
    search_bar.should.not_be.empty
    search_bar.val().should.be.none

    page('mark').text().should.be.empty
    page('a').with_text('Page 26').should.not_be.empty

    page = go_to(search_bar.submit_value('exhibit'))

    search_bar = page('input[type="search"]')
    search_bar.should.not_be.empty
    search_bar.val().should.equal('exhibit')

    page.text().should.contain('2333 pages with results')

    page('mark').text().should.contain('exhibit')

    page_link = page('a').with_text('Page 88')
    page_link.should.not_be.empty

    page = follow_link(page_link)

    search_bar = page('input[type="search"]')
    search_bar.should.not_be.empty
    search_bar.val().should.equal('exhibit')

    page.text().should.contain('Page 88')


def test_transcript_joins(seq):
    page = seq(1)

    text = page.text()

    text.should.contain('HLSL Seq. No. 1')

    # There should be four page joins in the first ten pages:

    text.should.contain('purely speculative diffi culties. HLSL Seq. No. 5') # This page break moves to:

    text.should.contain('Wehrmacht, the Medical Service of the SS') # This page break moves to:
    text.should.contain('and so forth. HLSL Seq. No. 7')

    text.should.contain('have to look through each individual document') # This page break moves to:
    text.should.contain('carry this out in practice. HLSL Seq. No. 9')

    text.should.contain(' probably very relevant and important ones. HLSL Seq. No. 10')

    # it should contain each page number once
    handles = page('.page-handle')
    handles.length.should.equal(10)
    print(handles.outerHtml())
    print([handles.text()])
    handles.with_text('HLSL SEQ. NO. 1 ').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 2\n').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 3\n').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 4\n').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 5\n').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 6\n').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 7\n').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 8\n').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 9\n').length.should.equal(1)
    handles.with_text('HLSL SEQ. NO. 10\n').length.should.equal(1)

    # test not repeating page numbers after
    page = seq(330)
    page('.page-handle').length.should.equal(20)
    page('.page-handle').with_text('HLSL SEQ. NO. 340').length.should.equal(1)
    text = page('.page-handle').text()
    for i in range(321,341):
        text.should.contain('HLSL Seq. No. {}\n'.format(i))
    page = seq(150)
    page('.page-handle').with_text('HLSL SEQ. NO. 160').length.should.equal(1)

def test_seq_alignment(seq):
    # the first seq load for 40 and 49 should be the same
    page = seq(40)
    page('.page-handle').nth(0).text().should.contain('Seq. No. 31')

    page = seq(49)
    page('.page-handle').nth(0).text().should.contain('Seq. No. 31')

    # it begins on a join and should not have the first incomplete sentence from seq 31
    page.text().should_not.contain('directly responsible to Hitler himself is the defendant Karl Brandt')

    # the batch previous should end on the same join
    page = seq(25)
    page('.page-handle').nth(-1).text().should.contain('Seq. No. 30')
    page.text().should.contain('The only defendant in the dock who was directly responsible to Hitler himself is the defendant Karl Brandt.')

def test_go_to_date(seq):
    page = seq(100)

    page('.page-handle').with_text('10 DECEMBER 1946').should.not_be.empty
    page('select option').with_text('10 December 1946').attr('selected').should.be.true

    date_link = page('select option').with_text('29 January 1947')
    date_link.should.not_be.empty
    page = go_to(date_link.submit_value())

    page('.page-handle').with_text('29 JANUARY 1947').should.not_be.empty

def test_go_to_page(seq):
    page = seq(500)
    page('.page-handle').with_text('PAGE 482').should.not_be.empty

    page = go_to(page('form').with_text('Go to page:').find('input[type=number]').submit_value(4820))
    page('.page-handle').with_text('PAGE 4,820').should.not_be.empty

    # test guesstimation: page 5000 is unlabeled
    page = go_to(page('form').with_text('Go to page:').find('input[type=number]').submit_value(5000))
    page('.page-handle').with_text('PAGE 5,000').should.be.empty

    page('.page-handle').with_text('PAGE 4,999').should.not_be.empty
    page('.page-handle').with_text('PAGE 5,001').should.not_be.empty

def test_evidence_links(seq):
    # evidence file number
    page = seq(136)
    page = follow_link(page('a').with_text('NO-417'))

    page.text().should.contain('Results 1-4 of 4 for * evidence: (NO-417)')
    page.text().should.contain('Organizational chart of the SS Medical Service (from September 1943)')

    page = follow_link(page('.document-row').with_text('Case transcript for NMT 1: Medical Case').find('a'))
    page.text().should.contain('3 pages with results')

def test_exhibit_links(seq):
    # prosecution exhibit number
    page = seq(210)
    page = follow_link(page('a').with_text('61'))

    page.text().should.contain('Results 1-5 of 5 for * exhibit: (Prosecution 61)')
    page.text().should.contain('Letter to Heinrich Himmler, sending report on high altitude experiments')

    page = follow_link(page('.document-row').with_text('Case transcript for NMT 1: Medical Case').find('a'))
    page.text().should.contain('1 page with results')

    # defense exhibit number
    page = seq(6267)
    page = follow_link(page('a').with_text('8'))

    page.text().should.contain('Results 1-2 of 2 for * exhibit: (Rose 8)')
    page.text().should.contain('Extract from a report of a conference of consulting specialists, concerning dysentery')

    page = follow_link(page('.document-row').with_text('Case transcript for NMT 1: Medical Case').find('a'))
    page.text().should.contain('2 pages with results')


def test_xml_import():
    abspath = path.dirname(path.abspath(__file__))
    transcript_page = TranscriptPage.objects.get(transcript_id=1, volume_id=1, volume_seq_number=136)
    transcript_page.seq_number.should.equal(136)
    transcript_page.date.should.equal(datetime(1946, 12, 10))
    transcript_page.page_number.should.equal(121)

    # ingest a dummy xml file
    out = call_command('ingest_transcript_xml', path.join(abspath, 'bad/NRMB-NMT01-01_00136_0.xml'))

    transcript_page = TranscriptPage.objects.get(transcript_id=1, volume_id=1, volume_seq_number=136)
    transcript_page.seq_number.should.equal(99999)
    transcript_page.date.should.equal(datetime(1999, 1, 1))
    transcript_page.page_number.should.equal(99999)
    transcript_page.text().should.contain('No text in here')
    transcript_page.extract_evidence_codes().should.be.empty
    transcript_page.extract_exhibit_codes().should.be.empty

    # ingest the correct xml file
    call_command('ingest_transcript_xml', path.join(abspath, 'good/NRMB-NMT01-01_00136_0.xml'))

    transcript_page = TranscriptPage.objects.get(transcript_id=1, volume_id=1, volume_seq_number=136)
    transcript_page.seq_number.should.equal(136)
    transcript_page.date.should.equal(datetime(1946, 12, 10))
    transcript_page.page_number.should.equal(121)
    transcript_page.text().should.contain('The defendants Karl Brandt, Genzken, Gebhardt, Rudolf Brandt')
    transcript_page.extract_evidence_codes().should.equal(['NO-416', 'NO-417'])
    transcript_page.extract_exhibit_codes().should.equal(['Prosecution 22'])
