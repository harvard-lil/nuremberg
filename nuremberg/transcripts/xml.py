import re
from lxml import etree
from datetime import datetime
from django.utils.text import slugify
from django.template import Template, Context
from django.contrib.humanize.templatetags.humanize import intcomma

class TranscriptPageJoiner:
    """
    This class is a parser for transcript XML pages that generates joined sentences across page boundaries.
    It's mainly just a state-carrier for the complex logic of the joined_html function.

    In addition to joining pages, the joiner also outputs page numbers, references, speaker tags and
    headers when they can be identified.

    It is fairly fast for what it is -- lxml and regexes should run in linear time. Still, it's probably
    a good idea to cache the output when possible.

    Use it like so:

    pages = TranscriptPage.objects.filter(...)
    joiner = TranscriptPageJoiner(pages)
    joiner.build_html()
    joiner.html # => "<p>transcript text</p>..."

    It is designed to be used for splicing separately-generated page ranges together.

    The default behavior is for the first and last pages provided to be used only to complete the
    determine boundary sentences. This means at least three pages are required.

    The way it works is the first marked page (the second page provided)
    is delayed until a sentence boundary, as determined by the first page.
    The last marked page (the second-to-last page provided) is carried forward
    to a sentence boundary, as determined by the last page.

    The entire first page, most or all of the last page, and likely some of the first
    marked page will be left out of the output. However, the result is sensible
    joins that splice easily across page ranges without a substantial amount
    of unnecessary logic or carried state.

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
        r'[0-9]{2}\w?\.?', # something like "23." or "23.:" or "-28a)."
        r'\s[I]',
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

    # enable hinting to figure out why joining isn't working
    debug = False

    # state variables
    joining = False # in joining state, paragraph breaks will be deferred to the next natural sentence boundary
    ignore_join = False # used by first_page to indicate that the first join found on the second page should be elided
    carried = False # the carried string will be inserted after the next join (i.e., page number)
    closing = False # in closing state, the last page is used only to finish the open join
    first_page = last_page = False # used to trim content from the first and last included pages

    # convenience output indicating the proper seq numbers to be used for splicing with this join
    from_seq = to_seq = None

    def build_html(self):
        self.html = ''
        self.html += '<div>'
        if self.debug:
            self.html += '<span>[opening]</span>'
        count = len(self.pages)
        self.first_page = not self.include_first
        for page in self.pages:
            self.seq = page.seq_number
            if not self.include_last:
                count -= 1
                self.last_page = count == 0
            if self.debug:
                self.html += '<span>[seq {}]</span>'.format(self.seq)
                if self.first_page:
                    self.html += '<span>[first page]</span>'
                if self.last_page:
                    self.html += '<span>[last page]</span>'

            if not (self.first_page or self.last_page):
                self.from_seq = self.from_seq or self.seq
                self.to_seq = self.seq
                if self.joining:
                    self.carried = self.page_label(page)
                else:
                    self.html += self.page_label(page)

            page_html = self.joined_html(page)
            if self.first_page:
                # no text is used from the first page
                # if the first page ends with an open join, signal to drop that join from the output.
                if self.joining:
                    self.ignore_join = True
            else:
                self.html += page_html
            self.first_page = False
        if self.joining:
            # oh well, nothing left to do
            self.html += '</p>'
            if self.debug:
                self.html += '<span>[closed on join]</span>'
        self.html += '</div>'
        return self.html

    def join_text(self, text, joined_text):
        if joined_text:
            ends = self.sentence_break.split(joined_text, 1)
            if len(ends) == 3:
                if not self.ignore_join:
                    text += ends[0] + ends[1]
                    if self.debug:
                        text += '[INSERTED END]'
                    text += '</p>\n'
                    if self.debug:
                        text += 'match: ' + str(ends)

                # we still print carried text after an ignored join (it's the start of a page)
                if self.carried: text += self.carried

                self.ignore_join = False
                self.carried = None
                self.joining = False

                if self.last_page:
                    if self.debug:
                        text += '<span>[closing]</span>'
                    return text

                text += '<p>'
                text += ends[2]

            elif not self.ignore_join:
                # we only end ignoring on a successful join
                text += ''.join(ends)
        return text

    page_label_template = Template("""
    </div>
    <div class="page"  data-seq="{{seq}}" data-page="{{page_number|default:""}}" data-date="{{date|date:'Y-m-d'}}">
        <div class="page-handle">
            <span class="page-details">
                HLSL Seq. No. {{seq}}
                {% if date %}
                    - {{date|date:'d F Y'}}
                {% endif %}
                {% if image_url %}
                    - Image
                    [<a class='view-image'>View</a>]
                    [<a class='download-image' href="{{image_url}}" download="Transcript Seq {{seq}}.jpg">Download</a>]
                {% endif %}
            </span>
            <span class="page-number">Page {{page_label}}</span>
        </div>
    """)

    def page_label(self, page):
        m = None
        if page.page_label:
            m = self.page_number.match(page.page_label)
        if m:
            page_label = intcomma(int(m.group('digits'))) + (m.group('suffix') or '')
        else:
            page_label = 'Unlabeled'
        return self.page_label_template.render(Context({'seq': page.seq_number, 'date': page.date, 'image_url':page.image_url, 'page_label': page_label, 'page_number': page.page_number}))

    def close_join(self, text):
        text += '</p>\n'
        if self.carried: text += self.carried
        self.carried = None
        self.joining = False
        self.ignore_join = False
        return text

    def joined_html(self, page):
        text = ''
        page_label = None
        ignore_p = False
        for event, element in etree.iterwalk(page.xml_tree(), events=('start', 'end')):
            if self.last_page and not self.joining:
                return text
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
                        text += '<p>'
                        if element.text:
                            if self.subheading.match(element.text):
                                text += '<span class="subheading">{}</span>'.format(element.text)
                            else:
                                text += element.text
                    else:
                        text = self.join_text(text, element.text)

                elif event == 'end':
                    if ignore_p:
                        ignore_p = False
                        continue

                    # decide whether to output a </p> tag
                    if not self.sentence_end.search(text):
                        self.joining = True
                        # BUG: No good way to tell if this is the middle of a word.
                        # It's usually not...
                        # For the future, use &mdash; to mark words that should be joined?
                        if text[-1] != '—':
                            text += ' '
                        if self.debug:
                            text += '[IGNORING END]'
                    elif not self.joining:
                        text = self.close_join(text)

            elif event == 'end':
                # no other tags have children, so just output them at closing
                if element.tag == 'spkr':
                    if self.joining:
                        # a <spkr> tag should always close a paragraph, even if it seems incomplete
                        text = self.close_join(text)
                        if self.last_page: return text
                        text += '<p>'
                    if element.text and (len(element.text) <= 2 or (element.tail and not element.tail.isspace())):
                        if self.speech_heading.match(element.tail):
                            # a <spkr> with an all-caps tail is probably a mis-identified header
                            text += '<span class="heading">{} {}</span>'.format(element.text, element.tail)
                        else:
                            text += '<span class="speaker">{}</span>{}'.format(element.text, element.tail)
                    else:
                        # A <spkr> without a tail is usually a header
                        text += '<span class="heading">{}</span>'.format(element.text)

                elif element.tag in ('evidenceFileDoc', 'exhibitDocPros', 'exhibitDocDef'):
                    if element.tag == 'evidenceFileDoc':
                        text += '<a href="/search?q=evidence:{}">{}</a>'.format(element.get('n'), element.text)
                    elif element.tag == 'exhibitDocPros':
                        text += '<a href="/search?q=exhibit:Prosecution+{}">{}</a>'.format(element.get('n'), element.text)
                    elif element.tag == 'exhibitDocDef':
                        text += '<a href="/search?q=exhibit:{}+{}">{}</a>'.format(element.get('def'), element.get('n'), element.text)

                    if element.tail:
                        if not self.joining:
                            text += element.tail
                        else:
                            text = self.join_text(text, element.tail)

        return text
