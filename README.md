# HLS Nuremberg Trials Project

> This is a Django client for the digital archives of the Nuremberg Trials
> Project maintained by the Harvard Law Library.  It is intended as a
> open-access web app for scholars, researchers, and members of the public,
> exposing the digitized documents, full-text trial transcripts, and rich
> search features for the same in a friendly, modern interface.


## Setup

The client uses [Docker/Docker Compose](https://docs.docker.com/compose/).

1. `docker compose up`
2. `cp dumps/nuremberg_prod_dump_2022-08-02.sqlite3.zip . && unzip nuremberg_prod_dump_2022-08-02.sqlite3`
3. `mv nuremberg_prod_dump_2022-08-02.sqlite3 web/nuremberg_dev.db`
4. `docker compose cp solr_conf/ solr:/opt/solr-8.11.2/solr_conf`
5. `docker compose exec solr cp -r /opt/solr-8.11.2/solr_conf /var/solr/data/nuremberg_dev`
6. `docker compose exec solr solr create_core -c nuremberg_dev -d solr_conf`
7. `docker compose exec web python manage.py rebuild_index`
8. `docker compose exec web python manage.py runserver 0.0.0.0:8000`

Then visit [localhost:8000](http://localhost:8000).

To run with production settings:
1. Set appropriate SECRET_KEY and ALLOWED_HOSTS env vars
2. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
3. `docker compose exec web ./manage.py compress`
4. `docker compose exec web ./manage.py collectstatic`

Then visit [localhost:8080](http://localhost:8080).


## Project Structure

The project is organized into several feature-oriented modules ("apps" in
Django parlance). Each module includes all URL routing, model and view code,
tests, templates, JavaScript code, and static assets for the corresponding
feature set:

- `nuremberg`: Top-level namespace for organizational purposes only.  `.core`:
- Top-level URL routing, test frameworks, base templates and middleware, and
- site-wide style files.  `.settings`: Environment-specific Django settings
- files.  `.content`: Files for static pages with project information, etc.
- `.documents`: Files for displaying digitized document images.
- `.transcripts`: Files for full-text transcripts and OCR documents.
- `.photographs`: Files for displaying images from the photographic archive.
- `.search`: Files for the search interface and API.

    This document covers the following topics:

- [Setting up a development environment](#setup) [Running the test
- suite](#testing) [Configuring project settings](#project-settings)
- [Data](#data) [Packaging static assets](#static-assets)


## Testing

Tests in the project are generally high-level integration acceptance tests that
exercise the full app stack in a deployed configuration. Since the app has the
luxury of running off of a largely static dataset, the test database is
persistent, greatly speeding up setup and teardown time.

### Running tests

Make sure you have initialized the database and solr index as described in [Setup](#setup) above. Then run:

```
docker compose exec web pytest
```

Pytest is configured in `pytest.ini` to run all files named `tests.py`.

There is also a Selenium suite to test the behavior of the document viewer
front-end. These tests take a while to run, don't produce coverage data, and
are relatively unreliable, so they aren't run as part of the default suite.
However they are still useful, as they exercise the full stack all the way
through image downloading and preloading. They can be run explicitly when
necessary.

```
docker compose exec web python pytest nuremberg/documents/browser_tests.py
```


## Project Settings

> NOTE: An example configuration used for the demo site on Heroku is in the
> [heroku](https://github.com/harvard-lil/nuremberg/tree/heroku) branch as
> `staging.py`.

Environment-specific Django settings live in the `nuremberg/settings`
directory, and inherit from `nuremberg.settings.generic`. The settings module
is configured by the `DJANGO_SETTINGS_MODULE` environment variable; the default
value is `nuremberg.settings.dev`.

Secrets (usernames, passwords, security tokens, nonces, etc.) should not be
placed in a settings file or committed into git. The proper place for these is
an environment variable configured on the host, and read via `os.environ`. If
they must live in a `.py` file, they should be included in the environment
settings file via an `import` statement and uploaded separately as part of the
deployment process.

(The only exception to this is the defaults used in the dev environment.)


## Data

Since it is expected that this app will host a largely static dataset, the Django admin is not enabled. Updates can be made directly in SQLite. Just ensure that any changes are reindexed by Solr.

A minimal admin interface can be manually enabled locally if desired in `core/urls.py`. For it to be operable, you will need to run migrations and use the Django management command to create an admin user for your use. If you choose to do so, make sure not to commit and deploy your changes!


## Solr

Solr indexes are defined in relevant `search_indexes.py` files, and additional
indexing configuration is in the
`search/templates/search_configuration/schema.xml` file used to generate
`solr_conf/schema.xml`.

### Starting fresh

To build a brand new Solr schema, run:

```
docker compose exec web python manage.py build_solr_schema
--configure-dir=solr_conf
```

This will generate both `schema.xml` and `solrconfig.xml` under the `solr_conf`
directory. To use the updated config files, run `docker compose down` to dispose of the existing solr container and `docker compose up -d` to start a fresh one.

### Reindexing

To rebuild the index contents, run:

```
docker compose exec web python manage.py rebuild_index
```

(It will take a couple of minutes to reindex fully.)

Do this any time you make changes to `search_indexes.py` or `schema.xml`.

In the past, when this site was under active development and more frequent reindexing was required, `manage.py update_index` was run via a `cron` script or similar to automate reindexing on a nightly or hourly
basis using `--age 24` or `--age 1`. (Note: This will restrict reindexing only
for indexes that have an `updated_at` field defined; currently, `photographs`
does not, but completely reindexing that model is fast anyway.)

For more fine-grained information on indexing progress, use `--batch-size 100 --verbosity 2` or similar.

### Deploying

The Solr schema must be maintained as part of the deploy process. When
deploying an updated schema, make sure you have generated and committed
new `schema.xml` and `solrconfig.xml` files using `manage.py build_solr_schema
--configure-dir=solr_conf`, and then run a complete reindexing.

> WARNING: Be cautious when doing this in production-- although in general
> reindexing will happen transparently and the site can continue to serve requests
> while reindexing is in progress, certain schema changes will cause a
> `SCHEMA-INDEX-MISMATCH` error that will cause search pages to crash until
> reindexing completes.


## Transcripts

There is a management command `manage.py ingest_transcript_xml` which reads a
file like `NRMB-NMT01-23_00512_0.xml` (or a directory of such files using `-d`)
and generates or updates the appropriate transcript, volume, and page models.
Since some values read out of the XML are stored in the database, re-ingesting
is the preferred way to update transcript data. If database XML is modified
directly, call `populate_from_xml` on the appropriate TranscriptPage model to
update date, page, and sequence number.

Remember to run `docker compose exec web python manage.py update_index transcripts` after ingesting XML to
enable searching of the new content.


## Static Assets

### CSS

CSS code is generated from `.less` files that live in
`nuremberg/core/static/styles`. The styles are built based on Bootstrap 3
mixins, but don't bundle any Bootstrap code directly to ensure a clean semantic
design.

Compilation is handled automatically by the `django-static-precompiler` module
while the development server is running.

### JavaScript

JavaScript code is organized simply. JS dependencies are in
`core/static/scripts`, and are simply included in `base.html`. App code is
modularized using `modulejs`, to ensure that only code in the module defined in
the relevant template is run.

The only significant JavaScript app is the document image loading, panning, and
zooming functionality implemented in `documents/scripts`. That functionality is
organized as a set of Backbone.js views and viewmodels. There is a smaller
amount of code in `transcripts` to handle infinite scrolling and page
navigation, which is implemented in pure jQuery. There are also a handful of
minor cosmetic features implemented in `search`.

In production, all site javascript is compacted into a single minified blob by
`compressor`. (The exception is the rarely-needed dependency `jsPDF`.)

### In Production

When deploying, you should run `docker compose exec web python manage.py compress` to bundle, minify and
compress CSS and JS files, and `docker compose exec web python manage.py collectstatic` to move the remaining
assets into `static/`. This folder should not be committed to git.

For deployment to Heroku, these static files will be served by the WhiteNoise
server. In other environments it may be appropriate to serve them directly with
Nginx or Apache. If necessary, the output directory can be controlled with an
environment-specific override of the `STATIC_ROOT` settings variable.

