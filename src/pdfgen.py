from weasyprint import HTML

def html_to_pdf(html_content: str) -> bytes:
    """
    Convert HTML string ke PDF, kembalikan dalam bentuk bytes.
    """
    # HTML string -> PDF bytes
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
