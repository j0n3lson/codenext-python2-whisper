FROM python:3.9

RUN apt update && \
    apt install -y \
    vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY ./ /deploy

RUN pip install --no-cache-dir --upgrade -r /deploy/requirements.txt
