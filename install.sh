#!/bin/bash
sudo NEEDRESTART_MODE=a apt update
sudo NEEDRESTART_MODE=a apt install python3-pip -y
pip install -r requirements.txt