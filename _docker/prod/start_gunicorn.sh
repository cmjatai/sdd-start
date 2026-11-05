#!/usr/bin/env bash
NAME="BACKEND.wsgi"
DJANGODIR=/var/project/backend
SOCKFILE=/var/project/backend/run/gunicorn.sock
USER=`whoami`
GROUP=`whoami`

NUM_WORKERS=9
TIMEOUT=300
MAX_REQUESTS=1000

DJANGO_SETTINGS_MODULE=backend.settings
DJANGO_WSGI_MODULE=backend.wsgi

echo "Iniciando: $NAME. base: $DJANGODIR"

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --log-level info \
  --timeout $TIMEOUT \
  --workers $NUM_WORKERS \
  --max-requests $MAX_REQUESTS \
  --user $USER \
  --access-logfile /var/project/backend/logs/gunicorn_access.log \
  --error-logfile /var/project/backend/logs/gunicorn_error.log \
  --bind=unix:$SOCKFILE
