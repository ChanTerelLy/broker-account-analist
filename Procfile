release: python manage.py migrate
web: gunicorn baa.wsgi --bind=0.0.0.0:$PORT --log-file -