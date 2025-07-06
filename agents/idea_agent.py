from .base_agent import BaseAgent
from typing import Dict

class IdeaAgent(BaseAgent):
    def __init__(self, llm=None):
        prompt = """You are a creative event planning expert. Generate 5 unique and innovative event ideas based on the following details:

Event Name: {event_name}
Event Type: {event_type}
Location: {location}
Start Date: {start_date}
End Date: {end_date}
Time: {start_time} to {end_time}
Description: {description}
Budget Range: ₹{price_range_0} to ₹{price_range_1}

For each idea, provide:
1. A catchy title (different from the event name)
2. A brief description (2-3 sentences)
3. A theme tag (e.g., #Heritage, #Modern, #Spiritual, #Adventure, #Culinary)
4. Why it fits the event type and location

Make each idea distinctly different in style and approach. Consider the local culture, venue possibilities, and budget constraints.

Format your response as:

**Idea 1: [Title]** #[Theme]
Description: [2-3 sentences explaining the concept]
Why it works: [1 sentence on suitability]

**Idea 2: [Title]** #[Theme]
Description: [2-3 sentences explaining the concept]
Why it works: [1 sentence on suitability]

[Continue for all 5 ideas]
"""
        super().__init__(
            prompt=prompt,
            name="IdeaAgent",
            role="Creative Event Brainstormer",
            llm=llm  # <-- pass LLM to BaseAgent
        )

    async def generate_ideas(self, inputs: Dict) -> Dict:
        """Generate creative event ideas asynchronously"""
        return await self.arun(inputs)
