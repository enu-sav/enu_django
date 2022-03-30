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
#ssh $remote "cd $remote_django_dir; ./backup.sh"
#rsync $remote:$remote_dump .

sudo service $curdir stop
# synchronizovať súbory
rsync -avh $remote:$remote_data_dir .
# skopírovať databázu
scp $remote:$remote_django_dir/db.sqlite3 .
./manage.py migrate
#./manage.py loaddata dump-$dt.json
sudo service $curdir start
