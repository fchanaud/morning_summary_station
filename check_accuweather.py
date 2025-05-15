#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API key from environment
ACCUWEATHER_API_KEY = os.getenv("ACCUWEATHER_API_KEY")
ADDRESS = os.getenv("ADDRESS", "16 acer road, dalston - E83GX")

def test_accuweather_location():
    """Test the AccuWeather Location API to check for connectivity and rate limits"""
    try:
        # First, get the location key for the provided address
        location_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
        params = {
            "apikey": ACCUWEATHER_API_KEY,
            "q": ADDRESS
        }
        
        print(f"Testing AccuWeather Location API with address: {ADDRESS}")
        print(f"Using URL: {location_url}")
        
        # Make the request
        location_response = requests.get(location_url, params=params)
        status_code = location_response.status_code
        
        print(f"Status code: {status_code}")
        
        if status_code == 200:
            location_data = location_response.json()
            if not location_data:
                print("✘ API returned empty results - address may not be found")
                return False
            
            location_key = location_data[0]["Key"]
            location_name = location_data[0]["LocalizedName"]
            print(f"✓ Successfully found location: {location_name} (Key: {location_key})")
            return True
        elif status_code == 503:
            print("✘ Service Unavailable (503) - The AccuWeather API may be experiencing issues or you may have exceeded your rate limit")
            return False
        elif status_code == 401:
            print("✘ Unauthorized (401) - Your API key may be invalid or expired")
            return False
        elif status_code == 429:
            print("✘ Too Many Requests (429) - You have exceeded your API key's rate limit")
            return False
        else:
            print(f"✘ Unexpected status code: {status_code}")
            print(f"Response: {location_response.text}")
            return False
    except Exception as e:
        print(f"✘ Error testing AccuWeather API: {e}")
        return False

if __name__ == "__main__":
    if not ACCUWEATHER_API_KEY:
        print("✘ AccuWeather API key not found in environment variables.")
        print("Make sure ACCUWEATHER_API_KEY is set in your .env file or environment.")
        exit(1)
    
    print(f"Testing with API key: {ACCUWEATHER_API_KEY[:5]}...{ACCUWEATHER_API_KEY[-5:]}")
    
    # Test the location API
    test_accuweather_location() 