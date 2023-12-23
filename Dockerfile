# pull official base image
FROM --platform=linux/amd64 python:3.9.15-slim-buster

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . /app/

# Install cron
RUN apt-get update \
  && apt-get install -y cron vim

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Add crontab file in the cron directory
COPY app.cron /etc/cron.d/app-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/app-cron

# Apply cron job
RUN crontab /etc/cron.d/app-cron

# Run the command on container startup
CMD cron -f