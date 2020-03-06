#!/bin/bash
echo -e "\nMoving to root directory..."
cd ../..

echo -e "\n Removing blocks.json..."
rm data/blocks.json

echo -e "\nBuilding docker container image"
echo "-------------------------------"
docker build -q -t miblock:latest .

echo -e "\nCreating containers (port 5000 & 5001)"
echo "--------------------------------------"
docker run -p 5000:5000 -d miblock
docker run -p 5001:5000 -d miblock
