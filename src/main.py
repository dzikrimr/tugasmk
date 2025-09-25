from ocr import extract_text_from_pdf
from ner import extract_entities
from utils import clean_text, normalize_money, normalize_duration

# 1. OCR dari PDF
pdf_path = "data/pdf/suratex.pdf"   # taruh file vendor disini
text = extract_text_from_pdf(pdf_path)
print("=== OCR Result (raw) ===")
print(text[:500])  # print sebagian isi

# 2. Cleaning
cleaned_text = clean_text(text)

# 3. NER IndoBERT
entities = extract_entities(cleaned_text)
print("\n=== Entities Extracted by IndoBERT ===")
print(entities)

# 4. Regex tambahan (optional)
extra_money = normalize_money(cleaned_text)
extra_duration = normalize_duration(cleaned_text)

print("\n=== Regex-based Extractions ===")
print("Money:", extra_money)
print("Duration:", extra_duration)
