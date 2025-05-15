const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

class GoogleCalendarService {
  constructor(configPath) {
    this.configPath = configPath || path.join(__dirname, 'calendar_config.json');
    this.initialized = false;
    this.auth = null;
    this.calendar = null;
  }

  /**
   * Initialize the Google Calendar service
   */
  async initialize() {
    try {
      // Check if config file exists
      if (!fs.existsSync(this.configPath)) {
        throw new Error(`Configuration file not found at ${this.configPath}. Please run getToken.js first.`);
      }

      // Read config
      const config = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
      
      // Create OAuth2 client
      this.auth = new google.auth.OAuth2(
        config.client_id,
        config.client_secret,
        config.redirect_uri
      );

      // Set credentials
      this.auth.setCredentials({
        refresh_token: config.refresh_token
      });

      // Create calendar client
      this.calendar = google.calendar({ version: 'v3', auth: this.auth });
      this.initialized = true;
      
      return true;
    } catch (error) {
      console.error('Error initializing Google Calendar service:', error);
      throw error;
    }
  }

  /**
   * Get today's events
   */
  async getTodayEvents() {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      // Calculate today's start and end
      const today = new Date();
      const startOfDay = new Date(today);
      startOfDay.setHours(0, 0, 0, 0);
      const endOfDay = new Date(today);
      endOfDay.setHours(23, 59, 59, 999);

      // Format dates for Google Calendar API
      const timeMin = startOfDay.toISOString();
      const timeMax = endOfDay.toISOString();

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