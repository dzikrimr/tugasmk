import requests
import json
import re
from datetime import datetime

OLLAMA_BASE_URL = "https://ollama.elginbrian.com"
MODEL_NAME = "gemma"

def extract_mapping_from_entities(entities: dict) -> dict:
    """
    Ekstrak dan mapping entities ke field kontrak dengan logika yang lebih baik
    """
    mapping = {}
    
    print(f"[DEBUG] Input entities: {entities}")
    
    # Mapping organisasi
    orgs = entities.get("ORG", [])
    if orgs:
        # Cari universitas untuk pihak pertama
        universities = [org for org in orgs if 'universitas' in org.lower()]
        if universities:
            mapping['pihak1_company'] = universities[0].title()
            print(f"[DEBUG] Found pihak1_company: {mapping['pihak1_company']}")
        
        # Ambil organisasi lain untuk pihak kedua (yang bukan universitas)
        other_orgs = [org for org in orgs if 'universitas' not in org.lower() and len(org) > 5]
        if other_orgs:
            mapping['pihak2_company'] = other_orgs[0].title()
            print(f"[DEBUG] Found pihak2_company: {mapping['pihak2_company']}")
    
    # Mapping person - filter dan clean
    persons = entities.get("PER", [])
    if persons:
        # Filter person yang valid
        valid_persons = []
        for p in persons:
            # Skip tokens yang dimulai dengan ## atau terlalu pendek
            if not p.startswith('##') and len(p) > 3 and '.' not in p[:3]:
                valid_persons.append(p.title())
        
        if len(valid_persons) >= 1:
            mapping['pihak1_name'] = valid_persons[0]
            mapping['pihak1_position'] = 'Pejabat yang berwenang'
            print(f"[DEBUG] Found pihak1_name: {mapping['pihak1_name']}")
            
        if len(valid_persons) >= 2:
            mapping['pihak2_name'] = valid_persons[1]
            mapping['pihak2_position'] = 'Direktur'
            print(f"[DEBUG] Found pihak2_name: {mapping['pihak2_name']}")
    
    # Mapping lokasi
    locations = entities.get("LOC", [])
    if locations:
        # Ambil alamat yang paling lengkap
        valid_locations = [loc for loc in locations if len(loc) > 10]
        if valid_locations:
            best_location = max(valid_locations, key=len)  # Ambil yang paling panjang
            mapping['contract_location'] = best_location.title()
            mapping['pihak1_address'] = best_location.title()
            mapping['pihak2_address'] = best_location.title()
            print(f"[DEBUG] Found location: {best_location}")
    
    # Mapping money
    money = entities.get("MONEY", [])
    if money:
        # Ambil nilai terbesar
        amounts = []
        for m in money:
            # Extract angka dari string seperti "Rp 3.500.000"
            num_str = re.sub(r'[^\d]', '', m)
            if num_str:
                amounts.append((int(num_str), m))
        
        if amounts:
            # Ambil yang terbesar
            max_amount = max(amounts, key=lambda x: x[0])
            mapping['contract_value'] = max_amount[1]
            mapping['contract_value_words'] = number_to_words_id(max_amount[1])
            print(f"[DEBUG] Found contract_value: {mapping['contract_value']}")
    
    # Mapping dates
    dates = entities.get("DATE", [])
    if dates:
        # Sort tanggal
        sorted_dates = sorted(dates)
        mapping['contract_date'] = sorted_dates[0]
        mapping['start_date'] = sorted_dates[0]
        mapping['end_date'] = sorted_dates[-1] if len(sorted_dates) > 1 else sorted_dates[0]
        print(f"[DEBUG] Found dates: {sorted_dates}")
    
    # Default values untuk field yang masih kosong
    defaults = {
        'contract_number': f'CONT/{datetime.now().year}/{str(datetime.now().month).zfill(3)}',
        'contract_date': datetime.now().strftime('%d %B %Y'),
        'contract_location': 'Kediri, Jawa Timur',
        'pihak1_name': 'Pejabat Universitas',
        'pihak1_company': 'Universitas Kadiri',
        'pihak1_address': 'Jl. Selomangleng No. 1, Kediri',
        'pihak1_position': 'Rektor',
        'pihak2_name': 'Mitra Kerjasama',
        'pihak2_company': 'PT. Mitra Sejahtera',
        'pihak2_address': 'Alamat Mitra',
        'pihak2_position': 'Direktur',
        'scope_of_work': 'Kerjasama dalam bidang Job Fair dan penempatan kerja mahasiswa',
        'contract_value': 'Rp 5.000.000',
        'contract_value_words': 'Lima Juta',
        'start_date': datetime.now().strftime('%d %B %Y'),
        'end_date': datetime.now().strftime('%d %B %Y'),
        'terms': 'Ketentuan teknis dan administratif akan diatur dalam surat perjanjian terpisah'
    }
    
    # Merge dengan default values hanya jika field belum ada
    for key, value in defaults.items():
        if key not in mapping:
            mapping[key] = value
    
    print(f"[DEBUG] Final mapping: {mapping}")
    return mapping

