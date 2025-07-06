from .base_agent import BaseAgent
from utils.validator import is_valid_url, validate_venue_block
from utils.venue_map_tool import VenueMapTool
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)

class LocationAgent(BaseAgent):
    def __init__(self, llm=None):
        prompt = """Suggest 5 real venues in {location} for the event below.

Event: {event_name} ({event_type})
Theme: {selected_idea}
Date: {start_date} to {end_date}
Time: {start_time} to {end_time}
Budget: ₹{price_range_0} - ₹{price_range_1}
Location Preference: {location_pref}
Description: {description}

For each venue, include:
- Name
- Cost (₹ per person)
- Capacity
- Description
- Phone & email
- Valid Google Maps link or website

Format example:
**Venue 1: [Name]** - ₹[Cost]
Description...
Capacity: X
Contact: +91..., email
Link: https://..."""
        super().__init__(
            prompt=prompt,
            name="LocationAgent",
            role="Venue Suggestion Specialist",
            model="phi3",
            temperature=0.7
        )

        # If a shared LLM is provided, override the default
        if llm:
            self.llm = llm
            self._rebuild_chain()

    def _rebuild_chain(self):
        """Rebuild LLMChain with updated LLM"""
        from langchain.chains import LLMChain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def post_process(self, raw_output: str) -> List[Dict]:
        venue_blocks = re.split(r'\n\n+', raw_output.strip())
        structured = []
        for block in venue_blocks:
            data = validate_venue_block(block)
            if data["valid"] and not is_valid_url(data.get("link", "")):
                data["link"] = VenueMapTool(data["name"])
            if data["valid"]:
                structured.append(data)
        return structured if structured else [{"error": "No valid venues found"}]

    def run_with_scraping_fallback(self, inputs: Dict[str, str]) -> List[Dict]:
        try:
            raw = self.run(inputs)
            structured = self.post_process(raw)
            if len(structured) < 3:
                logger.warning(f"{self.name}: Fewer than 3 valid venues found. Using fallback.")
                structured += self.scrape_fallback(inputs)
            return structured
        except Exception as e:
            logger.error(f"{self.name} failed: {str(e)}. Returning fallback.")
            return self.scrape_fallback(inputs)

    def scrape_fallback(self, inputs: Dict[str, str]) -> List[Dict]:
        fallback_name = "Sample Hall"
        return [{
            "name": fallback_name,
            "cost": "₹2000",
            "capacity": "50",
            "description": "Elegant sample venue in the city",
            "contact_info": {"emails": ["contact@samplehall.com"], "phones": ["+919999999999"]},
            "link": VenueMapTool(fallback_name),
            "valid": True,
            "errors": []
        }]
