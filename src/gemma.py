import requests
import json
import re

OLLAMA_BASE_URL = "https://ollama.elginbrian.com"
MODEL_NAME = "gemma"

def extract_mapping_from_entities(entities: dict) -> dict:
    """
    Ekstrak dan mapping entities ke field kontrak
    """
    mapping = {}
    
    # Mapping organisasi
    orgs = entities.get("ORG", [])
    if orgs:
        # Cari universitas untuk pihak pertama
        universities = [org for org in orgs if 'universitas' in org.lower()]
        if universities:
            mapping['pihak1_company'] = universities[0]
        
        # Ambil organisasi lain untuk pihak kedua
        other_orgs = [org for org in orgs if 'universitas' not in org.lower() and len(org) > 3]
        if other_orgs:
            mapping['pihak2_company'] = other_orgs[0]
    
    # Mapping person
    persons = entities.get("PER", [])
    if persons:
        # Filter person yang valid (lebih dari 3 karakter)
        valid_persons = [p for p in persons if len(p) > 3 and not p.startswith('##')]
        if len(valid_persons) >= 1:
            mapping['pihak1_name'] = valid_persons[0]
        if len(valid_persons) >= 2:
            mapping['pihak2_name'] = valid_persons[1]
    
    # Mapping lokasi
    locations = entities.get("LOC", [])
    if locations:
        valid_locations = [loc for loc in locations if len(loc) > 5]
        if valid_locations:
            mapping['contract_location'] = valid_locations[0]
            mapping['pihak1_address'] = valid_locations[0]
    
    # Mapping money
    money = entities.get("MONEY", [])
    if money:
        mapping['contract_value'] = money[0]
    
    # Mapping dates
    dates = entities.get("DATE", [])
    if dates:
        mapping['contract_date'] = dates[0] if len(dates) >= 1 else "TBD"
        mapping['start_date'] = dates[0] if len(dates) >= 1 else "TBD"
        mapping['end_date'] = dates[-1] if len(dates) >= 2 else "TBD"
    
    # Default values untuk field yang kosong
    defaults = {
        'contract_number': 'CONT/2024/001',
        'contract_date': 'TBD',
        'contract_location': 'TBD',
        'pihak1_name': 'TBD',
        'pihak1_company': 'TBD',
        'pihak1_address': 'TBD',
        'pihak1_position': 'TBD',
        'pihak2_name': 'TBD',
        'pihak2_company': 'TBD',
        'pihak2_address': 'TBD',
        'pihak2_position': 'TBD',
        'scope_of_work': 'Kerjasama dalam bidang yang telah disepakati bersama',
        'contract_value': 'TBD',
        'contract_value_words': 'TBD',
        'start_date': 'TBD',
        'end_date': 'TBD',
        'terms': 'Ketentuan lain akan diatur dalam addendum terpisah'
    }
    
    # Merge dengan default values
    for key, value in defaults.items():
        if key not in mapping:
            mapping[key] = value
    
    return mapping

def fill_template_with_gemma(template_path: str, entities: dict) -> str:
    """
    Fill template HTML dengan data entities menggunakan Gemma
    """
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()
    
    # Extract mapping dari entities
    field_mapping = extract_mapping_from_entities(entities)
    
    # Buat prompt yang lebih spesifik
    prompt = f"""
Kamu adalah asisten yang bertugas mengisi template kontrak HTML. 
Ganti semua placeholder {{{{ }}}} dengan data yang sesuai dari informasi berikut:

Data yang tersedia:
{json.dumps(field_mapping, indent=2, ensure_ascii=False)}

Template HTML:
{html_template}

INSTRUKSI PENTING:
1. Ganti SEMUA placeholder yang berbentuk {{{{field_name}}}} dengan nilai yang sesuai
2. Jika data tidak tersedia, gunakan "TBD" (To Be Determined)
3. Pastikan HTML tetap valid dan tidak rusak
4. Jangan tambahkan penjelasan, langsung berikan HTML yang sudah terisi
5. Pastikan format tanggal konsisten (DD MMMM YYYY)
6. Untuk contract_value_words, konversi angka ke kata-kata bahasa Indonesia

Output yang diharapkan: HTML lengkap yang siap dikonversi ke PDF.
"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL_NAME, 
                "prompt": prompt, 
                "stream": False,  # Non-streaming untuk hasil yang lebih konsisten
                "options": {
                    "temperature": 0.1,  # Low temperature untuk konsistensi
                    "top_p": 0.9,
                    "top_k": 40
                }
            },
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        filled_html = result.get("response", "").strip()
        
        # Fallback: jika Gemma gagal, isi manual
        if not filled_html or "{{" in filled_html:
            print("[WARNING] Gemma tidak berhasil mengisi semua placeholder, menggunakan fallback manual")
            filled_html = fill_template_manual(html_template, field_mapping)
        
        return filled_html
        
    except requests.RequestException as e:
        print(f"[Gemma API error] {e}")
        print("[INFO] Menggunakan fallback manual untuk mengisi template")
        field_mapping = extract_mapping_from_entities(entities)
        return fill_template_manual(html_template, field_mapping)

def fill_template_manual(html_template: str, field_mapping: dict) -> str:
    """
    Fallback manual untuk mengisi template jika Gemma gagal
    """
    filled_html = html_template
    
    # Ganti semua placeholder
    for field, value in field_mapping.items():
        placeholder = f"{{{{{field}}}}}"
        filled_html = filled_html.replace(placeholder, str(value))
    
    # Handle lampiran list (jika ada)
    lampiran_pattern = r'{%\s*for\s+lampiran\s+in\s+lampiran_list\s*%}.*?{%\s*endfor\s*%}'
    if re.search(lampiran_pattern, filled_html, re.DOTALL):
        # Untuk sekarang, hapus bagian lampiran karena kompleks
        filled_html = re.sub(lampiran_pattern, '<li>Lampiran akan ditentukan kemudian</li>', filled_html, flags=re.DOTALL)
    
    return filled_html

def number_to_words_id(num_str: str) -> str:
    """
    Convert number string to Indonesian words (simplified)
    """
    try:
        # Extract number from string like "Rp 3.500.000"
        num = re.sub(r'[^\d]', '', num_str)
        if not num:
            return "TBD"
        
        # Basic conversion (you might want to use a library like num2words)
        amount = int(num)
        if amount >= 1000000:
            return f"{amount // 1000000} juta"
        elif amount >= 1000:
            return f"{amount // 1000} ribu"
        else:
            return str(amount)
    except:
        return "TBD"