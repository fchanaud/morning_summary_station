#!/bin/bash
set -e  # Exit on error

echo "Starting deployment process..."

# Ensure pip is up to date
echo "Updating pip..."
pip install --upgrade pip

# Install all dependencies again to be safe
echo "Installing dependencies..."
pip install -r requirements.txt 

# Explicitly install gunicorn
echo "Installing gunicorn..."
pip install gunicorn==21.2.0

# Export Python path to include current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if gunicorn is installed and in path
echo "Checking gunicorn installation..."
if command -v gunicorn &> /dev/null; then
    echo "Gunicorn found at: $(which gunicorn)"
else
    echo "Gunicorn not found in PATH, trying to use module..."
    python -m gunicorn.app.wsgiapp wsgi:app
    exit $?
fi

# Start the application
echo "Starting application with gunicorn..."
gunicorn --log-level debug wsgi:app 