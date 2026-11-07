#!/usr/bin/env bash
# paramentro passado na linha de comando, ou padrão startdev1
COMPOSE_PROJECT_NAME=${1:-startdev1}
sudo docker compose -p $COMPOSE_PROJECT_NAME --env-file _docker/dev/.env -f _docker/dev/docker-compose.yaml down
USER=`whoami`
GROUP=`whoami`
sudo chown -R $USER:$GROUP .