FROM python:3
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install -y swig libssl-dev dpkg-dev netcat
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
RUN pip install uwsgi
ADD uwsgi.ini /code/
#ADD . /code/
ADD teller2.tar.gz /code/

RUN python /code/teller2/manage.py collectstatic --noinput

COPY entrypoint.sh /
#RUN /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]


