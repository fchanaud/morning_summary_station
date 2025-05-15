# Google Calendar Integration

This directory contains the necessary files to integrate Google Calendar with the Morning Summary Station.

## Setup Instructions

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   * Go to "APIs & Services" > "Library"
   * Search for "Google Calendar API"
   * Click "Enable"

### 2. Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (unless you have a Google Workspace organization)
3. Fill in the required information:
   * App name
   * User support email
   * Developer contact information
4. Add the following scopes:
   * `https://www.googleapis.com/auth/calendar.readonly`
5. Add your email address as a test user

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop app" as the application type
4. Name your client (e.g., "Morning Summary Calendar Client")
5. Click "Create"
6. Download the client configuration file (you'll need the client ID and client secret)

### 4. Set Up Environment Variables

Create a `.env` file in the root directory of the project with the following content:

```
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/oauth2callback
```

Replace `your-client-id` and `your-client-secret` with the values from the OAuth client you created.

### 5. Install Dependencies

```bash
npm install
```

### 6. Get Refresh Token

Run the authorization script to get your refresh token:

```bash
npm run auth-calendar
```

Follow the instructions that appear in the console:
1. Copy the provided URL
2. Paste it into your browser
3. Complete the Google authentication process
4. The script will save your credentials in `calendar_config.json`

### 7. Test the Integration

Once you've set up the integration, you can test it by running:

```bash
node get_events.js
```

This should output your calendar events for today in JSON format.

## Troubleshooting

### Common Issues

1. **Authentication Error**:
   * Make sure your OAuth client ID and secret are correct
   * Check that you've added yourself as a test user
   * Verify you've enabled the Google Calendar API

2. **No Events Found**:
   * Check that you have events scheduled in your Google Calendar for today
   * Make sure you've granted the correct permissions during authorization

3. **Node.js Not Found**:
   * Install Node.js from [nodejs.org](https://nodejs.org/)

4. **Error Running Scripts**:
   * Make sure you're in the project root directory when running npm commands
   * Check that the scripts have execute permissions

## How It Works

This integration uses the Google Calendar API to fetch events from your calendar. It uses OAuth 2.0 for authentication, which allows the app to access your calendar data without storing your Google password.

The integration consists of:
- `getToken.js`: Script to obtain OAuth credentials
- `calendar_service.js`: Service that handles communication with the Google Calendar API
- `get_events.js`: Script that fetches and formats today's events

The Python app uses this integration by executing the `get_events.js` script and parsing its output. 