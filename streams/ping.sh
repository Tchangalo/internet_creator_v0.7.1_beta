#!/bin/bash

provider=$1
router=$2

for i in $(seq 1 ${router})
do
    rid="p${provider}r${i}v"
    echo "Pinging cloudflare.com from $rid"
    ssh "$rid" "ping -c 2 cloudflare.com"
    echo "------------------------------------------------------------------------------------------------------------------------"
done
