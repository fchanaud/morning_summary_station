#!/bin/bash
set -e  # Exit on error

echo "==================== DEPLOYMENT START ===================="
echo "Starting deployment process at $(date)"
echo "Environment: RENDER=${RENDER:-false}"
echo "Python path: $PYTHONPATH"
echo "Working directory: $(pwd)"
echo "Directory contents:"
ls -la

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

# Check for required environment variables
echo "Checking environment variables..."
[ -z "$OPENAI_API_KEY" ] && echo "WARNING: OPENAI_API_KEY is not set"
[ -z "$ACCUWEATHER_API_KEY" ] && echo "WARNING: ACCUWEATHER_API_KEY is not set"
[ -z "$GOOGLE_CLIENT_ID" ] && echo "WARNING: GOOGLE_CLIENT_ID is not set"
[ -z "$GOOGLE_CLIENT_SECRET" ] && echo "WARNING: GOOGLE_CLIENT_SECRET is not set"
[ -z "$REDIRECT_URI" ] && echo "WARNING: REDIRECT_URI is not set"

# Create directory for token if needed
if [ ! -d "/tmp" ]; then
  echo "Creating /tmp directory for token storage"
  mkdir -p /tmp
fi

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
$GUNICORN_CMD wsgi:app --log-level debug --capture-output --enable-stdio-inheritance

echo "==================== DEPLOYMENT END ====================" 