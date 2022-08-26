from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.db import models
import datetime
import re

global_slug_count = 0

IMAGE_URL_ROOT="http://nuremberg.law.harvard.edu/imagedir/HLSL_NMT01"

class Document(models.Model):
    id = models.AutoField(primary_key=True, db_column='DocID')
    title = models.CharField(max_length=255, db_column='TitleDescriptive')
    literal_title = models.TextField(db_column='Title')
    updated_at = models.DateTimeField(auto_now=True, db_column='Updated')

    image_count = models.IntegerField(db_column='NoOfImages', default=0)

    language = models.ForeignKey('DocumentLanguage', db_column='DocLanguageID', on_delete=models.PROTECT)
    source = models.ForeignKey('DocumentSource', db_column='DocVersionID', on_delete=models.PROTECT)

    def page_range(self):
        return range(1, (self.image_count or 0) + 1)

    def images_screen(self):
        test_empty = self.images.all()
        test_empty = len(test_empty)
        if test_empty:
            return (image for image in self.images.all() if image.scale == DocumentImage.SCREEN)
        else:
            return "no images"

    def date(self):
        date = self.dates.first()
        if date:
            return date.as_date()

    def slug(self): # pragma: no cover
        global global_slug_count
        global_slug_count += 1
        # Try to extract the "genre term" from the descriptive title
        try:
            words = self.title.split(' ')
            n = 4
            while n < len(words) and words[n-1] in ('a', 'an', 'the', 'in', 'of', 'to', 'at', 'on', 'and', 'for'):
                n += 1
            testing =  slugify(' '.join(words[:n]))
            #print ("{0}. DocID: {1} TitleDescriptive slug: {2}".format(global_slug_count, self.id, testing))
            return slugify(' '.join(words[:n]))
        except:
            testing = "descriptive-title-missing"
            #print ("{0}. DocID: {1} TitleDescriptive slug: {2}".format(global_slug_count, self.id, testing))
            return testing

    class Meta:
        managed = False
        db_table = 'tblDoc'

    def __str__(self):
        return "#{0} - {1}".format(self.id, self.title)

class DocumentImage(models.Model):
    document = models.ForeignKey(Document, related_name='images', on_delete=models.PROTECT)

    page_number = models.IntegerField()
    physical_page_number = models.IntegerField(blank=True, null=True)

    THUMB = 't'
    HALF = 'h'
    SCREEN = 's'
    DOUBLE = 'd'
    FULL = 'f'
    IMAGE_SCALES = (
        (THUMB, 'thumb'),
        (HALF, 'half'),
        (SCREEN, 'screen'),
        (DOUBLE, 'double'),
        (FULL, 'full'),
    )

    url = models.CharField(max_length=255, blank=True, null=True)
    scale = models.CharField(max_length=1, choices=IMAGE_SCALES)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)

    image_type = models.ForeignKey('DocumentImageType', on_delete=models.PROTECT)

    def __getattribute__(self, attrname):
        orig = super().__getattribute__(attrname)
        if attrname == 'url' and settings.PROXY_DOCUMENT_IMAGE_THUMBS and orig.startswith('/static/image_cache/thumb/'):
            return reverse('proxy_image', kwargs={'path': orig.split('/')[-1]})
        return orig

    def find_url(self, scale):
        if self.scale == scale:
            return url
        else:
            images = self.document.images.all()
            filter = (image for image in images if image.page_number == self.page_number and image.scale == scale)
            scaled = next(filter, None)
            if scaled:
                return scaled.url
            else:
                return None

    def thumb_url(self):
        return self.find_url(self.THUMB)
    def screen_url(self):
        return self.find_url(self.SCREEN)
    def full_url(self):
        return self.find_url(self.FULL)

    def image_tag(self):
        return '<a href="{0}"><img src="{0}" alt="Scanned document page {1}" width=100 /></a>'.format(self.url, self.page_number)
    image_tag.allow_tags = True

    def __str__(self):
        return "#{} Page {} {} {}x{}".format(self.document.id, self.page_number, self.scale, self.width, self.height)

    class Meta:
        managed = False
        ordering = ['page_number']


