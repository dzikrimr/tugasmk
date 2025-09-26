from fastapi import FastAPI, UploadFile, File
import uvicorn
import traceback
import os
from collections import defaultdict
from src.ocr import extract_text_from_pdf
from src.ner import extract_entities
from src.utils import clean_text

app = FastAPI()

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        os.makedirs("temp", exist_ok=True)
        pdf_path = f"temp/{file.filename}"

        # simpan file PDF sementara
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # OCR per halaman
        text_pages = extract_text_from_pdf(pdf_path, return_pages=True)  # kembalikan list per halaman
        all_entities = []
        full_text = ""

        for page_text in text_pages:
            cleaned = clean_text(page_text)
            full_text += cleaned + "\n"
            entities = extract_entities(cleaned)  # chunking otomatis di dalam
            all_entities.append(entities)

        # Merge hasil entities per halaman
        merged_entities = defaultdict(list)
        for ent in all_entities:
            for k, v in ent.items():
                merged_entities[k].extend(v)
        # hapus duplikat
        for k in merged_entities:
            merged_entities[k] = list(set(merged_entities[k]))

        return {
            "text_preview": full_text[:300], 
            "entities": merged_entities
        }

    except Exception as e:
        print(traceback.format_exc())
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
