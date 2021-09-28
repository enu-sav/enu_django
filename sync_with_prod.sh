#!/bin/bash
# aktualny priecinok musi byt rovnaky na remote serveri
# enu_django
# enu_django-dev

remote=enutana
remotename=samba
curdir=${PWD##*/}
dt=`date -I`

remote_django_dir=Django/enu_django
remote_data_dir=Django/enu_django/data
remote_dump=$remote_django_dir/dump-$dt.json

# dump database on remote
ssh $remote "cd $remote_django_dir; ./backup.sh"

sudo service $curdir stop
rsync $remote:$remote_dump .
#rm -rf data
rsync -avh $remote:$remote_data_dir .

rm -f db.sqlite3
./manage.py makemigrations zmluvy
./manage.py makemigrations uctovnictvo
./manage.py migrate
./manage.py loaddata dump-$dt.json
sudo service $curdir start
