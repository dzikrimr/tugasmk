from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import FileResponse, JSONResponse
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
            return JSONResponse(
                status_code=404,
                content={"error": f"Template HTML tidak ditemukan: {template_path}"}
            )

        print(f"[INFO] Processing entities: {entities_json}")
        
        # Panggil Gemma untuk isi kontrak
        filled_html = fill_template_with_gemma(template_path, entities_json)
        
        # Debug: Cek apakah masih ada placeholder
        if "{{" in filled_html:
            print("[WARNING] Masih ada placeholder yang tidak terisi!")
            print(f"Filled HTML preview: {filled_html[:500]}...")
        else:
            print("[INFO] Semua placeholder berhasil diisi")

        # Convert HTML ke PDF
        try:
            pdf_bytes = html_to_pdf(filled_html)
            pdf_file = f"output/contract_{uuid.uuid4().hex}.pdf"
            
            with open(pdf_file, "wb") as f:
                f.write(pdf_bytes)
            
            print(f"[INFO] PDF berhasil dibuat: {pdf_file}")
            return FileResponse(
                pdf_file, 
                filename="contract.pdf",
                media_type="application/pdf"
            )
            
        except Exception as pdf_error:
            print(f"[ERROR] Gagal membuat PDF: {pdf_error}")
            # Return HTML untuk debugging
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Gagal membuat PDF: {str(pdf_error)}",
                    "filled_html": filled_html[:1000]  # First 1000 chars for debugging
                }
            )

    except Exception as e:
        print(f"[ERROR] General error: {e}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/debug/template/{template_name}")
async def debug_template(template_name: str):
    """
    Endpoint untuk debugging template
    """
    try:
        template_path = f"templates/{template_name}"
        if not os.path.exists(template_path):
            return {"error": "Template tidak ditemukan"}
        
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
        
        # Extract placeholders
        import re
        placeholders = re.findall(r'\{\{(\w+)\}\}', template_content)
        
        return {
            "template_path": template_path,
            "placeholders_found": list(set(placeholders)),
            "template_preview": template_content[:500]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test/entities")
async def test_entities():
    """
    Endpoint untuk testing entities mapping
    """
    from src.gemma import extract_mapping_from_entities
    
    test_entities = {
        "ORG": ["universitas kadiri", "jpc universitas kadiri", "job placement center"],
        "PER": ["Dr. Eko Winarti", "Fajar Setiawan", "Imam Safi'i"],
        "LOC": ["Jl. Selomangleng No. 1 Kediri", "Gedung H"],
        "MONEY": ["Rp 3.500.000", "Rp 400.000,00"],
        "DATE": ["19 November 2019", "20 November 2019"],
        "TIME": ["2 hari"]
    }
    
    mapping = extract_mapping_from_entities(test_entities)
    return {
        "test_entities": test_entities,
        "extracted_mapping": mapping
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)