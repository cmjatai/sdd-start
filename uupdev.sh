#!/usr/bin/env bash

COMPOSE_PROJECT_NAME=${1:-startdev1}
sudo docker compose -p $COMPOSE_PROJECT_NAME --env-file _docker/dev/.env --progress=plain -f _docker/dev/docker-compose.yaml up --build -d