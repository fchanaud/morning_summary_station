import os
import json
import pickle
import datetime
import logging
import uuid
import base64
from flask import Flask, jsonify, request, redirect, url_for, session
import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import openai  # Import the openai module instead of specific class

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))  # Needed for OAuth sessions

# API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ACCUWEATHER_API_KEY = os.getenv("ACCUWEATHER_API_KEY")
LOCATION = os.getenv("LOCATION", "London")
ADDRESS = os.getenv("ADDRESS", "16 acer road, dalston - E83GX")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Log configuration at startup (excluding sensitive values)
logger.info(f"Starting with: LOCATION={LOCATION}, ADDRESS={ADDRESS}, GOOGLE_CALENDAR_ID={GOOGLE_CALENDAR_ID}")
logger.info(f"OpenAI API Key configured: {'Yes' if OPENAI_API_KEY else 'No'}")
logger.info(f"AccuWeather API Key configured: {'Yes' if ACCUWEATHER_API_KEY else 'No'}")

# Configure the OpenAI API key
openai.api_key = OPENAI_API_KEY

# Path to store token - check if using Render and use appropriate path
if os.getenv('RENDER'):
    # On Render, use a persistent volume path if available, otherwise fall back to tmp
    TOKEN_PATH = os.getenv('PERSISTENT_STORAGE_DIR', '/tmp') + '/token.pickle'
    logger.info(f"Running on Render, token path: {TOKEN_PATH}")

    # Set the redirect URI for production environment
    REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://morning-summary-station.onrender.com/oauth2callback')
    logger.info(f"Using production redirect URI: {REDIRECT_URI}")
else:
    TOKEN_PATH = 'token.pickle'
    logger.info(f"Running locally, token path: {TOKEN_PATH}")
    
    # Set the redirect URI for local development
    REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/oauth2callback')
    logger.info(f"Using local redirect URI: {REDIRECT_URI}")

# Dictionary to store OAuth flow states
# This allows us to recover the flow even if the session is lost
oauth_flows = {}

# OAuth 2.0 Client Configuration
CLIENT_CONFIG = {
    'web': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'redirect_uris': [REDIRECT_URI]
    }
}

# Check if OAuth credentials are properly configured
if not CLIENT_CONFIG['web']['client_id'] or not CLIENT_CONFIG['web']['client_secret']:
    logger.warning("Google OAuth client credentials not properly configured!")

logger.info(f"Configured OAuth redirect URI: {CLIENT_CONFIG['web']['redirect_uris'][0]}")

# If modifying these scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_credentials():
    """
    Get valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    """
    creds = None
    
    # Make sure the token directory exists
    token_dir = os.path.dirname(TOKEN_PATH)
    if token_dir and not os.path.exists(token_dir):
        try:
            os.makedirs(token_dir)
            logger.info(f"Created token directory: {token_dir}")
        except Exception as e:
            logger.error(f"Failed to create token directory: {e}")

    # Try to load credentials from file
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
            logger.info("Successfully loaded credentials from token file")
            
            # Additional check for credential validity - force refresh if close to expiry
            if creds and hasattr(creds, 'expiry'):
                now = datetime.datetime.now()
                expiry = creds.expiry
                # If expiry is less than 1 hour away, try to refresh
                if expiry and (expiry - now).total_seconds() < 3600:
                    logger.info("Credentials close to expiry, attempting refresh")
                    creds.refresh(Request())
                    # Save refreshed credentials
                    with open(TOKEN_PATH, 'wb') as token:
                        pickle.dump(creds, token)
                    logger.info("Refreshed and saved credentials")
            
        except Exception as e:
            logger.error(f"Error loading or refreshing credentials from token file: {e}")
            creds = None
    else:
        logger.info(f"Token file not found at {TOKEN_PATH}")

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        logger.info("Credentials not valid, starting OAuth flow")
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Successfully refreshed credentials")
                
                # Save the refreshed credentials
                with open(TOKEN_PATH, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Saved refreshed credentials")
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                creds = None
        else:
            try:
                # Create a new flow
                flow = Flow.from_client_config(
                    CLIENT_CONFIG,
                    SCOPES,
                    redirect_uri=CLIENT_CONFIG['web']['redirect_uris'][0]
                )
                
                # Generate a unique state parameter
                state = str(uuid.uuid4())
                
                # Store the flow in our dictionary with the state as the key
                oauth_flows[state] = flow
                logger.info(f"Created new OAuth flow with state: {state}")
                
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent',
                    state=state,  # Use our state parameter
                )
                logger.info(f"Generated authorization URL: {auth_url[:50]}...")
                print(f"Please go to this URL to authorize access: {auth_url}")
                
                # Also store in session as a backup
                session['oauth_state'] = state
                
                return None
            except Exception as e:
                logger.error(f"Error setting up OAuth flow: {e}")
                # Return None to indicate auth is needed
                return None
        
        # Save the credentials for the next run
        try:
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
            logger.info(f"Saved credentials to {TOKEN_PATH}")
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
    return creds

