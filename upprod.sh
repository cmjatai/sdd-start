#!/usr/bin/env bash

COMPOSE_PROJECT_NAME=${1:-startprod1}
sudo docker compose -p $COMPOSE_PROJECT_NAME --env-file _docker/prod/.env_prod_compose --progress=plain -f _docker/prod/docker-compose.yaml up --build -d