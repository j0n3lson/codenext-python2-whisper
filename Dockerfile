FROM python:3.9

RUN apt update && \
    apt install -y \
    vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /server

COPY ./server /deploy/server

RUN pip install --no-cache-dir --upgrade -r /deploy/server/requirements.txt
