#!/bin/bash

export ANSIBLE_HOST_KEY_CHECKING=False
export ANSIBLE_SSH_TIMEOUT=100

node=$1
provider=$2
destroy=$3
routers=$4
ansible_limit=$5
startdelay=$6
refresh=$7

C='\033[0;94m'
NC='\033[0m'

sleeping ()
{
    for r in $(seq 1 $2)
    do
	while sleep 5
	do
	    ansible -i ${HOME}/streams/ansible/inventories/inventory${provider}.yaml p$1r${r}v -m ping -u vyos | grep -q pong && break
	done
	echo -e "${C}Router ${r} is running${NC}"
    done
}

#destroy and recreate vms
cd ${HOME}/streams/create-vms/create-vms-vyos/

#destroy
if [ $destroy == 1 ]
   then
       echo -e "${C}Destroying VMs${NC}"
       for r in $(seq 1 ${routers})
       do
	   sudo qm stop ${node}0${provider}00${r}
	   sudo bash create-vm-vyos_btrfs.sh -c destroy -n ${node} -p ${provider} -r ${r}
       done
fi

#create
echo -e "${C}Creating VMs${NC}"
for r in $(seq 1 $4)
do
	if [[ $(df -T / | awk 'NR==2 {print $2}') == "zfs" ]]
	then
	sudo bash create-vm-vyos_zfs.sh -c create -n ${node} -p ${provider} -r ${r} 
	else
	sudo bash create-vm-vyos_btrfs.sh -c create -n ${node} -p ${provider} -r ${r}
	fi  
done

#start and ssh-keygen
echo -e "${C}Starting VMs and ssh-keygen${NC}"
for r in $(seq 1 ${routers})
do
    sudo qm start ${node}0${provider}00${r}
    ssh-keygen -f "${HOME}/.ssh/known_hosts" -R "10.20.30.${provider}${r}"
    sleep $6
done

#sleeping
echo -e "${C}Waiting for first boot${NC}"
sleeping $provider $routers

#upgrade
if [ "${refresh}" == "1" ]
then
	cd ${HOME}/streams/ansible
	rm -rf vyos-files
	mkdir vyos-files
	cd vyos-files

	download_url=$(curl -s https://api.github.com/repos/vyos/vyos-nightly-build/releases/latest | jq -r ".assets[0].browser_download_url")

	echo -e "${C}Waiting for download of latest Vyos version into /home/user/streams/ansible/vyos-files to complete ...${NC}"
	if curl -LO "$download_url" 
	then
		echo -e "${C}Download completed successfully${NC}"
	else
		echo -e "${NC}Download failed. Exiting script${NC}"
		exit 1
	fi
fi

cd ${HOME}/streams/ansible
echo -e "${C}System upgrade${NC}"
ansible-playbook -i inventories/inventory${provider}.yaml vyos_upgrade.yml -e "vyos_version=$(ls -t ${HOME}/streams/ansible/vyos-files/ | head -n 1 | sed -e 's/^vyos-//' | sed -e 's/-amd.*$//')" $ansible_limit

#reboot
echo -e "${C}Second boot${NC}"
echo -e "${C}Shutting down VMs${C}"
sudo  bash ${HOME}/streams/ks/shutdown_isp$2.sh $4
echo -e "${C}Restarting VMs${NC}"
sudo  bash ${HOME}/streams/ks/start_isp$2.sh $4 $6

#sleeping
echo -e "${C}Waiting for second boot${NC}"
sleeping $provider $routers

#configuring
echo -e "${C}Configuring network${NC}"
ansible-playbook -i inventories/inventory${provider}.yaml setup.yml $ansible_limit

#delete cdrom
echo -e "${C}Deleting cdrom${NC}"
for r in $(seq 1 ${routers})
do
    sudo qm set ${node}0${provider}00${r} --delete ide2
done

#reboot
echo -e "${C}Final reboot${NC}"
sleep 3
echo -e "${C}Shutting down VMs${NC}"
sudo  bash ${HOME}/streams/ks/shutdown_isp$2.sh $4
echo -e "${C}Final restart${NC}"
sudo bash ${HOME}/streams/ks/start_isp$2.sh $4 $6

echo -e "${C}All done. Wait a minute until the network is running.${NC}"
