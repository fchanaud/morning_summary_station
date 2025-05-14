# iOS Shortcut Setup for Morning Summary Station

This guide will help you set up an iOS Shortcut to trigger your Morning Summary Station with a single tap on your iPhone.

## Prerequisites

- Your Morning Summary Station backend must be deployed and accessible via a public URL
- You need to have completed the Google Calendar OAuth setup at least once
- iOS Shortcuts app installed on your iPhone

## Creating the Shortcut

1. **Open the Shortcuts app** on your iPhone

2. **Create a new shortcut**:
   - Tap the "+" button in the top right corner
   - Tap "Add Action"

3. **Add the "Get Contents of URL" action**:
   - Search for "Get Contents of URL" in the search bar
   - Tap on it to add it to your shortcut
   - Configure it as follows:
     - URL: `https://your-server-address/api/text_summary` (replace with your actual server address)
     - Method: GET
     - Headers: None required (unless you've added authentication)
     - Request Body: None required

4. **Add the "Speak Text" action**:
   - Tap "+" to add another action
   - Search for "Speak Text" in the search bar
   - Tap on it to add it to your shortcut
   - Tap on the "Text" field
   - Tap on the "Get Contents of URL" result from the variables menu to connect them
   - Configure speech options (optional):
     - Tap "Show More" to expand options
     - Voice: Choose a more energetic voice (like "Fred" or "Samantha")
     - Pitch: Set to around 1.2 for more enthusiasm
     - Rate: Set to around 0.9 for clear but energetic speech
     - Volume: Set to maximum (1.0)

5. **Name your shortcut**:
   - Tap "Next" in the top right corner
   - Enter a name like "Morning Summary" or "Daily Briefing"
   - Optionally, customize the icon by tapping on it

6. **Add to Home Screen** (for easier access):
   - From the Shortcuts app, find your new shortcut
   - Long press on it
   - Select "Add to Home Screen"
   - Confirm by tapping "Add" in the top right corner

## Using the Shortcut

Once set up, using your Morning Summary Station is simple:

1. **First-time use**:
   - The first time you tap the shortcut, you may need to complete the Google Calendar authorization
   - Your iPhone will open a browser window to complete this process
   - After authorization, your shortcut will work automatically

2. **Daily use**:
   - Just tap the shortcut icon on your home screen
   - Your iPhone will fetch the morning summary
   - It will then speak the summary out loud with enthusiasm!

## Troubleshooting

- **If the shortcut doesn't speak**: Make sure your iPhone's volume is turned up and not on silent mode
- **If you get an error message**: Check that your server is running and accessible
- **If calendar events are missing**: You may need to re-authorize Google Calendar access
- **If your iPhone goes to sleep**: The shortcut will continue to run in the background
- **If you want to stop the speech**: Press the home button or swipe up (depending on your iPhone model)

## Advanced Options

- **Add to Siri**: You can add a Siri voice command to run your shortcut
- **Automation**: Schedule your shortcut to run automatically at a certain time each morning
- **Low Power Mode**: If your iPhone is in low power mode, the speech may be at a lower volume

---

Need more help? Visit the GitHub repository at https://github.com/fchanaud/morning_summary_station for additional resources. 