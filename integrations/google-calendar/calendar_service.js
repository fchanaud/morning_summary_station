const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

/**
 * A service class for interacting with Google Calendar
 */
class GoogleCalendarService {
  /**
   * Create a new GoogleCalendarService
   * @param {string} configPath - Path to the calendar config file
   */
  constructor(configPath) {
    this.configPath = configPath || path.join(__dirname, 'calendar_config.json');
    this.calendarId = 'primary'; // Always use primary as the default
    this.oAuth2Client = null;
    this.initialized = false;
  }

  /**
   * Initialize the OAuth2 client
   * @returns {boolean} - Whether initialization was successful
   */
  initialize() {
    try {
      if (!fs.existsSync(this.configPath)) {
        console.error(`Calendar config file not found at ${this.configPath}`);
        return false;
      }

      const config = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
      
      if (!config.installed) {
        console.error('Invalid config file: missing "installed" properties');
        return false;
      }

      const { client_id, client_secret, redirect_uris } = config.installed;
      
      // Create OAuth client
      this.oAuth2Client = new google.auth.OAuth2(
        client_id,
        client_secret,
        redirect_uris[0]
      );

      // Set credentials if we have tokens
      if (config.tokens) {
        console.log('Setting credentials from config tokens');
        this.oAuth2Client.setCredentials(config.tokens);
        this.initialized = true;
        return true;
      } else {
        console.error('No tokens found in config file');
        return false;
      }
    } catch (error) {
      console.error('Error initializing calendar service:', error);
      return false;
    }
  }

  /**
   * Get today's events from Google Calendar
   * @returns {Promise<Array>} - A promise that resolves to an array of events
   */
  async getTodayEvents() {
    if (!this.initialized && !this.initialize()) {
      throw new Error('Calendar service not initialized');
    }

    // Set up date range for today
    const now = new Date();
    const startOfDay = new Date(now.setHours(0, 0, 0, 0));
    const endOfDay = new Date(now.setHours(23, 59, 59, 999));

    // Create calendar API client
    const calendar = google.calendar({ version: 'v3', auth: this.oAuth2Client });

    try {
      // Get events for today
      const response = await calendar.events.list({
        calendarId: this.calendarId,
        timeMin: startOfDay.toISOString(),
        timeMax: endOfDay.toISOString(),
        singleEvents: true,
        orderBy: 'startTime',
      });

      const events = response.data.items || [];
      return events.map(event => {
        // Format the event to a simpler structure
        const startDateTime = event.start.dateTime || event.start.date;
        const endDateTime = event.end.dateTime || event.end.date;
        
        // Format time for display
        let formattedTime = 'All day';
        if (startDateTime && startDateTime.includes('T')) {
          const date = new Date(startDateTime);
          formattedTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        
        return {
          summary: event.summary || 'Untitled Event',
          start: startDateTime,
          end: endDateTime,
          formattedTime
        };
      });
    } catch (error) {
      console.error('Error getting today\'s events:', error);
      throw error;
    }
  }

  /**
   * Get events for a specific date range
   */
  async getEvents(startDate, endDate) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      // Format dates for Google Calendar API
      const timeMin = new Date(startDate).toISOString();
      const timeMax = new Date(endDate).toISOString();

      // Get events
      const response = await this.calendar.events.list({
        calendarId: 'primary',
        timeMin: timeMin,
        timeMax: timeMax,
        singleEvents: true,
        orderBy: 'startTime',
      });

      return response.data.items || [];
    } catch (error) {
      console.error('Error getting events:', error);
      throw error;
    }
  }

  /**
   * Format events into a more usable structure
   */
  formatEvents(events) {
    return events.map(event => {
      const start = event.start.dateTime || event.start.date;
      const end = event.end.dateTime || event.end.date;
      
      // Format the time in a readable way
      let formattedTime = '';
      if (event.start.dateTime) {
        const startTime = new Date(event.start.dateTime);
        const endTime = new Date(event.end.dateTime);
        formattedTime = `${startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - ${endTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      } else {
        formattedTime = 'All day';
      }
      
      return {
        id: event.id,
        summary: event.summary || 'Untitled Event',
        description: event.description || '',
        location: event.location || '',
        start: start,
        end: end,
        formattedTime: formattedTime,
        attendees: (event.attendees || []).map(a => a.email),
        isAllDay: !event.start.dateTime
      };
    });
  }
}

module.exports = GoogleCalendarService; 