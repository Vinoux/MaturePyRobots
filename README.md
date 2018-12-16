## MaturePyRobot 2017 [![Build Status](https://travis-ci.org/AlexAndriamahaleo/MaturePyRobots.svg?branch=master)](https://travis-ci.org/AlexAndriamahaleo/MaturePyRobots) [![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://github.com/AlexAndriamahaleo/MaturePyRobots/blob/championship_dev/LICENSE) [![PyPI - Python Version](https://img.shields.io/badge/Python-3.6.2-blue.svg)](https://www.python.org/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-9.6.5-blue.svg)](https://www.postgresql.org/) [![PyPI - Django Version](https://img.shields.io/badge/django%20version-1.11.5%2B-blue.svg)](https://docs.djangoproject.com/en/2.0/releases/1.11/)

## Pre-requirements

- Python 3 (recommended 3.6.2)
- PostgreSQL (9.6.5)
- Django (1.11.5+ recommended 1.11.6)
- Pillow: https://pillow.readthedocs.io/en/4.3.x/installation.html
Make sure you got some external libraries like zlib, libjpeg ... installed before you install Python3 if you plan to build your Python3 from source
Nb : For window, python3 use like python 

## Development

#### Install PostgreSQL

Recommend install PostgreSQL via docker: https://hub.docker.com/_/postgres/
~~~~
$ docker pull postgres
$ docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=yourpassword  --name postgres postgres
~~~~~

#### Install dependencies and initiate data ubuntu
Automate:
~~~~~
$./init.sh
~~~~~
OR manually:
~~~~~
$ pip3 install -r requirements.txt
$ python3 manage.py makemigrations
$ python3 manage.py migrate
$ python3 manage.py loaddata backend/fixtures/database.json
~~~~~

### Install dependencies and initiate data window 

Automate:
~~~~~
$./init.cmd

#### Configure database
- Edit  `WebPyRobot/development.py` file. Add:

~~~~
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'database_name',
        'USER': 'username',
        'PASSWORD': 'yourpostgrepassword',
        'HOST': 'db host',
        'PORT': 'db port',
    }
}
~~~~~

#### Run 

ubuntu :
~~~~
$ ./run.sh
~~~~
OR
~~~~~
$ python3 manage.py runserver
~~~~~
window :
~~~~
$./run.cmd
~~~~
The server will be available at http://127.0.0.1:8000/


## Deployment [![Nginx](https://img.shields.io/badge/Nginx-lastest-green.svg)](https://www.nginx.com/) [![Supervisor](https://img.shields.io/badge/Supervisor-lastest-green.svg)](http://supervisord.org/introduction.html) [![Redis](https://img.shields.io/badge/Redis-lastest-orange.svg)](https://redis.io/)

#### Pre-requirements
- Nginx (lastest version)
- Supervisor (lastest version)
- Redis

#### Deploy
Install Python3 and PostgreSQL on your server, don't forget to install Python development library (python-dev or python-devel) if you don't build Python from source

Install lastest Nginx: https://www.nginx.com/resources/admin-guide/installing-nginx-open-source/. Check `Installing From NGINX Repository
` section.

Install Supervisor:
~~~~
$ sudo apt-get install supervisor
~~~~
Install redis
~~~~
$ sudo apt-get install redis-server
~~~~

Push your code to the server

Edit WebPyRobot/production.py to add your database, secret key, Channels settings for production

Install dependencies and initiate data:
~~~~
$ ./init.sh
~~~~
Setup static files for Nginx
~~~~
$ python3 prod_manage.py collectstatic
~~~~
Edit configuration files in conf/ to match your server settings:

- `webpyrobot_channels_supervisord.conf` is the configuration file to keep the project running with `daphne` under the management of `supervisord`. It's also for managing Channels workers
- `webpyrobot_nginx.conf` is the  configuration file of the project in `nginx`

Start `supervisord` and `nginx`

~~~~
$ sudo systemctl service start supervisord
$ sudo systemctl service start nginx
~~~~

Enjoy your production!

