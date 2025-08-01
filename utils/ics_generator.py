from ics import Calendar, Event
from datetime import datetime, timedelta
import re
import uuid

class ICSGenerator:
    """
    ICS Calendar Generator for Event Planning
    Converts event plans into proper .ics calendar files
    """
    
    def __init__(self):
        self.calendar = Calendar()
    
    def generate_ics(self, markdown_str: str) -> str:
        """
        Converts Markdown event plan into a proper .ics calendar string.
        Extracts:
        - Event name
        - Location
        - Start/end date
        - Time range (if available)
        """
        # Fallbacks
        event_name = "Planned Event"
        location = "Not specified"
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = start_date
        start_time = "10:00"
        end_time = "12:00"

        # Extract from Markdown
        name_match = re.search(r'Event Name:\s*(.+)', markdown_str)
        if name_match:
            event_name = name_match.group(1).strip()

        loc_match = re.search(r'Location:\s*(.+)', markdown_str)
        if loc_match:
            location = loc_match.group(1).strip()

        date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})(?:\s*to\s*(\d{4}-\d{2}-\d{2}))?', markdown_str)
        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2) if date_match.group(2) else start_date

        time_match = re.search(r'Time:\s*(\d{1,2}:\d{2})\s*(AM|PM)?\s*to\s*(\d{1,2}:\d{2})\s*(AM|PM)?', markdown_str, re.IGNORECASE)
        if time_match:
            start_time = time_match.group(1)
            end_time = time_match.group(3)

        # Parse datetime safely
        try:
            start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            # Fallback to current time if parsing fails
            start_dt = datetime.now()
            end_dt = start_dt + timedelta(hours=2)

        # Generate ICS content
        calendar = Calendar()
        event = Event()
        event.name = event_name
        event.begin = start_dt
        event.end = end_dt
        event.location = location
        event.description = "Generated by EventPlanGenie"
        event.uid = str(uuid.uuid4())

        calendar.events.add(event)
        return str(calendar)
    
    def generate_event_ics(self, event_plan: dict) -> str:
        """
        Generate ICS from event plan dictionary (used in main.py)
        """
        # Extract event details from the event plan dictionary
        event_name = event_plan.get("event_name", "Planned Event")
        location = event_plan.get("location", "Not specified")
        description = event_plan.get("description", "Generated by EventPlanGenie")
        
        # Handle date parsing
        start_date = event_plan.get("start_date", datetime.now().strftime("%Y-%m-%d"))
        end_date = event_plan.get("end_date", start_date)
        start_time = event_plan.get("start_time", "10:00")
        end_time = event_plan.get("end_time", "12:00")
        
        # Parse datetime safely
        try:
            start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            # Fallback to current time if parsing fails
            start_dt = datetime.now()
            end_dt = start_dt + timedelta(hours=2)
        
        # Generate ICS content
        calendar = Calendar()
        event = Event()
        event.name = event_name
        event.begin = start_dt
        event.end = end_dt
        event.location = location
        event.description = description
        event.uid = str(uuid.uuid4())
        
        # Add additional details if available
        if "estimated_guests" in event_plan:
            event.description += f"\nEstimated Guests: {event_plan['estimated_guests']}"
        
        if "budget" in event_plan:
            event.description += f"\nBudget: ${event_plan['budget']:,.2f}"
        
        calendar.events.add(event)
        return str(calendar)
    
    def create_multiple_events(self, events_data: list) -> str:
        """
        Create ICS file with multiple events
        """
        calendar = Calendar()
        
        for event_data in events_data:
            event = Event()
            event.name = event_data.get("name", "Event")
            event.begin = event_data.get("start_time", datetime.now())
            event.end = event_data.get("end_time", datetime.now() + timedelta(hours=1))
            event.location = event_data.get("location", "")
            event.description = event_data.get("description", "")
            event.uid = str(uuid.uuid4())
            
            calendar.events.add(event)
        
        return str(calendar)

# Keep the original function for backward compatibility
def generate_ics(markdown_str: str) -> str:
    """
    Legacy function for backward compatibility
    """
    generator = ICSGenerator()
    return generator.generate_ics(markdown_str)