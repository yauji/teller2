#!/bin/bash


python3 ./manage.py makemigrations trans
python3 ./manage.py migrate
#python3 ./teller2/manage.py makemigrations trans
#python3 ./teller2/manage.py migrate
#python3 ./teller2/manage.py runserver 0.0.0.0:8000
#cd ./teller2
uwsgi --ini uwsgi.ini

exec "$@"
