#!/bin/bash


python3 ./teller2/manage.py make migrations trans
python3 ./teller2/manage.py migrate
python3 ./teller2/manage.py runserver 0.0.0.0:8000

exec "$@"
