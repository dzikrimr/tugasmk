from fastapi import FastAPI, UploadFile, File
import uvicorn
import os
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

        # ekstrak teks dan NER
        text = extract_text_from_pdf(pdf_path)
        cleaned = clean_text(text)
        entities = extract_entities(cleaned)

        return {
            "text_preview": cleaned[:300], 
            "entities": entities
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
