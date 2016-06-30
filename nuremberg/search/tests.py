from nuremberg.core.tests.acceptance_helpers import *
from nuremberg.search.templatetags.search_url import search_url

@pytest.fixture
def query():
    def get_query(query=''):
        return go_to(search_url(query))
    return get_query

def test_search_page(query):
    page = query('')

    search_bar = page('input[type="search"]')
    search_bar.should.not_be.empty
    search_bar.val().should.equal('*')

    page('p').text().should.contain('Results 1-15 of 6065 for *')
    page('.facet').text().should.contain('Document (5842)')

    page = follow_link(page('.facet p').with_text('Transcript').find('a'))

    page('p').text().should.contain('Results 1-4 of 4 for *')
    page('.facet').text().should_not.contain('Document')
    filter_link = page('.applied-filters').with_text('Material Type Transcript').find('a')
    filter_link.should.not_be.empty

    page = follow_link(filter_link)

def test_facets(query):
    page = query('polish workers in germany')

    # baseline
    page.text().should.contain('Results 1-15 of 22 for polish workers in germany')

    # test adding facet
    page = follow_link(page('.facet p').with_text('NMT 2').find('a'))
    page.text().should.contain('Results 1-8 of 8 for polish workers in germany')
    page('.applied-filters').with_text('Trial').text().should.contain('NMT 2')

    # test removing facet
    page = follow_link(page('.applied-filters').with_text('Trial NMT 2').find('a'))
    page.text().should.contain('Results 1-15 of 22 for polish workers in germany')

    # test unknown facet
    page = follow_link(page('.facet').with_text('Trial').find('p').with_text('Unknown').find('a'))
    page.text().should.contain('Results 1-12 of 12 for polish workers in germany')
    page('.applied-filters').with_text('Trial').text().should.contain('None')

    # test multiple facets
    page = follow_link(page('.facet').with_text('Language').find('p').with_text('English').find('a'))
    page.text().should.contain('Results 1-7 of 7 for polish workers in germany')
    page('.applied-filters').with_text('Trial').text().should.contain('None')
    page('.applied-filters').with_text('Language').text().should.contain('English')

    page = follow_link(page('.facet').with_text('Source').find('p').with_text('Typescript').find('a'))
    page.text().should.contain('Results 1-4 of 4 for polish workers in germany')
    page('.applied-filters').with_text('Trial').text().should.contain('None')
    page('.applied-filters').with_text('Language').text().should.contain('English')
    page('.applied-filters').with_text('Source').text().should.contain('Typescript')

    # test date range
    date_range = page('.facet').with_text('Date').find('form')
    from_name = date_range.find('input[type=number]').nth(0).attr('name')
    to_name = date_range.find('input[type=number]').nth(1).attr('name')
    page = go_to(date_range.submit_url({from_name: 1941, to_name: 1942}))
    page.text().should.contain('Results 1-2 of 2 for polish workers in germany')
    page('.applied-filters').with_text('Trial').text().should.contain('None')
    page('.applied-filters').with_text('Language').text().should.contain('English')
    page('.applied-filters').with_text('Source').text().should.contain('Typescript')
    page('.applied-filters').with_text('Date').text().should.contain('1941-1942')
    page('.document-row').text().should.contain('1941')
    page('.document-row').text().should.contain('1942')

    # test removing all filters
    page = follow_link(page('a').with_text('Clear all filters'))
    page.text().should.contain('Results 1-15 of 22 for polish workers in germany')

def test_keyword_search(query):
    page = query('')
    search_bar = page('input[type="search"]')
    page = go_to(search_bar.submit_value('experiments'))

    page('p').text().should.contain('Results 1-15 of 1495 for experiments')
    page('.document-row').length.should.equal(15)

    page = follow_link(page('.facet').with_text('Material Type').find('p').with_text('Transcript').find('a'))
    transcript_row = page('.document-row').with_text('Case transcript for NMT 1: Medical Case')
    transcript_row.should.not_be.empty
    transcript_row.text().should.contain('05 December 1946')

    page = follow_link(transcript_row.find('a'))
    page.text().should.contain('5680 pages with results')
    page('p').text().should.contain('We will than proceed to the next experiment')

    page = follow_link(page('a').with_text('Page 32'))
    page.text().should.contain('HLSL Seq. No. 8')

@pytest.fixture
def count_results(query):
    def _count(q, count, page_count=None, first_count=None):
        page = query(q)
        if page_count == None: page_count = 15
        if first_count == None: first_count = 1
        page('.results-count').text().should.contain('Results {}-{} of {} for {}'.format(first_count, page_count, count, q.replace(':', ': ')))
    return _count

