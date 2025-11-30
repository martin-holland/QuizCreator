#!/bin/bash
# Script to run Flask app using Flask CLI with correct Python
cd "$(dirname "$0")"
./venv/bin/python -m flask run --port 5001
