#!/bin/bash

provider=$1
router=$2

rid="p${provider}r${router}v"

ssh_output1=$(ssh -o ConnectTimeout=5 "$rid" "cli-shell-api showCfg" 2>&1)
ssh_output2=$(ssh -o ConnectTimeout=5 "$rid" "ip route" 2>&1)
ssh_output3=$(ssh -o ConnectTimeout=5 "$rid" "ip rule" 2>&1)
ssh_output4=$(ssh -o ConnectTimeout=5 "$rid" "ip neigh show" 2>&1)
ssh_output5=$(ssh -o ConnectTimeout=5 "$rid" "ip -br addr show" 2>&1)
ssh_output6=$(ssh -o ConnectTimeout=5 "$rid" "ip -br link show" 2>&1)
ssh_output7=$(ssh -o ConnectTimeout=5 "$rid" "ip vrf show" 2>&1)

echo "Configuration of $rid:"
echo "$ssh_output1"
echo "------------------------------------------------------------------------------------------------------------------------"

echo "Routing Table of $rid:"
echo "$ssh_output2"
echo "------------------------------------------------------------------------------------------------------------------------"

echo "Routing Rules of $rid:"
echo "$ssh_output3"
echo "------------------------------------------------------------------------------------------------------------------------"

echo "ARP Table of $rid:"
echo "$ssh_output4"
echo "------------------------------------------------------------------------------------------------------------------------"

echo "IPs of $rid:"
echo "$ssh_output5"
echo "------------------------------------------------------------------------------------------------------------------------"

echo "Interfaces of $rid:"
echo "$ssh_output6"
echo "------------------------------------------------------------------------------------------------------------------------"

echo "VRF of $rid:"
echo "$ssh_output7"
echo "------------------------------------------------------------------------------------------------------------------------"