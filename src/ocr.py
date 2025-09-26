import pytesseract
from pdf2image import convert_from_path
import os

##pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(pdf_path, output_dir="data/ocr_output"):
    """
    Convert PDF to images per page, run OCR (Tesseract), 
    and return the extracted text as a string.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert PDF pages to images
    pages = convert_from_path(pdf_path)

    all_text = ""
    for i, page in enumerate(pages):
        # OCR per page
        text = pytesseract.image_to_string(page, lang="ind")
        all_text += text + "\n"

        # Save per page output
        out_file = os.path.join(output_dir, f"page_{i+1}.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(text)

    return all_text.strip()
