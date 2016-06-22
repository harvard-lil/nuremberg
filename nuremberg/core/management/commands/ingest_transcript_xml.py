from os import path, listdir
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO, SEEK_CUR

from django.core.management.base import BaseCommand
from nuremberg.documents.models import DocumentCase
from nuremberg.transcripts.models import Transcript, TranscriptPage

class Command(BaseCommand):
    help = 'Parses a transcript page XML file or files and creates the appropriate models'

    filename_re = re.compile(r'^NRMB-(?P<case_label>[A-Z]+)(?P<case_number>\d{2})?-(?P<volume>\d{2})_(?P<vol_seq>\d{5})_[01]\.xml$')

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+', type=str, help='XML files to ingest')
        parser.add_argument('-d', action='store_true', default=False, help='Injest every XML file in the provided directories.')
        parser.add_argument('-s', default=None, type=int, help='Skip N files before ingesting.')

    def handle(self, *args, **options):
        count = 0
        if options['d']:
            paths = []
            for dirname in options['paths']:
                paths += [path.join(dirname, name) for name in listdir(dirname)]
        else:
            paths = options['paths']
        if options['s']:
            print('Skipping', options['s'], 'files.')
            paths = paths[options['s']:]
        print('Ingesting', len(paths), 'files.')
        for file_path in paths:
            if not path.exists(file_path):
                print("No such file:", filename)
                continue

            filename = path.basename(file_path)
            m = self.filename_re.match(filename)
            if not m:
                print("Don't know how to process this:", filename)
                continue

            # sketchily get case ID
            if m.group('case_label') == 'NMT':
                case_id = int(m.group('case_number')) + 1
            elif m.group('case_label') == 'IMT':
                case_id = 1
            else:
                print("I don't know a case called",m.group('case_label'))
                continue

            case = DocumentCase.objects.get(pk=case_id)
            try:
                transcript = case.transcript
            except Transcript.DoesNotExist:
                transcript = Transcript.objects.create(case=case, title="Case transcript for {}".format(case.short_name()))
                print("Created transcript", transcript.title)

            volume_number = int(m.group('volume'))

            volume = transcript.volumes.filter(volume_number=volume_number).first()
            if not volume:
                volume = transcript.volumes.create(volume_number=volume_number)
                print("Created transcript volume", transcript.title, volume.volume_number)

            volume_seq_number = int(m.group('vol_seq'))
            page = volume.pages.filter(volume_seq_number=volume_seq_number).first()
            with open(file_path, 'r') as file:
                xml = file.read()
            if not page:
                page = TranscriptPage( transcript=transcript, volume=volume, volume_seq_number=volume_seq_number)
            page.xml = xml
            try:
                page.populate_from_xml()
            except Exception as e:
                print('error populating page', file_path)
                raise e
            page.save()
            count += 1
            if count % 100 == 0: print('Created', count, 'pages.')
