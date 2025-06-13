from .base_agent import BaseAgent

prompt = """
Generate a time-wise schedule for the '{event_name}' ({event_type}) on '{date}'.
Description: {description}
Selected Idea: {selected_idea}
Selected Venue: {selected_venue}
Selected Vendor Package: {selected_vendor}

Start from guest arrival and end with wrap-up. Format:
- 5:00 PM - Guest Arrival
- 5:30 PM - Opening Ceremony
...
"""

def create_schedule(inputs):
    agent = BaseAgent(prompt)
    return agent.run(inputs)
