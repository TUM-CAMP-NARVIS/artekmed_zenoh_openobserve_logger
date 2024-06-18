FROM python:3.11-bullseye
LABEL authors="Ulrich Eck"


RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends build-essential git cmake python-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
