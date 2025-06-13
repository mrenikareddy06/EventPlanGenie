
from ics import Calendar, Event

def create_ics(event_title, event_date, event_description):
    cal = Calendar()
    e = Event()
    e.name = event_title
    e.begin = event_date
    e.description = event_description
    cal.events.add(e)
    return str(cal)