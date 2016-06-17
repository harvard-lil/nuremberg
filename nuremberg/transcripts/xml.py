import re
from io import BytesIO
from lxml import etree
from datetime import datetime
from django.utils.text import slugify

from django.db import models
from nuremberg.documents.models import DocumentCase

class TranscriptPageJoiner:
    def __init__(self, pages):
        self.pages = pages

    # Matches paragraphs that look like 'Court No. 1', mod OCR errors
    ignore_p = re.compile(r'^Cou[rn]t (N[oO0][\.\:]? ?)?[\dIlO]')

    # Match for places it makes sense to end a paragraph
    sentence_ending_letters = r'|'.join(( # ends of sentences that exclude "Mr."
        r'[a-z]{2}', # something like "service."
        r'[A-Z]{2}', # something like "OKL."
        r'\s\d+\.?', # something like "23." or "23.:"
        r'</a>', #something like "<a>NO-223</a>."
    ))
    # BUG: OCR sometimes reads '.' as ',' . Nothing to do about it
    sentence_ending_punctuation = r'[\.\?\:]' # mandatory punctuation to end a sentence
    sentence_wrapping = r'[\)\"]' # optional wrapping outside a sentence
    sentence_inner_wrapping = r'[\)\"]' # optional wrapping inside a sentence

    # a conservative regex used to break up paragraphs (we don't want to do this too randomly)
    sentence_break = re.compile(r'([a-z0-9]{2}[\.\?\:][\)\"]?)')

    # a liberal regex used to identify paragraph breaks to ignore
    sentence_ends = (
        r'<p>\s*$', # end on a blank paragraph (likely inserted)
        r'</span>\s*$', # end on a heading or subheading
        r'^\s*$', # end on an empty string
        r'({}){}?{}{}?\s*$'.format(sentence_ending_letters, \
            sentence_inner_wrapping, \
            sentence_ending_punctuation, \
            sentence_wrapping, \
            ),
    )
    sentence_end = re.compile(r'|'.join(sentence_ends))

    # a fully parenthesized non-sentence paragraph is almost always a subheading
    subheading = re.compile(r'^\(.+[^\.\!\?\:\"]\)$')

    # speech (a <spkr> tail) with no lowercase letters is probably a misidentified heading
    speech_heading = re.compile(r'^[^a-z]{4,}$')

    debug = False # enable hinting to figure out why joining isn't working
    joining = False # in joining state, paragraph breaks will be deferred to the next natural sentence boundary
    carried = False # the carried string will be inserted after the next join (i.e., page number)
    closing = False # in closing state, the last page is used only to finish the open join

    def html(self):
        text = ''
        self.count = len(self.pages)
        for page in self.pages:
            self.count -= 1
            text += self.joined_html(page)
        return text

    def join_text(self, text, joined_text):
        if joined_text:
            ends = self.sentence_break.split(joined_text, 1)
            if len(ends) == 3:
                text += ends[0] + ends[1]
                if self.debug:
                    text += '[INSERTED END]'
                text += '</p>\n'
                if self.debug:
                    text += 'match: ' + str(ends)
                if self.carried: text += self.carried
                if self.closing: return text
                text += '<p>'
                text += ends[2]

                self.carried = None
                self.joining = False
            else:
                text += ''.join(ends)
        return text

    def close_join(self, text):
        if self.carried: text += self.carried
        self.carried = None
        self.joining = False
        return text

    def joined_html(self, page):
        text = ''
        page_label = None
        ignore = False
        self.closing = self.count == 0
        for event, element in etree.iterwalk(page.xml_tree(), events=('start', 'end')):
            if event == 'end' and element.tag == 'pageNum':
                page_label = '<div class="page-handle"><span class="page-number">Page {} ({})</span></div>\n'.format(element.text, page.seq_number)
                if self.joining:
                    self.carried = page_label
                else:
                    text += page_label
            if element.tag == 'p' :
                # print(element, element.text)
                if len(element) and element[0].tag == 'runningHead':
                    continue
                if event == 'start':
                    if element.text and len(element.text) < 20 and self.ignore_p.match(element.text):
                        ignore = True
                        continue
                    if not self.joining:
                        text += '<p>'
                        if element.text:
                            if self.subheading.match(element.text):
                                text += '<span class="subheading">{}</span>'.format(element.text)
                            else:
                                text += element.text
                    else:
                        text = self.join_text(text, element.text)
                if event == 'end':
                    if ignore:
                        ignore = False
                        continue
                    # only close paragraphs on full sentences.
                    if not self.sentence_end.search(text):
                        self.joining = True
                        # BUG: No good way to tell if this is the middle of a word.
                        # It's usually not...
                        # For the future, use &mdash; to mark words that should be joined.
                        if text[-1] != '—':
                            text += ' '
                        if self.debug:
                            text += '[IGNORING END]'
                    elif not self.joining:
                        text += '</p>\n'
                        text = self.close_join(text)
                        if self.closing: return text
            elif element.tag == 'spkr' and event == 'end':
                if self.joining:
                    # a <spkr> tag should always close a paragraph, even if it seems incomplete
                    text += '</p>\n'
                    text = self.close_join(text)
                    if self.closing: return text
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
            elif element.tag == 'evidenceFileDoc' and event == 'end':
                text += '<a href="/search?q=evidence:{}">{}</a>'.format(element.get('n'), element.text)
                if element.tail:
                    if not self.joining:
                        text += element.tail
                    else:
                        text = self.join_text(text, element.tail)
            elif element.tag == 'exhibitDocPros' and event == 'end':
                text += '<a href="/search?q=exhibit:Prosecution+{}">{}</a>'.format(element.get('n'), element.text)
                if element.tail:
                    if not self.joining:
                        text += element.tail
                    else:
                        text = self.join_text(text, element.tail)
            elif element.tag == 'exhibitDocDef' and event == 'end':
                text += '<a href="/search?q=exhibit:{}+{}">{}</a>'.format(element.get('def'), element.get('n'), element.text)
                if element.tail:
                    if not self.joining:
                        text += element.tail
                    else:
                        text = self.join_text(text, element.tail)

        # default sequence page number for pages with no literal page number
        if not page_label:
            self.carried = '<div class="page-handle"><span class="page-number">Page ? ({})</span></div>\n'.format(page.seq_number)
            if not joining:
                text += self.carried
                self.carried = None

        return text
