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

### Deploying to Render

1. Create a new account on [Render](https://render.com/) if you don't have one
2. From the Render dashboard, click on "New +" and select "Web Service"
3. Connect your GitHub repository or use the public GitHub URL
4. Configure the following settings:
   - **Name**: `morning-summary-station` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `bash start.sh`
   
5. Add the following environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `ACCUWEATHER_API_KEY`: Your AccuWeather API key
   - `LOCATION`: London (or your preferred location name)
   - `ADDRESS`: 16 acer road, dalston - E83GX (or your address)
   - `GOOGLE_CALENDAR_ID`: primary (or your specific calendar ID)
   - `GOOGLE_CLIENT_ID`: Your Google Client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google Client Secret

6. Click "Create Web Service"
7. Once deployed, update your Google OAuth settings:
   - Go to the Google Cloud Console
   - Add your Render URL with `/oauth2callback` as an authorized redirect URI
   - Example: `https://morning-summary-station.onrender.com/oauth2callback`
   
8. Update the `redirect_uris` in your deployed app:
   - Go to the Render dashboard, find your service
   - Go to "Environment" tab
   - Add a new environment variable:
   - `REDIRECT_URI`: https://morning-summary-station.onrender.com/oauth2callback

9. For the first-time auth flow:
   - Visit your app's URL in a browser
   - Follow the authorization steps once to grant calendar access

After deployment, update your iOS Shortcut with the new Render URL.

## License

MIT
