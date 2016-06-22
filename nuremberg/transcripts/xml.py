import re
from lxml import etree

class TranscriptPageJoiner:
    """
    This class is a parser for transcript XML pages that generates joined sentences across page boundaries.
    Input is a list of TranscriptPage objects.
    Output is a list of TranscriptPage objects, missing the first and last input page, mated to
    HTML blobs that always begin and end on sentence breaks.
    In addition to joining pages, the joiner also outputs page numbers, references, speaker tags and
    headers when they can be identified.

    The class is mainly just a state-carrier for the complex logic of the put_page function.
    It is fairly fast for what it is -- lxml and regexes should run in linear time. Still, it's probably
    a good idea to cache the output when possible.

    Use it like so:

    pages = TranscriptPage.objects.filter(...)
    joiner = TranscriptPageJoiner(pages)
    joiner.build_html()
    joiner.html_pages # => "[{'html': ''<p>transcript text</p>..."

    It is designed to be used for splicing separately-generated page ranges together.

    The default behavior is for the first and last pages provided to be used only to complete the
     boundary sentences. This means at least three input pages are required to output one page.

    The way it works is the first marked page (the second page provided)
    is delayed until a sentence boundary, as determined by the first page.
    The last marked page (the second-to-last page provided) is carried forward
    to a sentence boundary, as determined by the last page.

    The entire first page, most or all of the last page, and likely some of the first
    marked page will be left out of the output. However, the result is sensible
    joins that splice easily across page ranges without a substantial amount
    of unnecessary logic or retained state.

    For example, if you provide these numbered pages:
    [
    "<p>Sentence one. Sentence</p> <pageNum>1</pageNum>"),
    "<p>two.</p> <p>Sentence three. Sentence</p> <pageNum>2</pageNum>",
    "<p>five. Sentence six.</p> <pageNum>3</pageNum>"
    ]

    the output will be:
    "<p><page>2</page> <p>Sentence three. Sentence five.</p>"

    Since the behavior between first and last pages is consistent, splicing is simply
    a matter of providing the last full  page as the first page to splice, or vice versa:

    [
    "<p>two.</p> <p>Sentence three. Sentence</p> <pageNum>2</pageNum>",
    "<p>five. Sentence six.</p> <pageNum>3</pageNum>",
    [include_last]
    ]
    becomes:

    "<page>3</page> <p>Sentance six.</p>"


    [
    [include_first]
    "<p>Sentence one. Sentence</p> <pageNum>1</pageNum>"),
    "<p>two.</p> <p>Sentence three. Sentence</p> <pageNum>2</pageNum>",
    ]
    becomes:

    "<page>1</page> <p>Sentence one. Sentence two.</p>"

    (include_first and include_last kwargs indicate that those pages should be included in full)

    For convenience, the joiner sets attributes indicating the proper first and last
    seq number displayed. So in example one,

    joiner.from_seq == 2
    joiner.to_seq == 2

    These values can be used without transformation to find page ranges that will
    append to the joined text without missing or repeated text or page numbers;
    seq_number__gte=2 will give a page range that can be spliced after it,
    and seq_number__lte=2 will give a page range that can be spliced before.
    """

    def __init__(self, pages, include_first=False, include_last=False):
        self.include_first = include_first
        self.include_last = include_last
        self.pages = pages

    # Matches paragraphs that look like 'Court No. 1', mod OCR errors
    ignore_p = re.compile(r'^Cou[rn]t (N[o0][\.\:]? ?)?[\dILO]', re.IGNORECASE)

    # Match for places it makes sense to end a paragraph
    sentence_ending_letters = r'|'.join(( # ends of sentences that exclude "Mr."
        r'[a-z]{2}', # something like "service."
        r'[A-Z]{2}', # something like "OKL."
        r'[0-9]{2}[\w%]?\.?', # something like "23." or "23.:" or "-28a)."
        r'\s[I]', # something like "as did I."
        r'</a>', #something like "<a>NO-223</a>."
    ))
    # BUG: OCR sometimes reads '.' as ',' . Nothing to do about it
    sentence_ending_punctuation = r'([\.\?\:]|\.{3,5})' # mandatory punctuation to end a sentence
    sentence_wrapping = r'[\)\"]' # optional wrapping outside a sentence
    sentence_inner_wrapping = r'[\)\"]' # optional wrapping inside a sentence

    # a conservative regex used to break up paragraphs (we don't want to do this too randomly)
    sentence_break = re.compile(r'([a-z0-9]{2}[\.\?\:][\)\"]?)')

    # a liberal regex used to identify paragraph breaks to ignore
    sentence_ends = (
        r'<p>\s*$', # end on a blank paragraph (likely inserted)
        r'</span>\s*$', # end on a heading or subheading
        r'^\s*$', # end on an empty paragraph
        r'({}){}?{}{}?\s*$'.format(sentence_ending_letters, \
            sentence_inner_wrapping, \
            sentence_ending_punctuation, \
            sentence_wrapping, \
            ),
    )
    sentence_end = re.compile(r'|'.join(sentence_ends))

    # a fully parenthesized non-sentence paragraph is almost always a subheading
    subheading = re.compile(r'^\([^\.]+[^\!\?\:\"]\)$')

    # speech (a <spkr> tail) with no lowercase letters is probably a misidentified heading
    speech_heading = re.compile(r'^[^a-z]{4,}$')

    # match for long page numbers with suffix
    page_number = re.compile(r'^(?P<digits>\d+)(?P<suffix>[^\d]+)?$')

    # enables hinting to figure out why joining isn't working
    debug = False

    # state variables
    input_page = None # the current page being parsed
    output_page = None # the page being created (different from input_page if joining)

    joining = False # in joining state, paragraph breaks will be deferred to the next natural sentence boundary
    join_page = False # if joining bridges a page, defer the next page break
    ignore_join = False # used by first_page to indicate that the first join found on the second page should be elided

    first_page = last_page = False # used to trim content from the first and last included pages

    # convenience output indicating the proper seq numbers to be used for splicing with this join
    from_seq = to_seq = None

    def build_html(self):
        self.html_pages = []
        count = len(self.pages)
        for index, page in enumerate(self.pages, start=1):
            self.first_page = index == 1 and not self.include_first
            self.last_page = index == count and not self.include_last

            self.seq = page.seq_number

            if not (self.first_page or self.last_page):
                self.from_seq = self.from_seq or self.seq
                self.to_seq = self.seq

            if self.last_page and not self.joining:
                return
            elif self.first_page:
                self.input_page = None
            else:
                self.input_page = page

            self.put_page(page)

            if self.joining:
                self.join_page = True
                if self.first_page:
                    # if the first page ends with an open join, signal to drop that join from the output.
                    self.ignore_join = True

    def open_page(self):
        self.page_html = ''
        self.log('<span>[opened seq {}]</span>'.format(self.seq))
        self.output_page = self.input_page

    def close_page(self):
        self.log('<span>[closed]</span>')
        if self.page_html and self.output_page:
            self.html_pages.append({'page': self.output_page, 'html': self.page_html})

    def put(self, text):
        self.page_html += text

    def open_p(self):
        self.put('<p>\n')
    def close_p(self):
        self.put('\n</p>\n')

    def log(self, text): # pragma: no cover
        if self.debug:
            self.page_html += text

    def join_text(self, joined_text):
        if joined_text:
            ends = self.sentence_break.split(joined_text, 1)
            if len(ends) == 3:
                if not self.ignore_join:
                    self.put(ends[0] + ends[1])
                    self.close_p()
                    self.log( '[INSERTED END]')
                    self.log('match: ' + str(ends))

                self.ignore_join = False
                self.joining = False

                if self.join_page:
                    self.close_page()
                    if self.last_page:
                        return
                    self.open_page()
                    self.join_page = False

                self.open_p()
                self.put(ends[2])

            elif not self.ignore_join:
                # we only end ignoring on a successful join
                self.put(joined_text)

    def close_join(self):
        self.close_p()
        if self.join_page:
            self.close_page()
            if self.last_page:
                return
            self.open_page()
            self.join_page = False
        self.joining = False
        self.ignore_join = False

    def put_page(self, page):
        ignore_p = False
        if not self.joining:
            self.open_page()
        for event, element in etree.iterwalk(page.xml_tree(), events=('start', 'end')):
            if self.last_page and not self.joining:
                # final join is complete
                return
            if element.tag == 'p' :
                # since p tags have children, we have to open and close them separately
                if event == 'start':
                    # skip paragraphs that aren't real transcript text
                    if (len(element) and element[0].tag == 'runningHead') \
                        or (element.text and len(element.text) < 20 and self.ignore_p.match(element.text)):
                        ignore_p = True
                        continue
                    # decide whether to output a <p> tag
                    if not self.joining:
                        self.open_p()
                        if element.text:
                            if self.subheading.match(element.text):
                                self.put('<span class="subheading">{}</span>'.format(element.text))
                            else:
                                self.put(element.text)
                    else:
                        self.join_text(element.text)

                elif event == 'end':
                    if ignore_p:
                        ignore_p = False
                        continue

                    # decide whether to output a </p> tag
                    if not self.sentence_end.search(self.page_html):
                        self.joining = True
                        # BUG: No good way to tell if this is the middle of a word.
                        # It's usually not...
                        # For the future, use &mdash; to mark words that should be joined?
                        if self.page_html[-1] != '—':
                            self.put(' ')
                        self.log('[IGNORING END]')
                    elif not self.joining:
                        self.close_p()

            elif event == 'end':
                # no other tags have children, so just output them at closing

                if element.tag == 'spkr':
                    if self.joining:
                        # a <spkr> tag should always close a paragraph, even if it seems incomplete
                        self.close_join()
                        self.open_p()
                    if element.text and (len(element.text) <= 2 or (element.tail and not element.tail.isspace())):
                        if self.speech_heading.match(element.tail):
                            # a <spkr> with an all-caps tail is probably a mis-identified header
                            self.put('<span class="heading">{} {}</span>'.format(element.text, element.tail))
                        else:
                            self.put('<span class="speaker">{}</span>{}'.format(element.text, element.tail))
                    else:
                        # A <spkr> without a tail is usually a header
                        self.put('<span class="heading">{}</span>'.format(element.text))

                elif element.tag in ('evidenceFileDoc', 'exhibitDocPros', 'exhibitDocDef'):
                    if element.tag == 'evidenceFileDoc':
                        self.put('<a href="/search?q=evidence:{}">{}</a>'.format(element.get('n'), element.text))
                    elif element.tag == 'exhibitDocPros':
                        self.put('<a href="/search?q=exhibit:Prosecution+{}">{}</a>'.format(element.get('n'), element.text))
                    elif element.tag == 'exhibitDocDef':
                        self.put('<a href="/search?q=exhibit:{}+{}">{}</a>'.format(element.get('def'), element.get('n'), element.text))

                    if element.tail:
                        if not self.joining:
                            self.put(element.tail)
                        else:
                            self.join_text(element.tail)

        if not (self.joining or self.last_page):
            self.close_page()
