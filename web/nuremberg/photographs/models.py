from django.utils.text import slugify
from django.db import models
import datetime
import re


class Photograph(models.Model):
    id = models.AutoField(db_column='RecordID', primary_key=True)  # Field name made lowercase.
    inscription = models.CharField(db_column='Inscription', max_length=2000)  # Field name made lowercase.

    year_taken = models.CharField(db_column='Date', max_length=100, blank=True, null=True)  # Field name made lowercase.
    image_url = models.CharField(db_column='FullImageURL', unique=True, max_length=100)  # Field name made lowercase.
    thumb_url = models.CharField(db_column='ThumbnailURL', max_length=100)  # Field name made lowercase.
    material_type = models.CharField(db_column='MaterialType', max_length=100)  # Field name made lowercase.
    via_id = models.CharField(db_column='LocalSystemID', max_length=200, blank=True, null=True)  # Field name made lowercase.
    created_at = models.DateTimeField(db_column='RecordCreated')  # Field name made lowercase.

    title_regex = re.compile(r'^([^:]*caption[^:]*: ?)?([^/]+)( / )?', re.IGNORECASE)
    def title(self):
        return self.title_regex.match(self.inscription).group(2)

    def description(self):
        return '\n'.join(self.inscription.split(' / ')[1:])

    def slug(self):
        return slugify(self.title())

    def date_year(self):
        m = re.search(r'\d{4}', self.year_taken)
        if m:
            return int(m.group(0))

    def date(self):
        return datetime.datetime(self.date_year(), 1, 1)

    class Meta:
        managed = False
        db_table = 'tblPhotographs'
