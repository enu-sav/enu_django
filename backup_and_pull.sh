#!/bin/bash
# aktualny priecinok musi byt pomenovany ako prislusna sluzba
# enu_django
# enu_django-dev

curdir=${PWD##*/}
dt=`date -I`

sudo service $curdir stop
./backup.sh
git pull
rm -f db.sqlite3
rm -rf zmluvy/migrations
./manage.py makemigrations zmluvy
./manage.py migrate
./manage.py loaddata dump-$dt.json
sudo service $curdir start
