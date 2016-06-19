# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-16 21:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('documents', '0005_auto_20160616_1938'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transcript',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('case', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='transcript', to='documents.DocumentCase')),
            ],
        ),
        migrations.CreateModel(
            name='TranscriptPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seq_number', models.IntegerField(db_index=True)),
                ('volume_seq_number', models.IntegerField(db_index=True)),
                ('date', models.DateTimeField(blank=True, null=True)),
                ('page_number', models.IntegerField(blank=True, null=True)),
                ('page_label', models.CharField(blank=True, max_length=10, null=True)),
                ('xml', models.TextField()),
                ('transcript', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pages', to='transcripts.Transcript')),
            ],
        ),
        migrations.CreateModel(
            name='TranscriptVolume',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volume_number', models.IntegerField()),
                ('description', models.TextField(blank=True, null=True)),
                ('transcript', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='volumes', to='transcripts.Transcript')),
            ],
        ),
        migrations.AddField(
            model_name='transcriptpage',
            name='volume',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pages', to='transcripts.TranscriptVolume'),
        ),
        migrations.AlterUniqueTogether(
            name='transcriptpage',
            unique_together=set([('volume', 'volume_seq_number'), ('transcript', 'seq_number')]),
        ),
        migrations.AlterIndexTogether(
            name='transcriptpage',
            index_together=set([('volume', 'volume_seq_number'), ('transcript', 'seq_number')]),
        ),
    ]
