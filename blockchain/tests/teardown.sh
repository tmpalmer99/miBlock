#!/bin/bash

echo -e "\n>> Stoping and removing containers"
for container_id in $(docker ps -qa)
do
 	docker stop $container_id > /dev/null 2>&1
done
docker rm $(docker ps -a -q)
