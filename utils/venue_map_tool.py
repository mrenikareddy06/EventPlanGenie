# utils/venue_map_tool.py

import requests

class VenueMapTool:
    """
    Utility to fetch map location for a venue using OpenStreetMap (Nominatim API).
    """
    @staticmethod
    def get_venue_map_link(venue_name: str, city: str) -> dict:
        query = f"{venue_name}, {city}"
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": 1}
        headers = {
            "User-Agent": "EventPlanGenie/1.0 (https://github.com/mrenikareddy06/EventPlanGenie)"
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            results = response.json()

            if results:
                place = results[0]
                map_link = f"https://www.openstreetmap.org/?mlat={place['lat']}&mlon={place['lon']}"
                return {
                    "name": venue_name,
                    "location": city,
                    "latitude": place["lat"],
                    "longitude": place["lon"],
                    "map_link": map_link,
                    "display_name": place["display_name"]
                }
            else:
                return {"error": f"No location found for '{venue_name}' in {city}."}
        except Exception as e:
            return {"error": str(e)}
