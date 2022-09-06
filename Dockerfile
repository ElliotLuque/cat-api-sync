FROM python:3.9

RUN apt-get update && apt-get install cron -y -qq
WORKDIR /app

COPY script.py /app/script.py

RUN echo "0 0 * * SAT root python /app/script.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab

CMD [ "cron", "-f" ]
