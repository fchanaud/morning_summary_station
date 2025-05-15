/**
 * Setup script to generate calendar_config.json from environment variables
 * This script should be run by Render during the build/deploy process
 */

const fs = require('fs');
const path = require('path');

// Path to write the config file
const configPath = path.join(__dirname, 'integrations/google-calendar/calendar_config.json');

// Get the configuration from environment variables
const clientId = process.env.GOOGLE_CLIENT_ID;
const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
const refreshToken = process.env.GOOGLE_REFRESH_TOKEN;

// Check if we have the required environment variables
if (!clientId || !clientSecret) {
  console.error('Missing required environment variables: GOOGLE_CLIENT_ID and/or GOOGLE_CLIENT_SECRET');
  process.exit(1);
}

// Create a basic config object
const config = {
  installed: {
    client_id: clientId,
    client_secret: clientSecret,
    redirect_uris: ['http://localhost', 'https://morning-summary-station.onrender.com/oauth2callback'],
    token_uri: 'https://oauth2.googleapis.com/token',
    auth_uri: 'https://accounts.google.com/o/oauth2/auth',
  }
};

// Add refresh token if it exists
if (refreshToken) {
  config.refresh_token = refreshToken;
  console.log('Added refresh token to calendar config');
} else {
  console.warn('No refresh token provided. Calendar integration will require authentication.');
}

// Ensure the directory exists
const configDir = path.dirname(configPath);
if (!fs.existsSync(configDir)) {
  fs.mkdirSync(configDir, { recursive: true });
  console.log(`Created directory: ${configDir}`);
}

// Write the config file
try {
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log(`Successfully created calendar config at: ${configPath}`);
} catch (error) {
  console.error(`Error writing calendar config: ${error.message}`);
  process.exit(1);
} 