from .base_agent import BaseAgent
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

prompt = """
Suggest 5 suitable venues in '{location}' for the event type '{event_type}' titled '{event_name}' on '{date}'. Description: {description}.
Give options like outdoor, indoor, and unique venues. Format:
1. <venue name> - <short reason>
..."""

def suggest_venues(inputs):
    class LocationAgent(BaseAgent):
        def __init__(self):
            super().__init__(
                name="LocationAgent",
                role="Venue Suggestion Agent",
                prompt=prompt
            )
            self.prompt = PromptTemplate(
                input_variables=["event_name", "event_type", "location", "date", "description"],
                template=prompt,
            )
            self.chain = LLMChain(llm=self.chain.llm, prompt=self.prompt)

    agent = LocationAgent()
    return agent.run(inputs)
