from .base_agent import BaseAgent
from utils.validator import validate_vendor_block
from utils.vendor_map_tool import VendorMapTool
from typing import Dict, List
import re

class VendorAgent(BaseAgent):
    def __init__(self):
        prompt = """Suggest 5 vendor packages for this event:

Event: {event_name} ({event_type})
Theme: {selected_idea}
Venue: {selected_venue}
Location: {location}
Dates: {start_date} to {end_date}
Budget: ₹{price_range_0} - ₹{price_range_1}
Description: {description}

Each vendor package must include:
- Name
- Services
- ₹ Cost
- Contact
- Valid link

Format:
**Package 1: [Name]** - ₹[Cost]
Includes: [services]
Contact: +91..., email
Link: https://..."""
        super().__init__(prompt=prompt, name="VendorAgent", role="Vendor Specialist")

    def post_process(self, raw_output: str, city: str = "") -> List[Dict]:
        vendor_blocks = re.split(r'\n\n+', raw_output.strip())
        structured = []
        for block in vendor_blocks:
            data = validate_vendor_block(block)
            if data["valid"] and city and not data.get("link"):
                map_result = VendorMapTool.get_vendor_map_link(data["name"], city)
                if "map_link" in map_result:
                    data["link"] = map_result["map_link"]
            if data["valid"]:
                structured.append(data)
        return structured if structured else [{"error": "No valid vendors found"}]

    def run_with_scraping_fallback(self, inputs: Dict[str, str]) -> List[Dict]:
        raw = self.run(inputs)
        structured = self.post_process(raw, city=inputs.get("location", ""))
        if len(structured) < 3:
            structured += self.scrape_fallback(inputs)
        return structured

    def scrape_fallback(self, inputs: Dict[str, str]) -> List[Dict]:
        fallback_name = "Star Catering"
        map_result = VendorMapTool.get_vendor_map_link(fallback_name, inputs.get("location", ""))
        return [{
            "name": fallback_name,
            "services": ["Buffet", "Live Counter"],
            "cost": "₹500",
            "contact_info": {"emails": ["star@vendor.com"], "phones": ["+918888888888"]},
            "link": map_result.get("map_link", "https://vendor.com"),
            "valid": True,
            "errors": []
        }]

def get_vendor_bundles(inputs: Dict[str, str]) -> List[Dict]:
    agent = VendorAgent()
    return agent.run_with_scraping_fallback(inputs)
