# utils/markdown_formatter.py

import re

def format_markdown_output(text: str) -> str:
    """
    Cleans up and formats raw text into polished Markdown.

    - Ensures headings and lists are well formatted
    - Removes redundant emojis or symbols
    - Normalizes spacing and line breaks
    """
    if not text:
        return ""

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # Fix headings (e.g., "##Heading" -> "## Heading")
    text = re.sub(r'(?m)^(#+)([^\s#])', r'\1 \2', text)

    # Fix bullet points (e.g., "-item" -> "- item")
    text = re.sub(r'(?m)^-\s*([^\s])', r'- \1', text)

    # Limit excessive emojis/symbols
    text = re.sub(r'[\u2600-\u26FF\u2700-\u27BF\u1F300-\u1F6FF\u1F900-\u1F9FF]{3,}', '', text)

    # Remove trailing whitespace
    text = text.strip()

    return text