def fill_template_with_gemma(template_path: str, entities: dict) -> str:
    """
    Fill template HTML dengan data entities
    """
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()
    
    # Extract mapping dari entities
    field_mapping = extract_mapping_from_entities(entities)
    
    print(f"[INFO] Trying Gemma API...")
    
    # Coba Gemma dulu dengan prompt yang lebih sederhana
    simple_prompt = f"""
Replace all placeholders in this HTML template with the corresponding values.

Data to use:
- pihak1_name: {field_mapping.get('pihak1_name', 'TBD')}
- pihak1_company: {field_mapping.get('pihak1_company', 'TBD')}
- pihak2_name: {field_mapping.get('pihak2_name', 'TBD')}
- contract_value: {field_mapping.get('contract_value', 'TBD')}
- contract_date: {field_mapping.get('contract_date', 'TBD')}

Template:
{html_template}

Return only the complete HTML with all {{placeholder}} replaced with actual values.
"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL_NAME, 
                "prompt": simple_prompt, 
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 2000
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            filled_html = result.get("response", "").strip()
            
            print(f"[INFO] Gemma response length: {len(filled_html)}")
            
            # Cek apakah Gemma berhasil
            if filled_html and len(filled_html) > 500 and "{{" not in filled_html:
                print("[INFO] Gemma berhasil mengisi template")
                return filled_html
            else:
                print("[WARNING] Gemma response tidak valid, menggunakan manual filling")
                
        else:
            print(f"[ERROR] Gemma API error: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Gemma API exception: {e}")
    
    # Fallback ke manual filling
    print("[INFO] Using manual template filling")
    return fill_template_manual(html_template, field_mapping)

def fill_template_manual(html_template: str, field_mapping: dict) -> str:
    """
    Fallback manual untuk mengisi template
    """
    filled_html = html_template
    
    print("[INFO] Manual filling started...")
    
    # Ganti semua placeholder
    for field, value in field_mapping.items():
        placeholder = f"{{{{{field}}}}}"
        if placeholder in filled_html:
            filled_html = filled_html.replace(placeholder, str(value))
            print(f"[DEBUG] Replaced {placeholder} with {value}")
        else:
            print(f"[WARNING] Placeholder {placeholder} not found in template")
    
    # Handle Jinja2 loops untuk lampiran (hapus karena tidak ada data)
    lampiran_pattern = r'{%\s*for\s+.*?%}.*?{%\s*endfor\s*%}'
    if re.search(lampiran_pattern, filled_html, re.DOTALL):
        filled_html = re.sub(lampiran_pattern, '', filled_html, flags=re.DOTALL)
        print("[INFO] Removed lampiran loop")
    
    # Cek apakah masih ada placeholder yang belum terisi
    remaining_placeholders = re.findall(r'\{\{(\w+)\}\}', filled_html)
    if remaining_placeholders:
        print(f"[WARNING] Remaining placeholders: {remaining_placeholders}")
        # Isi dengan default
        for placeholder in remaining_placeholders:
            filled_html = filled_html.replace(f"{{{{{placeholder}}}}}", "Akan ditentukan kemudian")
    
    print("[INFO] Manual filling completed")
    return filled_html

def number_to_words_id(num_str: str) -> str:
    """
    Convert number string to Indonesian words
    """
    try:
        # Extract number from string like "Rp 3.500.000"
        num = re.sub(r'[^\d]', '', num_str)
        if not num:
            return "Akan ditentukan kemudian"
        
        amount = int(num)
        if amount >= 1000000000:
            return f"{amount // 1000000000} Milyar"
        elif amount >= 1000000:
            return f"{amount // 1000000} Juta"
        elif amount >= 1000:
            return f"{amount // 1000} Ribu"
        else:
            return str(amount)
    except Exception as e:
        print(f"[ERROR] Number conversion error: {e}")
        return "Akan ditentukan kemudian"