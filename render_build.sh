#!/bin/bash

# Render build script
echo "Starting build process..."

# Install dependencies
pip install -r requirements.txt

# Set up calendar config
echo "Setting up Google Calendar configuration..."
node setup_calendar_config.js

# Complete the build
echo "Build process complete!" 