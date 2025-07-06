import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """
    General-purpose web scraper for use by agents.
    Supports title, link, contact extraction from vendor/venue/location pages.
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_html(self, url: str) -> Optional[str]:
        """Fetch raw HTML content of a webpage"""
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"[WebScraper] Failed to fetch {url}: {e}")
            return None

    def extract_links_and_titles(self, html: str, base_url: str = "") -> List[Dict[str, str]]:
        """Extract all visible <a> tag titles and hrefs"""
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or href.startswith("#") or "javascript:" in href:
                continue

            # Handle relative URLs
            if href.startswith("/"):
                href = base_url.rstrip("/") + href

            results.append({"title": text, "url": href})

        return results

    def extract_contact_info(self, html: str) -> Dict[str, str]:
        """Extract basic contact info like phone numbers and emails"""
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()

        import re
        phones = re.findall(r"\+?\d[\d\s\-\(\)]{7,}\d", text)
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

        return {
            "phone": phones[0] if phones else "",
            "email": emails[0] if emails else ""
        }

    def scrape_summary(self, url: str) -> Dict[str, Optional[str]]:
        """Fetch title, contact info, and top links from a vendor/venue webpage"""
        html = self.fetch_html(url)
        if not html:
            return {}

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title else ""

        contact = self.extract_contact_info(html)
        links = self.extract_links_and_titles(html, base_url=url)

        return {
            "page_title": title,
            "phone": contact.get("phone"),
            "email": contact.get("email"),
            "top_links": links[:5]  # Limit to 5 for brevity
        }

def search_real_vendors(service: str, city: str, budget_range: tuple = ("", "")) -> List[Dict[str, str]]:
    """
    Performs a simple vendor search using Google and scrapes top results.
    Returns a list of real vendor summaries (limited).
    """
    scraper = WebScraper()
    query = f"{service} vendors in {city} event planning"
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    html = scraper.fetch_html(search_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)

    vendor_data = []
    visited = set()

    for link in links:
        href = link["href"]
        if "http" in href and href not in visited and "google" not in href:
            visited.add(href)
            summary = scraper.scrape_summary(href)
            if summary and (summary.get("email") or summary.get("phone")):
                vendor_data.append({
                    "name": summary.get("page_title"),
                    "services": [service],
                    "cost": f"₹{budget_range[0]} - ₹{budget_range[1]}",
                    "contact_info": {
                        "email": summary.get("email"),
                        "phone": summary.get("phone")
                    },
                    "link": href
                })

        if len(vendor_data) >= 5:
            break

    return vendor_data
