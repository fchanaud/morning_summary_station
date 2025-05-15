#!/bin/bash

# Render build script
echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Set up calendar config
echo "Setting up Google Calendar configuration..."
node setup_calendar_config.js

# Test calendar script
echo "Testing calendar script setup..."
if [ -f ./integrations/google-calendar/calendar_config.json ]; then
  echo "Calendar config file created successfully."
else
  echo "Warning: Calendar config file not created properly."
fi

# Complete the build
echo "Build process complete!" 