class OldDocumentImage(models.Model):
    id = models.AutoField(primary_key=True, db_column='ImagesListID')
    document = models.ForeignKey(Document, related_name='old_images', on_delete=models.PROTECT, db_column='DocID')

    page_number = models.IntegerField(db_column='PageSequenceNo')
    physical_page_number = models.CharField(max_length=50, db_column='PhysicalPageNo')

    filename = models.CharField(db_column='FileName', max_length=8, blank=True, null=True)

    image_type = models.ForeignKey('DocumentImageType', db_column='PageTypeID', on_delete=models.PROTECT)

    class Meta:
        managed = False
        db_table = 'tblImagesList'


class DocumentImageType(models.Model):
    id = models.AutoField(primary_key=True, db_column='PageTypeID')
    name = models.CharField(max_length=50, db_column='PageType')
    class Meta:
        managed = False
        db_table = 'tblPageTypes'

class DocumentSource(models.Model):
    id = models.AutoField(primary_key=True, db_column='VersionID')
    name = models.CharField(max_length=50, db_column='Version')
    class Meta:
        managed = False
        db_table = 'tblVersions'

class DocumentLanguage(models.Model):
    id = models.AutoField(primary_key=True, db_column='LanguageID')
    name = models.CharField(max_length=15, db_column='Language')
    class Meta:
        managed = False
        db_table = 'tblLanguages'

class DocumentDate(models.Model):
    id = models.AutoField(primary_key=True, db_column='DatesOfDocListID')
    document = models.ForeignKey(Document, related_name='dates', on_delete=models.CASCADE, db_column='DocID')

    day = models.IntegerField(db_column='DocDay')
    month = models.IntegerField(db_column='DocMonthID') # this is technically a foreign key but also just 1-indexed month number
    year = models.IntegerField(db_column='DocYear')

    def as_date(self):
        if not (self.year and self.month and self.day):
            return None
        if self.year == 0 or self.month == 13 or self.day >= 32:
            return None
        if self.month == 2 and self.day == 29 and (self.year % 4) != 0:
            return None # this is an issue
        return datetime.date(self.year, self.month, self.day)

    class Meta:
        managed = False
        db_table = 'tblDatesOfDocList'


class DocumentPersonalAuthor(models.Model):
    id = models.AutoField(primary_key=True, db_column='PersonalAuthorID')
    last_name = models.CharField(max_length=35, db_column='AuthLName')
    first_name = models.CharField(max_length=25, db_column='AuthFName')
    title = models.CharField(max_length=100, db_column='AuthTitle')

    documents = models.ManyToManyField(Document, related_name='personal_authors', through='DocumentsToPersonalAuthors', through_fields=('author', 'document'))

    def full_name(self):
        if self.first_name and self.last_name:
            return '{} {}'.format(self.first_name, self.last_name)
        else:
            return self.first_name or self.last_name or 'Unknown'

    class Meta:
        managed = False
        db_table = 'tblPersonalAuthors'


