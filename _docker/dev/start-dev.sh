#!/usr/bin/env bash

echo -e "\033[38;2;255;255;0;2m\033[1m====> StartDEV...\033[0m"

change_env_file() {
    echo "[ENV FILE] change .env file..."
    declare -A env_vars=(
        ["^DATABASE_URL_DEV.+$"]="DATABASE_URL_DEV = ${DATABASE_URL:=postgresql:\/\/backend:backend@projectdevdb:5432\/backend}"
        ["^SOLR_URL.+$"]="SOLR_URL = ${SOLR_URL:=http:\/\/solr:solr@projectdevsolr:8983}"
        ["^DEBUG.+$"]="DEBUG = ${DEBUG:=True}"
        ["^DJANGO_VITE_DEV_MODE.+$"]="DJANGO_VITE_DEV_MODE = ${DJANGO_VITE_DEV_MODE:=True}"
        ["^REDIS_HOST.+$"]="REDIS_HOST = ${REDIS_HOST:=projectdevredis}"
        ["^FOLDER_DEBUG_CONTAINER.+$"]="FOLDER_DEBUG_CONTAINER = ${FOLDER_DEBUG_CONTAINER:=${HOME}}"
    )

    echo "" >> backend/.env
    for regex in "${!env_vars[@]}"; do
        sed -i -E "s|$regex|${env_vars[$regex]}|g" backend/.env
        key=$(echo "${env_vars[$regex]}" | cut -d' ' -f1)
        if ! grep -q "^$key" backend/.env; then
            echo "${env_vars[$regex]}" >> backend/.env
        fi
    done

    # Remover quebras de linhas sequenciais
    echo "" >> backend/.env
    sed -i -E ':a;N;$!ba;s/\n{3,}/\n\n/g' backend/.env
}

change_env_file

yes yes | python3 manage.py migrate

## SOLR
USE_SOLR="${USE_SOLR:=False}"
SOLR_URL="${SOLR_URL:=http://solr:solr@projectdevsolr:8983}"
SOLR_COLLECTIONS="${SOLR_COLLECTIONS:=backend_arq1,backend_arq2}"
NUM_SHARDS=${NUM_SHARDS:=1}
RF=${RF:=1}
MAX_SHARDS_PER_NODE=${MAX_SHARDS_PER_NODE:=1}
IS_ZK_EMBEDDED="${IS_ZK_EMBEDDED:=True}"

if [ "${USE_SOLR-False}" == "True" ] || [ "${USE_SOLR-False}" == "true" ]; then

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
    /bin/bash _docker/prod/wait-for-solr.sh $SOLR_URL
    CHECK_SOLR_RETURN=$?

    if [ $CHECK_SOLR_RETURN == 1 ]; then
        echo "Connecting to Solr..."

        if [ "${IS_ZK_EMBEDDED-False}" == "True" ] || [ "${IS_ZK_EMBEDDED-False}" == "true" ]; then
            ZK_EMBEDDED="--embedded_zk"
            echo "Assuming embedded ZooKeeper instalation..."
        fi

        python3 _docker/prod/solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE $ZK_EMBEDDED

    else
        echo "Solr is offline, not possible to connect."
    fi

else
    echo "Solr support is not initialized."
fi

rm ${HOME}/logs/celery/*.pid
#celery multi start 16 -A backend -l INFO -Q:1-10 cq_arq -Q:11-12 cq_core -Q:13 cq_videos -Q:14 cq_base -Q:15-16 celery -c 2 --hostname=backendredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log
celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 --hostname=projectdevredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log

yes yes | python3 manage.py runserver 0.0.0.0:9000