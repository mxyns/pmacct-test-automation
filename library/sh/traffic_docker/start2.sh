#!/bin/sh

PCAP_MOUNT_DIR="$1"
IP_ADDRESS="$2"

IP_OPT="--ip"
if [[ "$IP_ADDRESS" == *"::"* ]]; then
  IP_OPT="--ip6"
fi

# Runs a traffic reproducer container synchronously

if docker inspect traffic-reproducer-0 >/dev/null 2>&1; then
    echo "Container exists, removing it"
    docker rm traffic-reproducer-0
fi

echo "Starting traffic container with mounted folder: $1"
docker run -v ${PCAP_MOUNT_DIR}:/pcap \
          --network pmacct_test_network \
          $IP_OPT $IP_ADDRESS \
          --name traffic-reproducer-0 \
          traffic-reproducer
