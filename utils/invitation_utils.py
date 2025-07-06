# invitation_utils.py

from typing import Dict, Tuple
import re
from bs4 import BeautifulSoup


def split_invitation_output(raw_text: str, fallback_title: str = "Event") -> Dict[str, str]:
    """
    Splits the output of the invitation agent into Markdown and HTML parts.
    If HTML is missing, creates a fallback from Markdown.
    """
    parts = re.split(r"### HTML:?", raw_text)
    markdown = parts[0].strip()
    if len(parts) > 1:
        html = parts[1].strip()
    else:
        html = create_html_fallback(markdown, fallback_title)
    return {"markdown": markdown, "html": html}


def create_html_fallback(markdown_text: str, title: str = "Event") -> str:
    """
    Generates a very basic HTML version of the Markdown if HTML isn't provided.
    """
    body = markdown_text.replace("\n", "<br>")
    return f"""
    <html>
      <head><title>{title}</title></head>
      <body style='font-family:sans-serif;'>
        <h1>{title}</h1>
        <div>{body}</div>
      </body>
    </html>
    """


def validate_invitation_output(output: Dict[str, str]) -> Tuple[bool, str]:
    """
    Validates that the invitation output contains both markdown and HTML versions,
    and that the HTML is minimally well-formed.
    """
    markdown_valid = bool(output.get("markdown") and len(output["markdown"]) > 20)
    html_valid = False

    html = output.get("html", "")
    if html:
        try:
            soup = BeautifulSoup(html, "html.parser")
            html_valid = bool(soup.find("body"))
        except Exception:
            html_valid = False

    valid = markdown_valid and html_valid
    message = "✅ Invitation valid." if valid else "❌ Invitation incomplete or malformed."
    return valid, message


def extract_invite_metadata(markdown: str) -> Dict[str, str]:
    """
    Parses basic details from the invitation markdown (like event name, dates, RSVP info).
    """
    info = {}
    if not markdown:
        return info

    lines = markdown.splitlines()
    for line in lines:
        if "when:" in line.lower():
            info["when"] = line.split(":", 1)[-1].strip()
        elif "venue:" in line.lower():
            info["venue"] = line.split(":", 1)[-1].strip()
        elif "rsvp" in line.lower():
            info["rsvp"] = line.strip()
        elif line.lower().startswith("#"):
            info.setdefault("title", line.strip("# "))

    return info
