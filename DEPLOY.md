# How to deploy with this branch

This deployment branch contains all settings and files needed to deploy to Heroku. To deploy, you'll want to merge master into this branch, then push it to Heroku.

```bash
git checkout heroku
git merge master
git push heroku heroku:master
git checkout master
```

You can commit changes to Heroku-specific configuration to this branch. Don't commit them to master, and don't commit anything else here. In particular, don't merge any commits from this branch back to master. As long as this branch only edits Heroku files, and master never does, there should never be any conflicts and things will be easy.
