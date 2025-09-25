from fastapi import FastAPI, UploadFile, File
import uvicorn
from src.ocr import extract_text_from_pdf
from src.ner import extract_entities
from src.utils import clean_text

app = FastAPI()

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    pdf_path = f"temp/{file.filename}"
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    text = extract_text_from_pdf(pdf_path)
    cleaned = clean_text(text)
    entities = extract_entities(cleaned)

    return {
        "text_preview": cleaned[:300],  # preview sebagian
        "entities": entities
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
