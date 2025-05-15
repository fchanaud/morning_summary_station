const { google } = require('googleapis');
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// Get credentials from environment variables or .env file
const CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const REDIRECT_URI = process.env.GOOGLE_REDIRECT_URI || 'http://localhost:3000/oauth2callback';

// Verify credentials are available
if (!CLIENT_ID || !CLIENT_SECRET) {
  console.error('Error: Missing Google OAuth credentials');
  console.error('Make sure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set in your environment or .env file');
  process.exit(1);
}

// Configure OAuth2 client
const oauth2Client = new google.auth.OAuth2(
  CLIENT_ID,
  CLIENT_SECRET,
  REDIRECT_URI
);

// Define scopes - we only need read-only access for the morning summary
const scopes = [
  'https://www.googleapis.com/auth/calendar.readonly'
];

async function getRefreshToken() {
  return new Promise((resolve, reject) => {
    try {
      // Create server to handle OAuth callback
      const server = http.createServer(async (req, res) => {
        try {
          const queryParams = url.parse(req.url, true).query;
          
          if (queryParams.code) {
            // Get tokens from code
            const { tokens } = await oauth2Client.getToken(queryParams.code);
            console.log('\n=================');
            console.log('Refresh Token:', tokens.refresh_token);
            console.log('=================\n');
            console.log('Save this refresh token in your configuration!');
            
            // Create a config file with the token
            const configPath = path.join(__dirname, 'calendar_config.json');
            const config = {
              client_id: CLIENT_ID,
              client_secret: CLIENT_SECRET,
              refresh_token: tokens.refresh_token,
              redirect_uri: REDIRECT_URI
            };
            
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
            console.log(`Configuration saved to ${configPath}`);
            
            // Send success response
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(`
              <html>
                <head>
                  <title>Authentication Successful</title>
                  <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; text-align: center; }
                    h1 { color: #4CAF50; }
                    pre { background: #f5f5f5; padding: 15px; border-radius: 4px; text-align: left; }
                  </style>
                </head>
                <body>
                  <h1>Authentication Successful!</h1>
                  <p>You can close this window now.</p>
                  <p>Your refresh token has been saved to: ${configPath}</p>
                </body>
              </html>
            `);
            
            // Close server
            server.close();
            resolve(tokens);
          }
        } catch (error) {
          console.error('Error getting tokens:', error);
          res.writeHead(500, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <head>
                <title>Authentication Failed</title>
                <style>
                  body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; text-align: center; }
                  h1 { color: #F44336; }
                  pre { background: #f5f5f5; padding: 15px; border-radius: 4px; text-align: left; }
                </style>
              </head>
              <body>
                <h1>Authentication Failed</h1>
                <p>Please check console for errors.</p>
                <pre>${error.message}</pre>
              </body>
            </html>
          `);
          reject(error);
        }
      }).listen(3000, () => {
        // Generate auth url with offline access to get refresh token
        const authUrl = oauth2Client.generateAuthUrl({
          access_type: 'offline',
          scope: scopes,
          prompt: 'consent'  // Force consent screen to ensure refresh token
        });

        console.log('1. Copy this URL and paste it in your browser:');
        console.log('\n', authUrl, '\n');
        console.log('2. Follow the Google authentication process');
        console.log('3. Wait for the refresh token to appear here');
      });

    } catch (error) {
      console.error('Server creation error:', error);
      reject(error);
    }
  });
}

// Run the token retrieval
getRefreshToken().catch(console.error); 