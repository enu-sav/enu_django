#!/bin/bash
git pull
./manage.py makemigrations
./manage.py migrate
