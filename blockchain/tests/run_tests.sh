#!/bin/bash
clear

echo -e "\n\n>> Moving to root directory..."
cd ../..

echo -e ">> Removing blocks.json..."
rm data/blocks.json > /dev/null 2>&1

echo -e ">> Building docker container image"
docker build -q -t miblock:latest . > /dev/null 2>&1

echo -e ">> Creating containers (port 5000, 5001 & 5002)"
docker run -p 5000:5000 -d miblock > /dev/null 2>&1
docker run -p 5001:5000 -d miblock > /dev/null 2>&1
docker run -p 5002:5000 -d miblock > /dev/null 2>&1

sleep 3

echo -e ">> Moving to test directory..."
cd blockchain/tests

echo -e "\n\n==============================[REGISTER TESTS]=============================="
python3 test_register.py
echo -e "\n===============================[RECORD TESTS]==============================="
python3 test_records.py
echo -e "\n===============================[MINING TESTS]==============================="
python3 test_mining.py
echo -e "\n==============================[FINISHED TESTS]=============================="

sleep 3

echo -e "\n>> Stoping and removing containers"
for container_id in $(docker ps -qa)
do
 	docker stop $container_id > /dev/null 2>&1
done
docker rm $(docker ps -a -q)
