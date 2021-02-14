release: python manage.py migrate
web: npm run serve
django: gunicorn baa.wsgi --bind=0.0.0.0:8000 --log-file -