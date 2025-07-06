from .base_agent import BaseAgent
from utils.web_scraper import search_real_vendors
from utils.vendor_map_tool import VendorMapTool
from typing import List, Dict


class VendorResearchAgent(BaseAgent):
    def __init__(self, llm=None):
        prompt = """Research 5 **real vendor packages** for the following event. Output only valid businesses available in this city.

Event: {event_name} ({event_type})
Theme: {selected_idea}
Venue: {selected_venue}
Location: {location}
Dates: {start_date} to {end_date}
Budget: ₹{price_range_0} - ₹{price_range_1}
Description: {description}

You MUST return:
- Name
- Services Offered
- Estimated ₹ Cost
- Contact Info (email / phone)
- Link to website or source

Return in structured list or JSON.
"""
        super().__init__(
            prompt=prompt,
            name="VendorResearchAgent",
            role="Real Vendor Scraper",
            model="phi3",
            temperature=0.3
        )

        # Overwrite LLM if it's explicitly disabled or not needed
        if llm is not None:
            self.llm = llm

    def run(self, inputs: Dict[str, str]) -> List[Dict]:
        city = inputs.get("location", "")
        service = inputs.get("event_type", "")
        budget_range = (inputs.get("price_range_0", ""), inputs.get("price_range_1", ""))

        scraped_results = search_real_vendors(service, city, budget_range)
        structured = []

        for vendor in scraped_results:
            result = {
                "name": vendor.get("name"),
                "services": vendor.get("services", []),
                "cost": vendor.get("cost"),
                "contact_info": vendor.get("contact_info", {}),
                "link": vendor.get("link"),
                "valid": True,
                "errors": []
            }

            # Add fallback map link if missing
            if not result.get("link"):
                map_result = VendorMapTool.get_vendor_map_link(result["name"], city)
                if "map_link" in map_result:
                    result["link"] = map_result["map_link"]

            structured.append(result)

        return structured if structured else [{"error": "No real vendors found"}]
