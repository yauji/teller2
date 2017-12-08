FROM python:3
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install -y swig libssl-dev dpkg-dev netcat
RUN apt-get install -y nginx
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
RUN pip install uwsgi
#ADD . /code/
ADD teller2.tar.gz /code/

#RUN cp -r /code/teller2/* /code/

ADD uwsgi.ini /code/teller2

ADD teller2_nginx.conf /etc/nginx/conf.d/

#RUN python /code/manage.py collectstatic --noinput
RUN python /code/teller2/manage.py collectstatic --noinput

COPY entrypoint.sh /
#RUN /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
