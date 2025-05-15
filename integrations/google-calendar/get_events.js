#!/usr/bin/env node

const GoogleCalendarService = require('./calendar_service');
const path = require('path');

// Create a directory-independent config path
const configPath = path.join(__dirname, 'calendar_config.json');

// Create an instance of the service
const calendarService = new GoogleCalendarService(configPath);

// Get today's events
async function getTodayEvents() {
  try {
    // Initialize the calendar service
    await calendarService.initialize();
    
    // Get today's events
    const events = await calendarService.getTodayEvents();
    
    // Format the events
    const formattedEvents = calendarService.formatEvents(events);
    
    // Output as JSON
    console.log(JSON.stringify(formattedEvents));
  } catch (error) {
    console.error('Error getting today\'s events:', error);
    process.exit(1);
  }
}

// Run the function
getTodayEvents(); 