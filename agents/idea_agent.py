from .base_agent import BaseAgent

class IdeaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="IdeaAgent",
            role="Creative Event Brainstormer",
            prompt="""You are a creative AI helping users brainstorm unique event ideas based on the following:
            Event Name: {event_name}
            EventType: {event_type}
            Location: {location}
            Date: {date}
            Description:{description}
            
            Return 5 diverse, fun, and viable ideas with brief descriptions.
            """
        )

def generate_ideas(inputs):
    agent = IdeaAgent()
    return agent.run(inputs)
