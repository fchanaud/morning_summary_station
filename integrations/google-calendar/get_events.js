#!/usr/bin/env node

const path = require('path');
const GoogleCalendarService = require('./calendar_service');

// Create an instance of the calendar service
const configPath = path.join(__dirname, 'calendar_config.json');
const calendarService = new GoogleCalendarService(configPath);

/**
 * Get today's events and print them as JSON
 */
async function getTodayEvents() {
  try {
    // Initialize the service
    if (!calendarService.initialize()) {
      console.error('Failed to initialize calendar service');
      process.exit(1);
    }
    
    // Get events
    const events = await calendarService.getTodayEvents();
    
    // Print events as JSON (for the Python app to read)
    console.log(JSON.stringify(events));
  } catch (error) {
    console.error('Error getting today\'s events:', error);
    process.exit(1);
  }
}

// Run the function
getTodayEvents(); 