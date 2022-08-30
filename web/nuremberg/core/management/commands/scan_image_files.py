import requests, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO, SEEK_CUR

from django.core.management.base import BaseCommand
from nuremberg.documents.models import Document, DocumentImage, DocumentImageType

class Command(BaseCommand):
    help = 'Populates the DocumentImage metadata for any missing images'

    def add_arguments(self, parser):
        parser.add_argument('--ids', nargs='+', type=int, default=None, help='Document ids to scan for missing images (default is all documents)')

    def handle(self, *args, **options):
        documents = Document.objects
        if options['ids']:
            documents = documents.filter(id__in=options['ids'])
        else:
            documents = documents.all()

        with ThreadPoolExecutor(max_workers=10) as pool:
            for document in documents:
                if document.image_count and document.images.count() < document.image_count:
                    pool.submit(populate_document, document)
                else:
                    print("skipping document",document.id)

def populate_document(document):
    print("Populating", document.id, document.image_count)
    with ThreadPoolExecutor(max_workers=10) as pool:
        for page_number in range(1, document.image_count + 1):
            if not document.images.filter(page_number=page_number).exists():
                pool.submit(populate_metadata, document, page_number)
    print("Populated", document.id, document.image_count)


def populate_metadata(document, page_number):
    image = DocumentImage(document=document, page_number=page_number)

    filename = "{:05d}{:03d}".format(document.id, page_number)
    old_image = document.old_images.filter(filename=filename).first()

    if old_image:
        if old_image.physical_page_number:
            physical_page_number = re.sub(r'[^\d]', '', old_image.physical_page_number)
            if physical_page_number:
                image.physical_page_number = int(physical_page_number)

        image.image_type = old_image.image_type
    else:
        image.image_type = DocumentImageType.objects.get(id=4)

    image.url = "http://nuremberg.law.harvard.edu/imagedir/HLSL_NMT01/HLSL_NUR_{}.jpg".format(filename)
    (image.width, image.height) = get_jpeg_size(image.url)
    image.scale = DocumentImage.SCREEN
    if not (image.width and image.height):
        image.url = None
    image.save()

def get_jpeg_size(url, header_length=5000):
    header = requests.get(url, headers={'Range': 'bytes=0-{}'.format(header_length)})


    data = BytesIO(header.content)

    if data.read(2) != b'\xFF\xD8':
        print("not a valid JPEG file ", url, header.content)
        return (None, None)

    # scan the JFIF header for the SOF0 block with image dimensions in it
    while True:
        block_header = data.read(2)
        block_size = int.from_bytes(data.read(2), byteorder="big")
        if block_header == b'\xFF\xc0': # found SOF0
            break
        if block_header == b'':
            if header_length and header_length < 50000:
                return get_jpeg_size(url, header_length + 25000)
            elif header_length:
                return get_jpeg_size(url, '')

            print("ran out of bytes in JPEG header", url, "after", len(header.content))
            raise Exception("out of bytes")
        data.seek(block_size - 2, SEEK_CUR) # size includes size bytes

    data.read(1)

    height = int.from_bytes(data.read(2), byteorder="big")
    width = int.from_bytes(data.read(2), byteorder="big")
    return (width, height)
