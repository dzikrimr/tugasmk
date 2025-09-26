import pytesseract
from pdf2image import convert_from_path
import os

def extract_text_from_pdf(pdf_path, output_dir="data/ocr_output", return_pages=False):
    """
    Convert PDF to images per page, run OCR (Tesseract).
    
    Args:
        pdf_path (str): path file PDF
        output_dir (str): folder untuk menyimpan output teks per halaman
        return_pages (bool): jika True, kembalikan list teks per halaman

    Returns:
        str atau list: teks lengkap jika return_pages=False,
                       list teks per halaman jika return_pages=True
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert PDF pages to images
    pages = convert_from_path(pdf_path)

    all_text = ""
    page_texts = []

    for i, page in enumerate(pages):
        text = pytesseract.image_to_string(page, lang="ind")
        all_text += text + "\n"
        page_texts.append(text)

        # Save per page output
        out_file = os.path.join(output_dir, f"page_{i+1}.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(text)

    if return_pages:
        return page_texts
    return all_text.strip()
