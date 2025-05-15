#!/bin/bash
set -e  # Exit on error

echo "Starting deployment process..."

# Ensure pip is up to date
echo "Updating pip..."
pip install --upgrade pip || { echo "Failed to update pip but continuing..."; }

# Install all dependencies with exact versions to avoid compatibility issues
echo "Installing dependencies with pinned versions..."
pip install -r requirements.txt --no-cache-dir || { echo "Error installing dependencies"; exit 1; }

# Export Python path to include current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Verify our environment
echo "Python version:"
python --version
echo "Installed packages:"
pip list

# Check if gunicorn is installed and in path
echo "Checking gunicorn installation..."
if command -v gunicorn &> /dev/null; then
    echo "Gunicorn found at: $(which gunicorn)"
    GUNICORN_CMD="gunicorn"
else
    echo "Gunicorn not found in PATH, trying to use module..."
    GUNICORN_CMD="python -m gunicorn.app.wsgiapp"
fi

# Start the application
echo "Starting application with wsgi..."
$GUNICORN_CMD wsgi:app --log-level debug 