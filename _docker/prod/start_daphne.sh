#!/bin/bash

NAME="BACKEND.asgi"
DJANGODIR=/var/project/backend
SOCKFILE=/var/project/backend/run/daphne.sock

DJANGO_SETTINGS_MODULE=backend.settings
DJANGO_ASGI_MODULE=backend.asgi

echo "Iniciando: $NAME. base: $DJANGODIR"

# Adicionar retry para maior robustez
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    daphne -u $SOCKFILE ${DJANGO_ASGI_MODULE}:application \
    --access-log /var/project/backend/logs/daphne_access.log -v1 && break

    echo "Falha ao iniciar Daphne, tentativa $(($RETRY_COUNT + 1)) de $MAX_RETRIES"
    RETRY_COUNT=$(($RETRY_COUNT + 1))
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Falha ao iniciar Daphne após $MAX_RETRIES tentativas"
    exit 1
fi