#!/bin/bash

# find directory, where this script resides
SCRIPT_DIR=$( cd -- "$( dirname -- "$0" )" &> /dev/null && pwd )

# deploy Kafka infrastructure containers (zookeeper, broker and schema-registry)
# by passing the settings file, where docker image URLs are defined
docker compose --env-file $SCRIPT_DIR/../../../settings.conf -f "$SCRIPT_DIR/docker-compose.yml" up -d
