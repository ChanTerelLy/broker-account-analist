import django_heroku
from .base import *
WSGI_APPLICATION = 'baa.wsgi.application'
django_heroku.settings(locals())