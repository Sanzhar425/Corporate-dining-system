release: python manage.py migrate --noinput
web: gunicorn dining_system.wsgi:application --bind 0.0.0.0:$PORT --workers 3
