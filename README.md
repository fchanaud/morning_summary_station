# Morning Summary Station

A simple backend service that provides personalized, enthusiastic morning summaries with weather forecasts and calendar events for your iOS Shortcut.

## Features

- Daily weather forecast from AccuWeather Core Weather API
- Calendar events from Google Calendar
- LOUD, enthusiastic, friendly summary message using OpenAI API
- Single API endpoint for iOS Shortcuts integration

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- AccuWeather Core Weather API key
- OpenAI API key
- Google Calendar API credentials
- A device to host the backend (Render, Replit, or local server)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/fchanaud/morning_summary_station.git
   cd morning_summary_station
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```
   # API Keys
   OPENAI_API_KEY=your_openai_api_key
   ACCUWEATHER_API_KEY=your_accuweather_api_key
   
   # Location Settings
   LOCATION=London
   ADDRESS=16 acer road, dalston - E83GX
   
   # Google Calendar Settings
   GOOGLE_CALENDAR_ID=primary
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

5. Set up Google Calendar API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Web application type)
   - Set the authorized redirect URI to `http://localhost:5000/oauth2callback`
   - Add your email as a test user
   - Copy the Client ID and Client Secret to your `.env` file

6. Run the application:
   ```bash
   python app.py
   ```

7. First-time setup: Visit `http://localhost:5000` in a browser and follow the OAuth flow to authorize Google Calendar access.

## iOS Shortcut Setup

Create a simple iOS Shortcut to trigger your morning summary:

1. Open the Shortcuts app on your iPhone
2. Tap the "+" button to create a new shortcut
3. Add a "Get Contents of URL" action:
   - Set the URL to your server's endpoint: `https://your-server-address/api/text_summary`
   - Method: GET
4. Add a "Speak Text" action:
   - Connect it to the output of the previous action
   - Configure voice settings as needed (select a louder, more energetic voice)
   - Optionally: Set pitch higher and rate faster for a more enthusiastic sound
5. Save the shortcut with a name like "Morning Summary"
6. Add it to your home screen:
   - Long press the shortcut in the Shortcuts app
   - Select "Add to Home Screen"
   - Choose an icon (like a sun or megaphone)

Now you'll have a single button on your home screen that when tapped will:
1. Connect to your server
2. Fetch your personalized morning summary
3. Speak it out loud in an enthusiastic voice

## Deployment

To deploy the application to a production server (Render, Replit, etc.):

1. Update the redirect URI in your Google Cloud Console to match your production URL
2. Update the `redirect_uris` in the `CLIENT_CONFIG` in `app.py`
3. Set all environment variables on your hosting platform
4. Deploy the application

## License

MIT
