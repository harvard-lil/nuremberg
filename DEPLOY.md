# How to deploy with this branch

This branch is configured to deploy to a basic Heroku app with a single web dyno, and the Heroku ClearDB and Websolr addons enabled.

# Deployment steps

There are three important steps for deployment:

- Pushing code to Heroku
- Importing the Nuremberg database
- Indexing the database into Solr

# Pushing code to Heroku

To deploy,, you can simply push this `heroku` branch to Heroku.

You can set up Git using the [Heroku CLI instructions](https://devcenter.heroku.com/articles/git). After logging in to the CLI, you can create the Heroku remote, run:

```heroku git:remote -a <app name>```

This will create the remote `heroku` for you. Then you can deploy this branch simply by running

```git push heroku heroku:main```

This instructs git to push to the `heroku` remote, send the local `heroku` branch to the `main` branch on the remote. Heroku will then automatically build and deploy the new code.

# SQL Import

To seed the production database, retrieve the ClearDB database URL by running:

```heroku config -a [app name]```

Then, you can import the database dump directly from your local environment by running:

```mysql [CLEARDB_DATABASE_URL] < nuremberg_prod.sql```

# Reindexing Solr

After the database has been uploaded, you can reindex the Solr search engine.

If this is the first time configuring Solr, you must upload the Nuremberg config file. Go to the WebSolr control panel through Heroku. Go to "Configuration", and upload the `schema.xml` configuration file. (Other Solr hosts will have a similar process.) For Solr 4, use the `schema.xml` file from the project root. For Solr 8, upload the files from the `solr_conf` directory.

Once WebSolr has been configured, you can reindex the database by running:

```heroku run python manage.py rebuild_index```

IMPORTANT NOTE: On low-tier databases, this reindexing may use up the database request quota before fully indexing, leading the site to be unavailable until the quota resets. To get around this, you can instead run the reindexing locally by setting the `SOLR_REMOTE` environment variable to the `WEBSOLR_URL` from `heroku config`.

Follow the instructions in README to set up the local database. Then run

```SOLR_REMOTE=[websolr URL] python manage.py rebuild_index```

or, from docker:

```docker-compose exec -e SOLR_REMOTE=[websolr URL] web python manage.py rebuild_index --noinput```

This will run the reindexing from your _local_ database, while saving the index into the remote Solr instance. That will stop it from using up the request quota for the live site.

# Merging code into this branch

This deployment branch contains all settings and files needed to deploy to Heroku. To deploy, you'll want to merge master into this branch, then push it to Heroku.

```bash
git checkout heroku
git merge master
git push heroku heroku:main
git checkout master
```

You can commit changes to Heroku-specific configuration to this branch. Don't commit them to master, and don't commit anything else here. In particular, don't merge any commits from this branch back to master. As long as this branch only edits Heroku files, and master never does, there should never be any conflicts and things will be easy.
