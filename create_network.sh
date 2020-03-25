#!/bin/bash
clear

echo -e '             _'
echo -e '          _-" "-._                _ ____  _            _'
echo -e '       _-"        "-,            (_)  _ \| |          | |'
echo -e '      |-._       _-"|   _ __ ___  _| |_) | | ___   ___| | __'
echo -e '      |   "--.,-"   |  |  _ '"'"' _ \| |  _ <| |/ _ \ / __| |/ /'
echo -e '      |       |     |  | | | | | | | |_) | | (_) | (__|   < '
echo -e '      |       |     |  |_| |_| |_|_|____/|_|\___/ \___|_|\_\'
echo -e '      +._     |  _-"'
echo -e '         "-.._|-"'

echo -e "\n>> Stoping and removing containers"
for container_id in $(docker ps -qa)
do
 	docker stop $container_id > /dev/null 2>&1
done
docker rm $(docker ps -a -q) > /dev/null 2>&1

echo -e ">> Removing blocks.json"
rm data/blocks.json > /dev/null 2>&1

echo -e ">> Building docker container image"
docker build -t miblock:latest . > /dev/null 2>&1

echo -e ">> Creating $1 docker container(s)"
for (( i=0; i<$1; i++ ))
do
	echo -e ">> Docker @ port 500$i with name container$((i+1))"
	docker run --name container$((i+1)) -p 500$i:5000 -d miblock
done

sleep 1

echo -e ">> Initialising discover node '127.0.0.1:5000'"
curl http://127.0.0.1:5000/discovery/initialise
echo -e ""

echo -e ">> Running client"
cd demo/
clear
python3 client.py -n $1
