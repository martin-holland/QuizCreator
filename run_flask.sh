#!/bin/bash
# Script to run Flask app with correct virtual environment
cd "$(dirname "$0")"
# Use venv Python directly to avoid shell alias issues
./venv/bin/python app.py
