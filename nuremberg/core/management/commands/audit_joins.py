from django.core.management.base import BaseCommand
from nuremberg.transcripts.models import Transcript
from nuremberg.transcripts.xml import TranscriptPageJoiner


class Command(BaseCommand):
    help = 'Joins transcript pages and outputs a log of all joins made.'

    def add_arguments(self, parser):
        parser.add_argument('transcript', type=int, help='transcript to audit')
        parser.add_argument('from_seq', type=int, help='seq range start')
        parser.add_argument('to_seq', type=int, help='seq range end')
        parser.add_argument('-a', action='store_true', default=False, help='Log allowed paragraph breaks as well as joins.')


    def handle(self, *args, **options):
        transcript = Transcript.objects.get(id=options['transcript'])
        pages = transcript.pages.filter(seq_number__gte=options['from_seq'], seq_number__lte=options['to_seq'])
        joiner = TranscriptPageJoiner(pages)
        joiner.audit = True

        print('Joining {} pages...'.format(pages.count()))
        joiner.build_html()
        print('Join ignored:')
        for row in joiner.joins:
            if row.startswith('IGNORED'):
                print(row)

        print('Join inserted:')
        for row in joiner.joins:
            if row.startswith('INSERTED'):
                print(row)

        print('Join rejected:')
        for row in joiner.joins:
            if row.startswith('REJECTED'):
                print(row)

        print('Join caught:')
        for row in joiner.joins:
            if row.startswith('CAUGHT'):
                print(row)

        if options['a']:
            print('Join allowed:')
            for row in joiner.joins:
                if row.startswith('ALLOWED'):
                    print(row)
