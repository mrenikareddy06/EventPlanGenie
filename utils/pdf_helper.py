# utils/pdf_helper.py

from fpdf import FPDF
import tempfile
from typing import Optional

class PDFHelper:
    @staticmethod
    def markdown_to_pdf(markdown_str: str) -> Optional[str]:
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)

            # Clean markdown syntax for basic text
            lines = markdown_str.replace("**", "").replace("##", "").replace("###", "").splitlines()
            for line in lines:
                line = line.strip()
                if line:
                    pdf.multi_cell(0, 10, line)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                pdf.output(tmp_pdf.name)
                return tmp_pdf.name
        except Exception as e:
            print(f"PDF generation failed: {e}")
            return None
