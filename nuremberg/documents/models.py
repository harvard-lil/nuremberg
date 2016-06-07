from django.db import models
import datetime

IMAGE_URL_ROOT="http://nuremberg.law.harvard.edu/imagedir/HLSL_NMT01"

class Document(models.Model):
    id = models.AutoField(primary_key=True, db_column='DocID')
    title = models.CharField(max_length=255, db_column='TitleDescriptive')
    literal_title = models.TextField(db_column='Title')
    updated_at = models.DateTimeField(auto_now=True, db_column='Updated')

    image_count = models.IntegerField(db_column='NoOfImages')

    language = models.ForeignKey('DocumentLanguage', db_column='DocLanguageID')
    source = models.ForeignKey('DocumentSource', db_column='DocVersionID')

    def images_screen(self):
        return self.images.filter(scale=DocumentImage.SCREEN)

    def date(self):
        date = self.dates.first()
        if date:
            return self.dates.first().as_date()

    def slug(self):
        # Try to extract the "genre term" from the descriptive title
        return self.title.split(' ')[0]

    def image_urls(self):
        # This is how the existing site generates page URLs, just concats doc ID with presumed page no.
        image_number = 1
        while image_number <= self.image_count:
            yield "{}/{}{:05d}{:03d}.jpg".format(IMAGE_URL_ROOT, "HLSL_NUR_", self.id, image_number)
            image_number += 1

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

    image_type = models.ForeignKey('DocumentImageType')

    def thumb_url(self):
        return self.local_url().replace('image_cache/', 'image_cache/thumb/')

    def local_url(self):
        return self.url.replace('http://nuremberg.law.harvard.edu/imagedir/HLSL_NMT01/', '/proxy_image/')

    def image_tag(self):
        return '<a href="{0}"><img src="{0}" width=100 /></a>'.format(self.url)
    image_tag.allow_tags = True

    def __str__(self):
        return "#{} Page {} {} {}x{}".format(self.document.id, self.page_number, self.scale, self.width, self.height)

    class Meta:
        ordering = ['page_number']


class OldDocumentImage(models.Model):
    id = models.AutoField(primary_key=True, db_column='ImagesListID')
    document = models.ForeignKey(Document, related_name='old_images', on_delete=models.PROTECT, db_column='DocID')

    page_number = models.IntegerField(db_column='PageSequenceNo')
    physical_page_number = models.CharField(max_length=50, db_column='PhysicalPageNo')

    filename = models.CharField(db_column='FileName', max_length=8, blank=True, null=True)

    image_type = models.ForeignKey('DocumentImageType', db_column='PageTypeID')

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
        return '{} {}'.format(self.first_name, self.last_name)

    class Meta:
        managed = False
        db_table = 'tblPersonalAuthors'


class DocumentsToPersonalAuthors(models.Model):
    id = models.AutoField(primary_key=True, db_column='PersonalAuthorsListID')
    document = models.ForeignKey(Document, db_column='DocID')
    author = models.ForeignKey(DocumentPersonalAuthor, db_column='PAuthNameID')

    class Meta:
        managed = False
        db_table = 'tblPersonalAuthorsList'

class DocumentGroupAuthor(models.Model):
    id = models.AutoField(primary_key=True, db_column='GroupAuthorID')
    name = models.CharField(max_length=25, db_column='GroupAuthorName')

    documents = models.ManyToManyField(Document, related_name='group_authors', through='DocumentsToGroupAuthors', through_fields=('author', 'document'))

    def full_name(self):
        return name.split(' (')[0]

    class Meta:
        managed = False
        db_table = 'tblGroupAuthors'

class DocumentsToGroupAuthors(models.Model):
    id = models.AutoField(primary_key=True, db_column='GroupAuthorsListID')
    document = models.ForeignKey(Document, db_column='DocID')
    author = models.ForeignKey(DocumentGroupAuthor, db_column='GANameID')

    class Meta:
        managed = False
        db_table = 'tblGroupAuthorsList'


class DocumentDefendant(models.Model):
    id = models.AutoField(primary_key=True, db_column='DefendantID')
    last_name = models.CharField(max_length=110, db_column='DefLName')
    first_name = models.CharField(max_length=25, db_column='DefFName')
    case = models.IntegerField( db_column='CaseID')

    documents = models.ManyToManyField(Document, related_name='defendants', through='DocumentsToDefendants', through_fields=('defendant', 'document'))

    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    class Meta:
        managed = False
        db_table = 'tblDefendants'


class DocumentsToDefendants(models.Model):
    id = models.AutoField(primary_key=True, db_column='DefendantsListID')
    document = models.ForeignKey(Document, db_column='DocID')
    defendant = models.ForeignKey(DocumentDefendant, db_column='DefNameID')

    class Meta:
        managed = False
        db_table = 'tblDefendantsList'


class DocumentCase(models.Model):
    id = models.AutoField(primary_key=True, db_column='CaseID')
    name = models.CharField(max_length=100, db_column='Case_temp')

    @property
    def short_name(self):
        # cheating for now
        if self.id == 1:
            return 'IMT'
        elif self.id > 13:
            return 'Other'
        else:
            return 'NMT {}'.format(self.id-1)

    documents = models.ManyToManyField(Document, related_name='cases', through='DocumentsToCases', through_fields=('case', 'document'))

    class Meta:
        managed = False
        db_table = 'tblCases'


class DocumentsToCases(models.Model):
    id = models.AutoField(primary_key=True, db_column='CasesListID')
    document = models.ForeignKey(Document, db_column='DocID')
    case = models.ForeignKey(DocumentCase, db_column='DocCaseID')

    class Meta:
        managed = False
        db_table = 'tblCasesList'

class DocumentActivity(models.Model):
    id = models.AutoField(primary_key=True, db_column='ActivityID')
    name = models.CharField(max_length=100, db_column='Activity')

    @property
    def short_name(self):
        # cheating for now
        return self.name.split(' (')[0]

    documents = models.ManyToManyField(Document, related_name='activities', through='DocumentsToActivities', through_fields=('activity', 'document'))

    class Meta:
        managed = False
        db_table = 'tblActivities'

class DocumentsToActivities(models.Model):
    id = models.AutoField(primary_key=True, db_column='ActivitiesListID')
    document = models.ForeignKey(Document, db_column='DocID')
    activity = models.ForeignKey(DocumentActivity, db_column='ActNameID')

    class Meta:
        managed = False
        db_table = 'tblActivitiesList'
