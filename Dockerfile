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
RUN pip install -r requirements.txt
RUN playwright install --with-deps chromium
#RUN playwright install --with-deps webkit

COPY app.cron /etc/cron.d/app-cron

RUN chmod 0644 /etc/cron.d/app-cron
RUN chmod +x /app/get_paper.py
RUN crontab /etc/cron.d/app-cron

CMD python3 /app/get_paper.py && cron -f