#!/bin/bash
# Ensure pip is up to date
pip install --upgrade pip

# Install gunicorn explicitly
pip install gunicorn==21.2.0

# Start the application
gunicorn app:app 