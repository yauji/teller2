FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
#ADD . /code/
ADD teller2.tar.gz /code/
COPY entrypoint.sh /
#RUN /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