def get_calendar_events():
    """
    Fetch calendar events from Google Calendar for today.
    First tries to use the MCP integration, falls back to OAuth if that fails.
    """
    try:
        # Try to use the MCP integration first
        import subprocess
        import json
        import os
        
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "integrations/google-calendar/get_events.js")
        
        # Check if the script exists and use it if possible
        if os.path.exists(script_path):
            try:
                result = subprocess.run(["node", script_path], 
                                      capture_output=True, text=True, check=True)
                events = json.loads(result.stdout)
                logger.info(f"Successfully retrieved {len(events)} events from MCP calendar integration")
                
                # Transform events to match expected format
                transformed_events = []
                for event in events:
                    # Convert to the format expected by the rest of the code
                    transformed_event = {
                        "summary": event.get("summary", "Untitled Event"),
                        "start": {
                            "dateTime": event.get("start")
                        },
                        "end": {
                            "dateTime": event.get("end")
                        }
                    }
                    transformed_events.append(transformed_event)
                
                return transformed_events
            except Exception as e:
                logger.warning(f"MCP calendar integration failed: {e}, falling back to OAuth")
                # Fall back to OAuth method
                pass
        
        # Original OAuth method as fallback
        logger.info("Using OAuth method for calendar events")
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
        logger.error(f"Error fetching calendar events: {e}")
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
        
        # Check if we have any events
        if events:
            # Check if events are in the MCP format or the OAuth format
            if isinstance(events[0], dict) and 'formattedTime' in events[0]:
                # MCP format - already formatted nicely
                for event in events:
                    events_text += f"- {event['summary']} at {event['formattedTime']}\n"
            else:
                # Original OAuth format - needs parsing
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
        
        # Create a more concise prompt for the AI to reduce token usage
        prompt = f"""Create a brief but enthusiastic morning summary for someone in {LOCATION}.
Date: {datetime.datetime.now().strftime('%A, %B %d')}
Weather: {weather_text}
Events: {events_text if events_text else 'No events today.'}

Make it ENERGETIC, upbeat and SHORT (max 100 words). Use CAPS for emphasis. Include weather and events info."""
        
        logger.debug("Sending request to OpenAI API")
        
        # Verify openai.api_key is set
        if not openai.api_key:
            logger.error("OpenAI API key not configured")
            return "Error: OpenAI API key not configured. Please check your environment variables."
        
        try:
            # First try with ChatCompletion (newer API version)
            try:
                # Try the ChatCompletion API (newer model)
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an enthusiastic personal assistant that creates brief, energetic morning summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=250,  # Reduced from 500 to save costs
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                summary = response.choices[0].message.content.strip()
                logger.debug(f"Generated summary with gpt-3.5-turbo, length: {len(summary)}")
            except (AttributeError, TypeError) as e:
                # Fall back to the older Completion API if ChatCompletion isn't available
                logger.warning(f"ChatCompletion API not available: {e}. Falling back to Completion API")
                response = openai.Completion.create(
                    model="gpt-3.5-turbo-instruct",  # Use the instruct model which is similar to text-davinci-003
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=250,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                summary = response.choices[0].text.strip()
                logger.debug(f"Generated summary with gpt-3.5-turbo-instruct, length: {len(summary)}")
            
            return summary
            
        except Exception as openai_error:
            logger.error(f"OpenAI API error: {openai_error}")
            # Try fallback to a simpler message
            return f"""
            GOOD MORNING!! 
            
            It's {datetime.datetime.now().strftime('%A, %B %d, %Y')}!
            
            I couldn't generate your full summary due to an API error, but I hope you have an AMAZING day anyway!
            
            Error details: {str(openai_error)}
            """
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
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
                .note { background-color: #fffde7; padding: 15px; border-left: 4px solid #ffd600; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>Morning Summary Station</h1>
            <p>This is the backend for your Morning Summary Station. To use it:</p>
            <ol>
                <li>Set up an iOS Shortcut that calls: <code>GET /api/text_summary</code></li>
                <li>Use the "Speak Text" action in Shortcuts to have your iPhone read the summary aloud</li>
            </ol>
            <div class="note">
                <strong>Note:</strong> This application is in testing mode. To use it, you must be added as a test user in the 
                Google Cloud Console. Please contact the administrator if you need access.
            </div>
            <p>The first time you use this, you may need to authorize Google Calendar access.</p>
        </body>
    </html>
    """

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback"""
    try:
        logger.info("OAuth callback received with URL: " + request.url)
        
        # Get the state parameter from the request
        state = request.args.get('state')
        if not state:
            logger.error("No state parameter in OAuth callback")
            return "Authentication failed: Missing state parameter. Please restart the app."
        
        logger.info(f"Received callback with state: {state}")
        
        # Try to get the flow from our dictionary using the state
        flow = oauth_flows.get(state)
        
        # If not found in the dictionary, try from session as backup
        if not flow and session.get('oauth_state') == state:
            try:
                logger.info("Recreating flow from scratch using state from session")
                flow = Flow.from_client_config(
                    CLIENT_CONFIG,
                    SCOPES,
                    redirect_uri=CLIENT_CONFIG['web']['redirect_uris'][0]
                )
            except Exception as flow_error:
                logger.error(f"Failed to recreate flow: {flow_error}")
        
        if not flow:
            logger.error(f"No flow found for state: {state}")
            return f"""
            <html>
                <head>
                    <title>Authentication Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }}
                        h1 {{ color: #F44336; }}
                        pre {{ background: #f5f5f5; padding: 10px; text-align: left; overflow: auto; }}
                    </style>
                </head>
                <body>
                    <h1>Authentication Failed</h1>
                    <p>No authentication flow was found for your session state ({state}).</p>
                    <p>Please try again by returning to the main page and starting over.</p>
                </body>
            </html>
            """
        
        # Complete OAuth flow
        try:
            authorization_response = request.url
            logger.info(f"Processing authorization response: {authorization_response[:100]}...")
            
            flow.fetch_token(authorization_response=authorization_response)
            creds = flow.credentials
            logger.info("Successfully obtained credentials from OAuth flow")
            
            # Ensure we request a refresh token to avoid future auth requirements
            if not creds.refresh_token:
                logger.warning("No refresh token in credentials, future reauthorization may be required")
            else:
                logger.info("Refresh token obtained, which should prevent future auth prompts")
            
            # Clean up the used flow
            if state in oauth_flows:
                del oauth_flows[state]
                logger.info(f"Removed flow with state: {state} from storage")
        except Exception as token_error:
            logger.error(f"Error fetching token: {token_error}")
            return f"""
            <html>
                <head>
                    <title>Authentication Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }}
                        h1 {{ color: #F44336; }}
                        pre {{ background: #f5f5f5; padding: 10px; text-align: left; overflow: auto; }}
                    </style>
                </head>
                <body>
                    <h1>Authentication Error</h1>
                    <p>There was an error processing your authentication:</p>
                    <pre>{str(token_error)}</pre>
                    <p>Please try again. If the problem persists, contact the administrator.</p>
                    <p><a href="/">Return to home page</a></p>
                </body>
            </html>
            """
        
        # Save credentials
        try:
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Successfully saved credentials to token file")
        except Exception as token_save_error:
            logger.error(f"Error saving token: {token_save_error}")
            return f"""
            <html>
                <head>
                    <title>Authentication Warning</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }}
                        h1 {{ color: #FF9800; }}
                    </style>
                </head>
                <body>
                    <h1>Authentication Partially Successful</h1>
                    <p>You were authenticated successfully, but we couldn't save your credentials for future use.</p>
                    <p>Error details: {str(token_save_error)}</p>
                    <p>You may need to authenticate again next time.</p>
                    <p><a href="/api/text_summary">Continue to your summary</a></p>
                </body>
            </html>
            """
        
        # Remove state from session
        session.pop('oauth_state', None)
        
        # Return success message
        return """
        <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }
                    h1 { color: #4CAF50; }
                    p { font-size: 18px; }
                    .button { 
                        display: inline-block; 
                        background-color: #4CAF50; 
                        color: white; 
                        padding: 10px 20px; 
                        text-decoration: none; 
                        border-radius: 4px; 
                        margin-top: 20px; 
                    }
                </style>
            </head>
            <body>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and use your iPhone shortcut now.</p>
                <p>Your Morning Summary Station is ready to go!</p>
                <a href="/api/text_summary" class="button">Get Your Summary Now</a>
            </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        return f"""
        <html>
            <head>
                <title>Authentication Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }}
                    h1 {{ color: #F44336; }}
                    p {{ font-size: 18px; }}
                    .error {{ background: #ffebee; padding: 10px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>Authentication Error</h1>
                <p>There was an error during authentication:</p>
                <p class="error">{str(e)}</p>
                <p>Please try again later.</p>
                <p><a href="/">Return to home page</a></p>
            </body>
        </html>
        """

@app.route('/api/text_summary', methods=['GET'])
def get_text_summary():
    """API endpoint to get just the text summary for Shortcuts integration"""
    try:
        logger.info("Received request to /api/text_summary")
        
        # Verify API keys are available
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key is not configured")
            return jsonify({"error": "OpenAI API key is not configured"}), 500
            
        if not ACCUWEATHER_API_KEY:
            logger.error("AccuWeather API key is not configured")
            return jsonify({"error": "AccuWeather API key is not configured"}), 500
        
        # Get calendar events with error handling
        try:
            events = get_calendar_events()
            logger.info(f"Retrieved {len(events)} calendar events")
        except Exception as e:
            logger.error(f"Error retrieving calendar events: {e}")
            events = []
        
        # Check if we need authorization
        if not events:
            # Handle authorization
            try:
                # Create a new flow
                flow = Flow.from_client_config(
                    CLIENT_CONFIG,
                    SCOPES,
                    redirect_uri=CLIENT_CONFIG['web']['redirect_uris'][0]
                )
                
                # Generate a unique state parameter
                state = str(uuid.uuid4())
                
                # Store the flow in our dictionary with the state as the key
                oauth_flows[state] = flow
                logger.info(f"Created new OAuth flow with state: {state} for /api/text_summary")
                
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent',
                    state=state,  # Use our state parameter
                )
                
                # Also store in session as a backup
                session['oauth_state'] = state
                
                logger.info(f"Generated auth URL with state: {state}")
                
                # Return just the auth URL as plain text for Shortcuts to handle
                return f"""Authorization required. Please visit this URL to authorize access (note: you must be added as a test user in Google Cloud Console): 
                
{auth_url}

If you see a warning about the app not being verified, click "Advanced" and then "Go to [app name] (unsafe)" to proceed.""", 200
            except Exception as auth_err:
                logger.error(f"Error generating auth URL: {auth_err}")
                return jsonify({"error": f"Authentication error: {str(auth_err)}"}), 500
        
        # Get weather data with error handling
        try:
            weather = get_weather_data()
            if weather.get("error"):
                logger.warning(f"Weather API returned an error: {weather['error']}")
        except Exception as e:
            logger.error(f"Error retrieving weather data: {e}")
            weather = {"error": str(e)}
        
        # Generate summary with error handling
        try:
            summary = generate_summary(events, weather)
            logger.info("Summary generated successfully")
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return jsonify({"error": f"Failed to generate summary: {str(e)}"}), 500
        
        return summary
        
    except Exception as e:
        logger.error(f"Unhandled exception in text_summary endpoint: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Add a new route for using the MCP calendar service directly
@app.route('/api/calendar_events', methods=['GET'])
def get_calendar_events_direct():
    """API endpoint to get calendar events directly using the MCP service"""
    try:
        logger.info("Received request to /api/calendar_events")
        
        # Run the Node.js script to get calendar events
        import subprocess
        import json
        import os
        
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "integrations/google-calendar/get_events.js")
        
        # Check if the script exists
        if not os.path.exists(script_path):
            logger.error(f"Calendar script not found at {script_path}")
            return jsonify({"error": "Calendar integration not set up"}), 500
        
        # Execute the Node.js script
        try:
            result = subprocess.run(["node", script_path], 
                                  capture_output=True, text=True, check=True)
            events = json.loads(result.stdout)
            logger.info(f"Successfully retrieved {len(events)} events from calendar")
            return jsonify(events)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing calendar script: {e}")
            logger.error(f"Script output: {e.stderr}")
            return jsonify({"error": "Failed to get calendar events"}), 500
        
    except Exception as e:
        logger.error(f"Unhandled exception in calendar_events endpoint: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 