def test_field_search(count_results):

    # TODO: these tests are pretty brittle to indexing changes, consider beefing them up
    count_results('workers', 603)
    count_results('workers author:fritz', 78)
    count_results('workers date:january', 32)
    count_results('workers -trial:(nmt 4)', 487)
    count_results('workers evidence:NO-190', 5, 5)
    count_results('workers source:typescript language:german', 37)
    count_results('workers source:typescript language:german -author:Milch', 28)
    count_results('workers trial:(nmt 2 | nmt 4)', 262)
    count_results('workers date:unknown', 37)
    count_results('workers date:none', 37)
    count_results('workers -date:none', 569)
    count_results('workers -date:none notafield:(no matches)', 569)
    count_results('workers trial:(nmt 2 | nmt 4) author:speer|fritz', 37)
    count_results('workers author:"hitler adolf"', 0, 0, 0)
    count_results('workers author:"adolf hitler"', 11, 11)
    count_results('workers exhibit:prosecution', 159)
    count_results('* author:hitler -author:adolf', 0, 0, 0)
    count_results('* exhibit:handloser', 81)
    count_results('malaria', 98)
    count_results('freezing', 281)
    count_results('malaria freezing', 33)
    count_results('-malaria freezing', 250)
    count_results('malaria -freezing', 67)
    count_results('malaria | freezing', 344)

def test_document_search(query):
    page = query('workers')
    page.text().should.contain('Results 1-15 of 603 for workers')
    page = follow_link(page('.document-row a'))

    search_bar = page('input[type=search]')
    search_bar.should.not_be.empty
    search_bar.val().should.equal('workers')

    page = go_to(search_bar.submit_value('instructions'))
    page.text().should.contain('Results 1-15 of 323 for instructions')
    page = follow_link(page('.document-row a'))

    search_bar = page('input[type=search]')
    search_bar.should.not_be.empty
    search_bar.val().should.equal('instructions')

    page = follow_link(page('a').with_text('Back to search results'))
    page.text().should.contain('Results 1-15 of 323 for instructions')

def test_landing_search(query):
    page = go_to(url('content:landing'))

    search_bar = page('input[type=search]')
    search_bar.should.not_be.empty

    page = go_to(search_bar.submit_value('workers'))
    page.text().should.contain('Results 1-15 of 603 for workers')

    page = go_to(url('content:landing'))

    # uncheck Documents
    search_bar = page('input[type=search]')
    form = search_bar.closest('form')
    values = QueryDict('', mutable=True)
    values[search_bar.attr('name')] = 'workers'
    values.setlist(form.find('label').with_text('Documents').find('input').attr('name'),
        ['transcripts', 'photographs'])
    page = go_to(form.submit_url(values, defaults=False))

    page.text().should.contain('Results 1-6 of 6 for workers type: transcripts|photographs')

def test_transcript_snippets(query):
    page = query('documents type:transcript')

    page.text().should.contain('Results 1-4 of 4 for documents type: transcript')
    page.text().should.contain('4039 results in this transcript')

    # snippets on several pages
    page.text().should.contain('... p. 26')
    page.text().should.contain('... p. 28')
    page.text().should.contain('... p. 30')

    # test single page results
    page = query('documents hlsl:2')

    page.text().should.contain('Results 1-1 of 1 for documents hlsl: 2')
    page.text().should.contain('1 result in this transcript')

    # all snippets from first page
    page.text().should.contain('[ ... p. 26 ] can work on it')
    page.text().should.contain('[ ... p. 26 ] possible with these few documents')
    page.text().should.contain('[ ... p. 26 ] able to select which documents')

    # test no snippets
    page = query('type:transcript')

    # text from several pages
    page.text().should.contain('... p. unlabeled')
    page.text().should.contain('... p. 26')
    page.text().should.contain('... p. 27')

    # test single page no snippets
    page = query('type:transcript')

    # one snippet
    page.text().should.contain('... p. unlabeled')
    page.text().should.contain('[ ... ]')


def test_pagination(query):
    page = query('')

    page.text().should.contain('Results 1-15 of 6065 for *')

    page = follow_link(page('a').with_text('404'))

    page.text().should.contain('Results 6046-6060 of 6065 for *')


def test_sort(query):
    # testing "relevance" might be too brittle for now
    page = query('experiments')
    page.text().should.contain('Argument: Final plea for Karl Gebhardt')
    page = follow_link(page('a.page-number').with_text('100'))
    page.text().should.contain('Brief: Prosecution closing brief against Georg Loerner')

    # test date sorts
    page = query('-date:none')
    page = go_to(page.absolute_url(page('select option').with_text('Earliest Date').val()))
    page.text().should.contain('18 August 1896')
    page = follow_link(page('a.page-number').with_text('355'))
    page.text().should.contain('03 September 1948')

    page = query('-date:none')
    page = go_to(page.absolute_url(page('select option').with_text('Latest Date').val()))
    page.text().should.contain('03 September 1948')
    page = follow_link(page('a.page-number').with_text('355'))
    page.text().should.contain('18 August 1896')

    # test page sorts
    page = query('')
    page = go_to(page.absolute_url(page('select option').with_text('Most Pages').val()))
    page.text().should.contain('492 pages')
    page = follow_link(page('a.page-number').with_text('405'))
    page.text().should.contain('0 pages')

    page = query('')
    page = go_to(page.absolute_url(page('select option').with_text('Fewest Pages').val()))
    page.text().should.contain('0 pages')
    page = follow_link(page('a.page-number').with_text('405'))
    page.text().should.contain('492 pages')
