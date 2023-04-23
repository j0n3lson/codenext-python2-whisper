FROM python:3.9

WORKDIR /server

COPY ./server /deploy/server

RUN pip install --no-cache-dir --upgrade -r /deploy/server/requirements.txt
