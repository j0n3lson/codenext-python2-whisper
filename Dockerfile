FROM python:3.9

WORKDIR /app

COPY ./app /deploy/app

RUN pip install --no-cache-dir --upgrade -r /deploy/app/requirements.txt
