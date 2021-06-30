#!/bin/bash
# aktualny priecinok musi byt pomenovany ako prislusna sluzba
# enu_django
# enu_django-dev

curdir=${PWD##*/}
dt=`date -I`

rm -rf dump*.json
rm -rf actual-commit*

echo `git log --pretty=format:'%h' -n 1` > actual-commit-on-$dt

echo Backing up database content to dump-$dt.json
./manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > dump-$dt.json

(
echo Archiving everything to backup/`pwd`/$dt
cd ..
tar czf backup/$curdir-$dt.tgz --exclude=.env $curdir
)
