#!/bin/bash
clear
cd ../
echo -e '             _'
echo -e '          _-" "-._                _ ____  _            _'
echo -e '       _-"        "-,            (_)  _ \| |          | |'
echo -e '      |-._       _-"|   _ __ ___  _| |_) | | ___   ___| | __'
echo -e '      |   "--.,-"   |  |  _ '"'"' _ \| |  _ <| |/ _ \ / __| |/ /'
echo -e '      |       |     |  | | | | | | | |_) | | (_) | (__|   < '
echo -e '      |       |     |  |_| |_| |_|_|____/|_|\___/ \___|_|\_\'
echo -e '      +._     |  _-"'
echo -e '         "-.._|-"'

echo -e "\n>> Stopping and removing containers"
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
	echo -e ">> Docker @ port 50$i with name container$((i+1))"
	docker run --name container$((i+1)) -p 50$i:5000 -d miblock
done

sleep 1

echo -e ">> Initialising discover node '127.0.0.1:500'"
curl http://127.0.0.1:500/discovery/initialise
echo -e ""

echo -e ">> Running Performance Evaluation"
cd evaluation
python3 performance.py -n $1
