#!/usr/bin/env bash
#!/usr/bin/env bash
sudo docker compose -f _docker/dev/docker-compose.yaml down

USER=`whoami`
GROUP=`whoami`
sudo chown -R $USER:$GROUP .

sudo docker compose -f _docker/dev/docker-compose.yaml up --build -d