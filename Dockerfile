FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y python3 python3-pip cron vim

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . /app/

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN playwright install --with-deps chromium

# Add crontab file in the cron directory
COPY app.cron /etc/cron.d/app-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/app-cron

# Apply cron job
RUN crontab /etc/cron.d/app-cron

# Run the command on container startup
CMD python3 /app/get_paper.py && cron -f