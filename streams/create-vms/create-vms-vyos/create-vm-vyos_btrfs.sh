#!/bin/env bash

set -euo pipefail
while getopts c:n:p:r: flag
do
    case "${flag}" in
	c) command=${OPTARG};;
	n) node=${OPTARG};;
	p) provider=${OPTARG};;
	r) router=${OPTARG};;
    esac
done

echo "vmid:${node}0${provider}00${router} provider:${provider} router:${router}"

if [[ -n "${node+set}" && "${provider+set}" && "${router+set}" ]]
then
    vmid=${node}0${provider}0`printf '%02d' $router`
	mgmtmac=00:24:18:A${provider}:`printf '%02d' $router`:00

    case "${command}" in
	create)
	    vmid=${node}0${provider}0`printf '%02d' $router`
	    ## Create VM, import disk and define boot order
	    qm create $vmid --name "p${provider}r${router}v" --ostype l26 --memory 1664 --balloon 1664 --cpu cputype=host --cores 4 --scsihw virtio-scsi-single --net0 virtio,bridge=vmbr1001,macaddr="${mgmtmac}"
	    qm importdisk $vmid vyos-1.5.0-cloud-init-10G-qemu.qcow2 local-btrfs
	    qm set $vmid --virtio0 local-btrfs:$vmid/vm-$vmid-disk-0.raw
	    qm set $vmid --boot order=virtio0
	    	   
	    ## add interfaces to the router
	    for net in {1..4}
	    do
			if [[ ${provider} == 1 && ${router} == 9 && ${net} == 2 ]]
			then
				vlanid=1074
			elif [[ ${provider} == 2 && ${router} == 9 && ${net} == 2 ]]
			then
				vlanid=2074
			elif [[ ${provider} == 3 && ${router} == 9 && ${net} == 2 ]]
			then
				vlanid=3074
			else
				vlanid=$(/home/user/streams/vlans3.sh 8 2 ${router} ${net} ${provider})
			fi
			qm set $vmid --net${net} virtio,bridge=vmbr${provider},tag=${vlanid},macaddr=00:${node}4:18:F${provider}:`printf '%02d' $router`:`printf '%02d' $net`
	    done

	    ## Import seed.iso for cloud init
	    qm set $vmid --ide2 media=cdrom,file=local-btrfs:iso/seed.iso
	    #qm set $vmid --onboot 1
	    ;;

	destroy)
	    qm stop $vmid && qm destroy $vmid
	    ;;

	*)
	    echo "hi there, possible commands are create and destroy"
	    ;;
    esac

else
    echo "something went wrong"

fi



