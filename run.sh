#!/bin/bash

# Switch to the docker directory
cd `dirname $0`
cd Docker

# Spin  up containers
docker-compose up -d

# Switch to the script directory
cd ..

# Create venv and install requirements
python3 -m venv venv
pip3 install -r sec_dl/requirements.txt

clear

# activate venv
source venv/bin/activate

# run package
python3 -m sec_dl.main
