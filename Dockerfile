FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul
USER root
RUN apt-get update
RUN apt-get install -y python3 python3-pip cron vim tzdata

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . /app/

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN python3 -m playwright install --with-deps chromium

COPY app.cron /etc/cron.d/app-cron

RUN chmod 0644 /etc/cron.d/app-cron
RUN crontab /etc/cron.d/app-cron

CMD python3 /app/get_paper.py && cron -f