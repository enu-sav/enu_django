#!/bin/bash
sudo service enu_django stop
echo `git log --pretty=format:'%h' -n 1` > commit
curdir=${PWD##*/}
(
cd ..
tar cvzf $curdir-`date --iso-8601`.tgz --exclude=.env $curdir
)
git pull
./manage.py makemigrations
./manage.py migrate
sudo service enu_django start
