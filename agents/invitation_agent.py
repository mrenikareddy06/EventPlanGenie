from .base_agent import BaseAgent
from typing import Dict
import logging

logger = logging.getLogger(__name__)

INVITE_PROMPT = """You are a professional event invitation writer.

Event:
- Name: {event_name}
- Theme: {selected_idea}
- Venue: {selected_venue}
- When: {start_date} to {end_date}, {start_time}–{end_time}
- Description: {description}

Create two outputs:
1. MARKDOWN invitation including RSVP instructions, contact info.
2. HTML version of the same (inline CSS okay).

Return keys: markdown, html

Format:
### MARKDOWN:
[Markdown version here]

### HTML:
[HTML version here]
"""

class InvitationAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(
            prompt=INVITE_PROMPT,
            name="InvitationAgent",
            role="Invitation Creator",
            model="phi3",
            temperature=0.6
        )
        if llm:
            self.llm = llm

    def run(self, inputs: Dict[str, str]) -> Dict[str, str]:
        try:
            raw = super().run(inputs)
            parts = raw.split("### HTML:")
            if len(parts) == 2:
                markdown = parts[0].replace("### MARKDOWN:", "").strip()
                html = parts[1].strip()
            else:
                logger.warning("InvitationAgent: Unexpected format in output. Falling back.")
                markdown = raw.strip()
                html = self.create_html_fallback(markdown, inputs.get("event_name", "Event"))

            return {"markdown": markdown, "html": html}
        except Exception as e:
            logger.error(f"InvitationAgent Error: {e}")
            return {
                "markdown": f"⚠️ Could not generate invitation. Error: {e}",
                "html": self.create_html_fallback("Error generating invitation", "Event")
            }

    def create_html_fallback(self, md_text: str, title: str) -> str:
        escaped = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        return f"<html><head><title>{title}</title></head><body><h2>{title}</h2><p>{escaped}</p></body></html>"


def generate_invitation(inputs: Dict[str, str], llm=None) -> Dict[str, str]:
    return InvitationAgent(llm=llm).run(inputs)
