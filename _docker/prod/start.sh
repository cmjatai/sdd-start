#!/usr/bin/env bash

echo -e "\033[38;2;255;255;0;2m\033[1m====> StartPRD...\033[0m"

#/bin/bash wait-for-pg.sh "postgresql://backend_st1:backend_st1@backenddb:5432/backend"

change_env_file() {
    echo "[ENV FILE] change .env file..."

    if [ -f "${ROOT_HOME}/backend_data/secret.key" ]; then
        KEY=`cat ${ROOT_HOME}/backend_data/secret.key`
    else
        KEY=`python3 genkey.py`
        echo $KEY > ${ROOT_HOME}/backend_data/secret.key
    fi

    sed -i -E "s|^SECRET_KEY.+$|\n|g" ${ROOT_HOME}/backend_data/.env
    echo "SECRET_KEY = $KEY" >> ${ROOT_HOME}/backend_data/.env

    declare -A env_vars=(
        ["^DATABASE_URL_PRD.+$"]="DATABASE_URL_PRD = ${DATABASE_URL:=postgresql://${POSTGRES_USER:=startprod1}:${POSTGRES_PASSWORD:=startprod1}@${COMPOSE_PROJECT_NAME}-db:5432/${POSTGRES_DB:=startprod1}}"
        ["^SOLR_COLLECTIONS.+$"]="SOLR_COLLECTIONS = ${SOLR_COLLECTIONS:=${COMPOSE_PROJECT_NAME}_arq1,${COMPOSE_PROJECT_NAME}_arq2}"
        ["^SOLR_URL.+$"]="SOLR_URL = ${SOLR_URL:=http:\/\/startprod1:startprod1@${COMPOSE_PROJECT_NAME}-solr:8983}"
        ["^DEBUG.+$"]="DEBUG = ${DEBUG:=False}"
        ["^DJANGO_VITE_DEV_MODE.+$"]="DJANGO_VITE_DEV_MODE = ${DJANGO_VITE_DEV_MODE:=False}"
        ["^REDIS_HOST.+$"]="REDIS_HOST = ${REDIS_HOST:=${COMPOSE_PROJECT_NAME}-redis}"
        ["^FOLDER_DEBUG_CONTAINER.+$"]="FOLDER_DEBUG_CONTAINER = ${FOLDER_DEBUG_CONTAINER:=${HOME}}"
        ["^COMPOSE_PROJECT_NAME.+$"]="COMPOSE_PROJECT_NAME = ${COMPOSE_PROJECT_NAME:=${COMPOSE_PROJECT_NAME}}"
        ["^TZ.+$"]="TZ = ${TZ:=${TZ:=America/Sao_Paulo}}"
    )

    echo "" >> ${ROOT_HOME}/backend_data/.env
    for regex in "${!env_vars[@]}"; do
        sed -i -E "s|$regex|${env_vars[$regex]}|g" ${ROOT_HOME}/backend_data/.env
        key=$(echo "${env_vars[$regex]}" | cut -d' ' -f1)
        if ! grep -q "^$key" ${ROOT_HOME}/backend_data/.env; then
            echo "${env_vars[$regex]}" >> ${ROOT_HOME}/backend_data/.env
        fi
    done

    # Remover quebras de linhas sequenciais
    echo "" >> ${ROOT_HOME}/backend_data/.env
    sed -i -E ':a;N;$!ba;s/\n{3,}/\n\n/g' ${ROOT_HOME}/backend_data/.env
}

change_env_file

yes yes | python3 manage.py migrate

## SOLR
USE_SOLR="${USE_SOLR:=False}"
SOLR_URL="${SOLR_URL:=http://startprod1:startprod1@${COMPOSE_PROJECT_NAME}-solr:8983}"
SOLR_COLLECTIONS="${SOLR_COLLECTIONS:=${COMPOSE_PROJECT_NAME}_arq1,${COMPOSE_PROJECT_NAME}_arq2}"
NUM_SHARDS=${NUM_SHARDS:=1}
RF=${RF:=1}
MAX_SHARDS_PER_NODE=${MAX_SHARDS_PER_NODE:=1}
IS_ZK_EMBEDDED="${IS_ZK_EMBEDDED:=True}"

if [ "${USE_SOLR-False}" == "True" ] || [ "${USE_SOLR-False}" == "true" ]; then

    echo " "
    echo "Solr configurations"
    echo "==================="
    echo "URL: $SOLR_URL"
    echo "COLLECTION: $SOLR_COLLECTIONS"
    echo "NUM_SHARDS: $NUM_SHARDS"
    echo "REPLICATION FACTOR: $RF"
    echo "MAX SHARDS PER NODE: $MAX_SHARDS_PER_NODE"
    echo "ASSUME ZK EMBEDDED: $IS_ZK_EMBEDDED"
    echo "========================================="

    echo "running Solr script"
    /bin/bash wait-for-solr.sh $SOLR_URL
    CHECK_SOLR_RETURN=$?

    if [ $CHECK_SOLR_RETURN == 1 ]; then
        echo "Connecting to Solr..."

        if [ "${IS_ZK_EMBEDDED-False}" == "True" ] || [ "${IS_ZK_EMBEDDED-False}" == "true" ]; then
            ZK_EMBEDDED="--embedded_zk"
            echo "Assuming embedded ZooKeeper instalation..."
        fi

        python3 solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE $ZK_EMBEDDED
    else
        echo "Solr is offline, not possible to connect."
    fi

else
    echo "Solr support is not initialized."
fi


sleep 3

rm ${HOME}/logs/celery/*.pid
#celery multi start 16 -A backend -l INFO -Q:1-10 cq_arq -Q:11-12 cq_core -Q:13 cq_videos -Q:14 cq_base -Q:15-16 celery -c 2 --hostname=backendredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log
celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 --hostname=backendredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log

sleep 3

# Iniciar gunicorn primeiro
/bin/sh start_gunicorn.sh &

sleep 3

# Iniciar daphne
/bin/sh start_daphne.sh &

sleep 5

# Iniciar nginx
echo "Iniciando NGINX..."
/usr/sbin/nginx -g "daemon off;"
