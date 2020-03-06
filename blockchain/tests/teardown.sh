#!/bin/bash
echo -e "\nStoping and removing containers"
echo "-------------------------------"
for container_id in $(docker ps -qa)
do
	docker stop $container_id
done
docker rm $(docker ps -a -q)
