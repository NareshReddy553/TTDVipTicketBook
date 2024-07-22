# FROM python:3.7
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED=1
# WORKDIR /Django
# COPY . /Django/
# RUN pip install --upgrade pip --no-cache-dir
# RUN pip install -r requirements.txt
# CMD ["python3","manage.py","runserver",]

# syntax=docker/dockerfile:1
FROM python:3.12.3

RUN  apt-get update

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code
COPY requirements.txt /code/

RUN pip install --upgrade pip --no-cache-dir
RUN pip install -r requirements.txt

COPY . /code/
# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8080
CMD ["/bin/sh", "-c", "python manage.py runserver  0.0.0.0:8080"]

