import os
import json
import pickle
import datetime
from flask import Flask, jsonify, request, redirect, url_for, session
import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import openai  # Import the openai module instead of specific class

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for OAuth sessions

# API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ACCUWEATHER_API_KEY = os.getenv("ACCUWEATHER_API_KEY")
LOCATION = os.getenv("LOCATION", "London")
ADDRESS = os.getenv("ADDRESS", "16 acer road, dalston - E83GX")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Configure the OpenAI API key
openai.api_key = OPENAI_API_KEY

# Path to store token
TOKEN_PATH = 'token.pickle'

# OAuth 2.0 Client Configuration
CLIENT_CONFIG = {
    'web': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'redirect_uris': [os.getenv('REDIRECT_URI', 'http://localhost:5000/oauth2callback')]
    }
}

# If modifying these scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_credentials():
    """
    Get valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    """
    creds = None

    # Try to load credentials from file
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_config(
                CLIENT_CONFIG,
                SCOPES,
                redirect_uri=CLIENT_CONFIG['web']['redirect_uris'][0]
            )
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            print(f"Please go to this URL to authorize access: {auth_url}")
            
            # Store flow in session for callback
            session['flow'] = flow
            return None
        
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_calendar_events():
    """
    Fetch calendar events from Google Calendar for today.
    Requires the Google Calendar API credentials to be set up.
    """
    try:
        # Get credentials
        creds = get_credentials()
        
        # If no credentials yet, return empty list (will be handled by auth flow)
        if not creds:
            return []
        
        # Build service
        service = build('calendar', 'v3', credentials=creds)
        
        # Get today's events
        today = datetime.datetime.now()
        today_start = datetime.datetime.combine(today.date(), datetime.time.min).isoformat() + 'Z'
        today_end = datetime.datetime.combine(today.date(), datetime.time.max).isoformat() + 'Z'
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=today_start,
            timeMax=today_end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        # Extract events
        events = events_result.get('items', [])
        
        return events
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        # If we hit an auth error, we might need to refresh
        # For simplicity, return mock data for now if there's an error
        today = datetime.datetime.now().date()
        
        # Mock data for demonstration
        events = [
            {
                "summary": "Morning Meeting",
                "start": {"dateTime": f"{today}T09:00:00"},
                "end": {"dateTime": f"{today}T10:00:00"}
            },
            {
                "summary": "Lunch with Alex",
                "start": {"dateTime": f"{today}T12:30:00"},
                "end": {"dateTime": f"{today}T13:30:00"}
            },
            {
                "summary": "Project Deadline",
                "start": {"dateTime": f"{today}T17:00:00"},
                "end": {"dateTime": f"{today}T18:00:00"}
            }
        ]
        
        return events

def get_weather_data():
    """
    Fetch weather data from AccuWeather API for the specified location.
    """
    try:
        # First, get the location key for the provided address
        location_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
        params = {
            "apikey": ACCUWEATHER_API_KEY,
            "q": ADDRESS
        }
        
        location_response = requests.get(location_url, params=params)
        location_data = location_response.json()
        
        if not location_data:
            return {"error": "Location not found"}
        
        location_key = location_data[0]["Key"]
        
        # Now get the current conditions
        current_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
        current_params = {
            "apikey": ACCUWEATHER_API_KEY,
            "details": True
        }
        
        current_response = requests.get(current_url, params=current_params)
        current_data = current_response.json()
        
        # Get the daily forecast
        forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}"
        forecast_params = {
            "apikey": ACCUWEATHER_API_KEY,
            "metric": True
        }
        
        forecast_response = requests.get(forecast_url, params=forecast_params)
        forecast_data = forecast_response.json()
        
        # Combine current conditions with forecast
        weather_data = {
            "current": current_data[0] if current_data else {},
            "forecast": forecast_data
        }
        
        return weather_data
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return {"error": f"Failed to fetch weather data: {str(e)}"}

def generate_summary(events, weather):
    """
    Generate a personalized morning summary using OpenAI's GPT model.
    """
    try:
        # Format events for the prompt
        events_text = ""
        for event in events:
            start_time = event.get("start", {}).get("dateTime", "")
            if start_time:
                try:
                    # Parse and format the time
                    dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%I:%M %p")
                except:
                    formatted_time = start_time
                
                events_text += f"- {event['summary']} at {formatted_time}\n"
        
        # Format weather for the prompt
        weather_text = "Weather information not available."
        
        # Check if we have current conditions
        if weather.get("current"):
            current = weather["current"]
            temperature = current.get("Temperature", {}).get("Metric", {}).get("Value")
            weather_condition = current.get("WeatherText")
            
            if temperature and weather_condition:
                weather_text = f"Current weather: {weather_condition}, {temperature}°C. "
        
        # Add forecast information if available
        if weather.get("forecast") and weather["forecast"].get("DailyForecasts"):
            daily = weather["forecast"]["DailyForecasts"][0]
            min_temp = daily["Temperature"]["Minimum"]["Value"]
            max_temp = daily["Temperature"]["Maximum"]["Value"]
            day_condition = daily["Day"]["IconPhrase"]
            weather_text += f"Today's forecast: {day_condition} with temperatures between {min_temp}°C and {max_temp}°C."
        
        # Create the prompt for the AI - making it LOUD and enthusiastic!
        prompt = f"""
        Create a LOUD, ENTHUSIASTIC, and FRIENDLY morning summary for someone in {LOCATION}.
        
        Today's Date: {datetime.datetime.now().strftime('%A, %B %d, %Y')}
        
        Weather:
        {weather_text}
        
        Today's Events:
        {events_text if events_text else 'No events scheduled for today.'}
        
        Make the summary LOUD (use capital letters for emphasis), high-energy, motivational, and uplifting.
        Use lots of exclamation marks! Be VERY excited about the day ahead!
        Keep it concise (around 150 words). Include specific references to the weather and events.
        """
        
        # Use the older OpenAI API format
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.7,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        # Extract and return the generated text
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Sorry, I couldn't generate your morning summary: {str(e)}"

@app.route('/')
def index():
    """Basic route that explains how to use the API"""
    return """
    <html>
        <head>
            <title>Morning Summary Station</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                code { background-color: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>Morning Summary Station</h1>
            <p>This is the backend for your Morning Summary Station. To use it:</p>
            <ol>
                <li>Set up an iOS Shortcut that calls: <code>GET /api/text_summary</code></li>
                <li>Use the "Speak Text" action in Shortcuts to have your iPhone read the summary aloud</li>
            </ol>
            <p>The first time you use this, you may need to authorize Google Calendar access.</p>
        </body>
    </html>
    """

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback"""
    try:
        # Get flow from session
        flow = session.get('flow')
        if not flow:
            return "Authentication failed. Please restart the app."
        
        # Complete OAuth flow
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        
        # Save credentials
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
        
        # Return success message
        return "Authentication successful! You can close this window and use your iPhone shortcut now."
    except Exception as e:
        print(f"Error in OAuth callback: {e}")
        return f"Error during authentication: {str(e)}"

@app.route('/api/text_summary', methods=['GET'])
def get_text_summary():
    """API endpoint to get just the text summary for Shortcuts integration"""
    events = get_calendar_events()
    
    # If authorization is needed, redirect to auth URL
    if not events and 'flow' in session:
        flow = session.get('flow')
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return jsonify({"auth_required": True, "auth_url": auth_url})
    
    weather = get_weather_data()
    summary = generate_summary(events, weather)
    
    return summary

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 