class DocumentsToPersonalAuthors(models.Model):
    id = models.AutoField(primary_key=True, db_column='PersonalAuthorsListID')
    document = models.ForeignKey(Document, db_column='DocID', on_delete=models.CASCADE)
    author = models.ForeignKey(DocumentPersonalAuthor, db_column='PAuthNameID', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'tblPersonalAuthorsList'

class DocumentGroupAuthor(models.Model):
    id = models.AutoField(primary_key=True, db_column='GroupAuthorID')
    name = models.CharField(max_length=25, db_column='GroupAuthorName')

    documents = models.ManyToManyField(Document, related_name='group_authors', through='DocumentsToGroupAuthors', through_fields=('author', 'document'))

    def short_name(self):
        return self.name.split(' (')[0]

    class Meta:
        managed = False
        db_table = 'tblGroupAuthors'

class DocumentsToGroupAuthors(models.Model):
    id = models.AutoField(primary_key=True, db_column='GroupAuthorsListID')
    document = models.ForeignKey(Document, db_column='DocID', on_delete=models.CASCADE)
    author = models.ForeignKey(DocumentGroupAuthor, db_column='GANameID', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'tblGroupAuthorsList'

class DocumentCase(models.Model):
    id = models.AutoField(primary_key=True, db_column='CaseID')
    name = models.CharField(max_length=100, db_column='Case_temp')

    @property
    def tag_name(self):
        # cheating for now
        if self.id == 1:
            return 'IMT'
        elif self.id > 13:
            return 'Other'
        else:
            return 'NMT {}'.format(self.id-1)

    def short_name(self):
        return self.name.split(' -')[0].replace('.', ':').replace(' 0', ' ')

    documents = models.ManyToManyField(Document, related_name='cases', through='DocumentsToCases', through_fields=('case', 'document'))

    class Meta:
        managed = False
        db_table = 'tblCases'


class DocumentsToCases(models.Model):
    id = models.AutoField(primary_key=True, db_column='CasesListID')
    document = models.ForeignKey(Document, db_column='DocID', on_delete=models.CASCADE)
    case = models.ForeignKey(DocumentCase, db_column='DocCaseID', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'tblCasesList'

class DocumentDefendantManager(models.Manager):
    """
    Filters out null names
    """
    use_for_related_fields = True
    def get_queryset(self):
        return super().get_queryset().exclude(first_name__isnull=True)

class DocumentDefendant(models.Model):
    objects = DocumentDefendantManager()

    id = models.AutoField(primary_key=True, db_column='DefendantID')
    last_name = models.CharField(max_length=110, db_column='DefLName')
    first_name = models.CharField(max_length=25, db_column='DefFName')
    case = models.ForeignKey(DocumentCase, related_name='defendants', db_column='CaseID', on_delete=models.CASCADE)

    documents = models.ManyToManyField(Document, related_name='defendants', through='DocumentsToDefendants', through_fields=('defendant', 'document'))

    def full_name(self):
        if self.first_name and self.last_name:
            return '{} {}'.format(self.first_name, self.last_name)
        else:
            return self.first_name or self.last_name or 'Unknown'

    class Meta:
        managed = False
        db_table = 'tblDefendants'

class DocumentsToDefendants(models.Model):
    id = models.AutoField(primary_key=True, db_column='DefendantsListID')
    document = models.ForeignKey(Document, db_column='DocID', on_delete=models.CASCADE)
    defendant = models.ForeignKey(DocumentDefendant, db_column='DefNameID', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'tblDefendantsList'


class DocumentActivityManager(models.Manager):
    """
    Filters out first activity (No activity specified)
    """
    use_for_related_fields = True
    def get_queryset(self):
        return super().get_queryset().exclude(id=1)

class DocumentActivity(models.Model):
    objects = DocumentActivityManager()

    id = models.AutoField(primary_key=True, db_column='ActivityID')
    name = models.CharField(max_length=100, db_column='Activity')
    case = models.ForeignKey(DocumentCase, related_name='activities', db_column='CaseID', on_delete=models.CASCADE)

    @property
    def short_name(self):
        # cheating for now
        return self.name.split(' (c')[0]

    documents = models.ManyToManyField(Document, related_name='activities', through='DocumentsToActivities', through_fields=('activity', 'document'))

    class Meta:
        managed = False
        db_table = 'tblActivities'

class DocumentsToActivities(models.Model):
    id = models.AutoField(primary_key=True, db_column='ActivitiesListID')
    document = models.ForeignKey(Document, db_column='DocID', on_delete=models.CASCADE)
    activity = models.ForeignKey(DocumentActivity, db_column='ActNameID', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'tblActivitiesList'


class DocumentEvidencePrefix(models.Model):
    id = models.AutoField(db_column='NMTCodeID', primary_key=True)  # Field name made lowercase.
    code = models.CharField(db_column='NMTCode', max_length=5, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tblNMTCodes'


class DocumentEvidenceCode(models.Model):
    id = models.AutoField(db_column='NMTListID', primary_key=True)  # Field name made lowercase.
    prefix = models.ForeignKey(DocumentEvidencePrefix, db_column='NMTListCodeID', on_delete=models.PROTECT)  # Field name made lowercase.
    document = models.ForeignKey(Document, related_name='evidence_codes', db_column='DocID', on_delete=models.CASCADE)
    number = models.IntegerField(db_column='NMTNo', blank=True, null=True)  # Field name made lowercase.
    suffix = models.CharField(db_column='NMTNoText', max_length=25, blank=True, null=True)  # Field name made lowercase.

    def __str__(self):
        return '{}-{}{}'.format(self.prefix.code, self.number, self.suffix or '')

    class Meta:
        managed = False
        db_table = 'tblNMTList'

class DocumentExhibitCodeName(models.Model):
    id = models.AutoField(db_column='DefenseExhNameID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='DefenseExhName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    case = models.ForeignKey(DocumentCase, db_column='CaseID', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'tblDefenseExhNames'

class DocumentExhibitCode(models.Model):
    id = models.AutoField(db_column='CasesListID', primary_key=True)  # Field name made lowercase.
    document = models.ForeignKey(Document, related_name='exhibit_codes', db_column='DocID', on_delete=models.CASCADE)

    case = models.ForeignKey(DocumentCase, db_column='DocCaseID', on_delete=models.CASCADE)
    prosecution_number = models.IntegerField(db_column='ProsExhNo', blank=True, null=True)  # Field name made lowercase.
    prosecution_suffix = models.CharField(db_column='ProsExhNoSuffix', max_length=5, blank=True, null=True)  # Field name made lowercase.
    prosecution_doc_book_number = models.IntegerField(db_column='ProsDocBkNo', blank=True, null=True)  # Field name made lowercase.
    prosecution_doc_book_suffix = models.CharField(db_column='ProsDocBkNoSuffix', max_length=5, blank=True, null=True)  # Field name made lowercase.

    defense_name = models.ForeignKey(DocumentExhibitCodeName, db_column='DefExhNameID', blank=True, null=True, on_delete=models.SET_NULL)  # Field name made lowercase.
    defense_suffix = models.CharField(db_column='DefExhNoSuffix', max_length=5, blank=True, null=True)  # Field name made lowercase.
    defense_name_denormalized = models.CharField(db_column='DefExhName', max_length=50, blank=True, null=True)
    defense_number = models.IntegerField(db_column='DefExhNo', blank=True, null=True)  # Field name made lowercase.
    defense_suffix = models.CharField(db_column='DefExhNoSuffix', max_length=5, blank=True, null=True)  # Field name made lowercase.

    defense_doc_name_id = models.IntegerField(db_column='DefDocNameID', blank=True, null=True)  # Field name made lowercase.
    defense_doc_name = models.CharField(db_column='DefDocName', max_length=50, blank=True, null=True)  # Field name made lowercase.

    defense_doc_number = models.IntegerField(db_column='DefDocNo', blank=True, null=True)  # Field name made lowercase.
    defense_doc_suffix = models.CharField(db_column='DefDocNoSuffix', max_length=5, blank=True, null=True)  # Field name made lowercase.
    defense_doc_book_name_id = models.IntegerField(db_column='DefDocBkNameID', blank=True, null=True)  # Field name made lowercase.
    defense_doc_book_name = models.CharField(db_column='DefDocBkName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    defense_doc_book_number = models.IntegerField(db_column='DefDocBkNo', blank=True, null=True)  # Field name made lowercase.
    defense_doc_book_suffix = models.CharField(db_column='DefDocBkNoSuffix', max_length=5, blank=True, null=True)  # Field name made lowercase.

    def __str__(self):
        if self.prosecution_number:
            return 'Prosecution {}{}'.format(self.prosecution_number, self.prosecution_suffix or '')
        if self.defense_number:
            if self.defense_name:
                name = self.defense_name.name
            else:
                name = self.defense_name_denormalized or 'Defendant'
            return '{} {}{}'.format(name, self.defense_number, self.defense_suffix or '')
        return ''

    class Meta:
        managed = False
        db_table = 'tblCasesList'
