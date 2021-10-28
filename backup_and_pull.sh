#!/bin/bash
# aktualny priecinok musi byt pomenovany ako prislusna sluzba
# enu_django
# enu_django-dev

curdir=${PWD##*/}
dt=`date -I`

sudo -k # make sure to ask for password on next sudo
if sudo true; then
    sudo service $curdir stop
else
    echo "sudo command failed, aborting script"
    exit 1
fi

./backup.sh
git pull
if [[ ! $(git pull) ]]; then  
    echo "git command failed, aborting script"
    exit 1
fi  

#rm -f db.sqlite3
#rm -rf zmluvy/migrations
#./manage.py makemigrations zmluvy  # not required if migrations are in git
#./manage.py makemigrations uctovnictvo # not required if migrations are in git
./manage.py migrate
#./manage.py loaddata dump-$dt.json
sudo service $curdir start
