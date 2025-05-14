# Morning Summary Station

A Flask application that provides personalized morning summaries with weather forecasts and calendar events. Designed to be integrated with iOS Shortcuts for a daily briefing.

## Features

- Daily weather forecast from AccuWeather
- Calendar events from Google Calendar
- AI-generated personalized summary using OpenAI
- Web interface for viewing summaries
- API endpoints for iOS Shortcuts integration

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- AccuWeather API key
- OpenAI API key
- Google Calendar API credentials (for production use)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/morning_summary_station.git
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
   OPENAI_API_KEY=your_openai_api_key_here
   ACCUWEATHER_API_KEY=your_accuweather_api_key_here
   
   # Location Settings
   LOCATION=London
   ADDRESS=your_address_here
   
   # Google Calendar Settings
   GOOGLE_CALENDAR_ID=primary
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the web interface at `http://localhost:5000`

## iOS Shortcuts Integration

To integrate with iOS Shortcuts:

1. Create a new shortcut in the Shortcuts app
2. Add a "Get Contents of URL" action
3. Set the URL to `http://your-server-ip:5000/api/text_summary`
4. Add a "Show Result" action or use "Speak Text" for a verbal summary

## API Endpoints

- `/api/summary` - Returns a JSON object with all summary data
- `/api/text_summary` - Returns just the text summary (ideal for Shortcuts)

## License

MIT # morning_summary_station
