from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import os
import uuid
import traceback
from collections import defaultdict
from src.ocr import extract_text_from_pdf
from src.ner import extract_entities
from src.utils import clean_text
from src.gemma import fill_template_with_gemma
from src.pdfgen import html_to_pdf

app = FastAPI()

# Folder sementara
os.makedirs("temp", exist_ok=True)
os.makedirs("output", exist_ok=True)

class ContractPayload(BaseModel):
    entities_json: Dict[str, Any]
    template_name: str = "contract_template.html"

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        pdf_path = f"temp/{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        text_pages = extract_text_from_pdf(pdf_path, return_pages=True)
        all_entities = []
        full_text = ""

        for page_text in text_pages:
            cleaned = clean_text(page_text)
            full_text += cleaned + "\n"
            entities = extract_entities(cleaned)
            all_entities.append(entities)

        # Merge entities per halaman
        merged_entities = defaultdict(list)
        for ent in all_entities:
            for k, v in ent.items():
                merged_entities[k].extend(v)
        for k in merged_entities:
            merged_entities[k] = list(set(merged_entities[k]))

        return {
            "text_preview": full_text[:300],
            "entities": merged_entities
        }

    except Exception as e:
        print(traceback.format_exc())
        return {"error": str(e)}


@app.post("/generate_contract")
async def generate_contract(payload: ContractPayload = Body(..., examples={
    "example": {
        "summary": "Contoh payload JSON",
        "value": {
            "entities_json": {
                "text_preview": "Isi teks...",
                "entities": {
                    "ORG": ["universitas kadiri"],
                    "PER": ["Dr. Eko Winarti"],
                    "LOC": ["Jl. Selomangleng No. 1"],
                    "MONEY": ["Rp 3.500.000"],
                    "DATE": ["20 November 2019"],
                    "TIME": ["2 hari"]
                }
            },
            "template_name": "contract_template.html"
        }
    }
})):
    try:
        entities_json = payload.entities_json
        template_name = payload.template_name
        template_path = f"templates/{template_name}"

        if not os.path.exists(template_path):
            return {"error": "Template HTML tidak ditemukan"}

        # Panggil Gemma untuk isi kontrak
        filled_html = fill_template_with_gemma(template_path, entities_json)

        # Convert HTML ke PDF
        pdf_bytes = html_to_pdf(filled_html)
        pdf_file = f"output/contract_{uuid.uuid4().hex}.pdf"
        with open(pdf_file, "wb") as f:
            f.write(pdf_bytes)

        return FileResponse(pdf_file, filename="contract.pdf")

    except Exception as e:
        print(traceback.format_exc())
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
