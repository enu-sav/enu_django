#!/bin/bash
# aktualny priecinok musi byt pomenovany ako prislusna sluzba
# enu_django
# enu_django-dev

curdir=${PWD##*/}
sudo service $curdir stop
echo `git log --pretty=format:'%h' -n 1` > commit

dt=`date -I`
echo Backing up database content to dump-$dt.json
./manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > dump-$dt.json

(
echo Archiving everything to `pwd`/$dt
cd ..
tar czf $curdir-$dt.tgz --exclude=.env $curdir
)
git pull
./manage.py makemigrations zmluvy
./manage.py migrate
./manage.py loaddata dump-$dt.json
sudo service $curdir start
