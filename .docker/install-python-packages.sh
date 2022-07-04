#!/bin/bash
set -euo pipefail

source /venv/bin/activate

pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir wheel

cd /tmp  # Pipfile and Pipfile.lock are in /tmp

if [ "${DEV_MODE:-0}" == "1" ]
then
    # Install dev requirements
    pip install --no-cache-dir -r requirements.dev.txt
else
    # Install only prod requirements
    pip install --no-cache-dir -r requirements.txt
fi
