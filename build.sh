#!/bin/bash
set -e  # Exit on error

echo "Starting build process..."

# Update pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!" 