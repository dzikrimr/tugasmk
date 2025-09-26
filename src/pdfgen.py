import pdfkit

def html_to_pdf(html_content: str) -> bytes:
    """
    Convert HTML string ke PDF, kembalikan dalam bentuk bytes.
    """
    options = {
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "10mm",
        "margin-right": "10mm",
    }

    # pdfkit.from_string menghasilkan file PDF sementara,
    # tapi kita bisa ambil output sebagai bytes
    pdf_bytes = pdfkit.from_string(html_content, False, options=options)
    return pdf_bytes
