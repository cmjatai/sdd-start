#!/bin/bash

docker exec stormdb psql -U sddstart -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'sddstart' AND pid <> pg_backend_pid();"
docker exec stormdb psql -U sddstart -d postgres -c "DROP DATABASE IF EXISTS sddstart;"
docker exec stormdb psql -U sddstart -d postgres -c "CREATE DATABASE sddstart WITH OWNER = sddstart ENCODING = 'UTF8' CONNECTION LIMIT = -1;"
