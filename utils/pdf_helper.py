import markdown2
from weasyprint import HTML

def convert_markdown_to_pdf(markdown_text: str, pdf_path: str):
    html = markdown2.markdown(markdown_text)
    HTML(string=html).write_pdf(pdf_path)
    return pdf_path
