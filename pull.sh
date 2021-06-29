#!/bin/bash
sudo service enu_django stop
echo `git log --pretty=format:'%h' -n 1` > commit
(
cd ..
tar cvzf enu_django-`date --iso-8601`.tgz enu_django
)
git pull
./manage.py makemigrations
./manage.py migrate
sudo service enu_django start
