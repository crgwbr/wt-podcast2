FROM registry.gitlab.com/thelabnyc/python-geoip:3.8

WORKDIR /code

RUN apt-get update && \
    apt-get install -y ffmpeg

COPY server/ /code/
RUN poetry install --no-interaction --no-ansi

RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD "gunicorn -w 4 wtpodcast2.wsgi:application"
