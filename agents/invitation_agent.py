from .base_agent import BaseAgent

class InvitationAgent(BaseAgent):
    def __init__(self):
        prompt = """
        Write a beautiful invitation for the event '{event_name}' ({event_type}) in '{location}' on '{date}'.
        Description: {description}
        Selected Idea: {selected_idea}
        Selected Venue: {selected_venue}
        Selected Vendor Package: {selected_vendor}

        Mention theme, venue, and contact info. Include RSVP and welcoming tone.
        """
        super().__init__(prompt=prompt, name="InvitationAgent", role="Invitation Creator")

def generate_invitation(inputs):
    agent = InvitationAgent()
    return agent.run(inputs)
