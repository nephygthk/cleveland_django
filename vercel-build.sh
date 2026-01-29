#!/bin/bash
set -e

# Upgrade pip
python3.9 -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Collect static files
python3.9 manage.py collectstatic --noinput
