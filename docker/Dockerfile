FROM python:3.6
#FROM python:2
#FROM python:3
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install -y swig libssl-dev dpkg-dev netcat-traditional
RUN apt-get install -y nginx
#RUN apt-get update && apt-get install -y libpq-dev python-dev gcc
RUN apt-get update && apt-get install -y libpq-dev python-dev-is-python3 gcc
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
RUN pip install uwsgi
RUN pip install six
#ADD . /code/
ADD teller2.tar.gz /code/

#RUN cp -r /code/teller2/* /code/

ADD uwsgi.ini /code/teller2

ADD teller2_nginx.conf /etc/nginx/conf.d/

ENV DB_PASSWORD=postgres
ENV POSTGRES_PORT_5432_TCP_ADDR=db
#ENV DB_PASSWORD=${DB_PASSWORD}
#ENV POSTGRES_PORT_5432_TCP_ADDR=${POSTGRES_PORT_5432_TCP_ADDR}
#RUN python /code/manage.py collectstatic --noinput
RUN python /code/teller2/manage.py collectstatic --noinput

COPY entrypoint.sh /
#RUN /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
