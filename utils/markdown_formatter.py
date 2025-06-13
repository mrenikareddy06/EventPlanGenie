# utils/markdown_formatter.py

def format_markdown(text: str) -> str:
    # Adds double line breaks for Streamlit markdown rendering
    return text.replace('\n', '\n\n')

def clean_html_tags(text: str) -> str:
    import re
    return re.sub(r'<[^>]+>', '', text)
