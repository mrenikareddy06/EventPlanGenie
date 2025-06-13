from .base_agent import BaseAgent
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class VendorAgent(BaseAgent):
    def __init__(self):
        prompt = """
        You are an event planning assistant. Based on the selected event idea and venue, suggest 5 real-world vendor bundles (catering, decor, etc.).
        Each bundle should be cost-efficient and themed.

        Event: {event_name} ({event_type})
        Location: {location}
        Date: {date}
        Description: {description}

        Output: List 5 vendor packages with estimated cost.
        """
        super().__init__(prompt=prompt, name="VendorAgent", role="Vendor Suggestion Expert")

def get_vendor_bundles(inputs):
    agent = VendorAgent()
    return agent.run(inputs)

