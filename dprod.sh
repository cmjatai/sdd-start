#!/usr/bin/env bash
# paramentro passado na linha de comando, ou padrão startprod1
COMPOSE_PROJECT_NAME=${1:-startprod1}
sudo docker compose -p $COMPOSE_PROJECT_NAME --env-file _docker/prod/.env -f _docker/prod/docker-compose.yaml down
USER=`whoami`
GROUP=`whoami`
sudo chown -R $USER:$GROUP .