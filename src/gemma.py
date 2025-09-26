import requests
import json
import re
from datetime import datetime, timedelta

OLLAMA_BASE_URL = "https://ollama.elginbrian.com"
MODEL_NAME = "gemma"

def extract_mapping_from_entities(entities: dict) -> dict:
    """
    Ekstrak dan mapping entities ke field kontrak ILCS dengan logika yang lebih baik
    """
    mapping = {}
    
    print(f"[DEBUG] Input entities: {entities}")
    
    # Mapping organisasi
    orgs = entities.get("ORG", [])
    if orgs:
        # Cari universitas untuk pihak kedua (mitra)
        universities = [org for org in orgs if 'universitas' in org.lower()]
        if universities:
            mapping['pihak2_company'] = universities[0].title()
            print(f"[DEBUG] Found pihak2_company: {mapping['pihak2_company']}")
        
        # Ambil organisasi lain untuk mitra (yang bukan universitas)
        other_orgs = [org for org in orgs if 'universitas' not in org.lower() and len(org) > 5]
        if other_orgs and not universities:
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
            print(f"[DEBUG] Found pihak1_name: {mapping['pihak1_name']}")
            
        if len(valid_persons) >= 2:
            mapping['pihak2_name'] = valid_persons[1]
            print(f"[DEBUG] Found pihak2_name: {mapping['pihak2_name']}")
    
    # Mapping lokasi
    locations = entities.get("LOC", [])
    if locations:
        # Ambil alamat yang paling lengkap
        valid_locations = [loc for loc in locations if len(loc) > 10]
        if valid_locations:
            best_location = max(valid_locations, key=len)  # Ambil yang paling panjang
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
    
    # Default values untuk field yang masih kosong sesuai format ILCS
    defaults = {
        'contract_number': f'ILCS/{datetime.now().year}/{str(datetime.now().month).zfill(2)}/{str(datetime.now().day).zfill(2)}',
        'contract_date': datetime.now().strftime('%d %B %Y'),
        
        # Pihak Pertama (ILCS) - Fixed
        'pihak1_name': 'Direktur Utama ILCS',
        'pihak1_company': 'PT Integrasi Logistik Cipta Solusi',
        'pihak1_address': 'Jakarta, Indonesia',
        'pihak1_position': 'Direktur Utama',
        'pihak1_npwp': 'XX.XXX.XXX.X-XXX.XXX',
        
        # Pihak Kedua (Vendor/Mitra) - From entities
        'pihak2_name': 'Nama Perwakilan Mitra',
        'pihak2_company': 'Nama Perusahaan Mitra',
        'pihak2_address': 'Alamat Perusahaan Mitra',
        'pihak2_position': 'Direktur',
        'pihak2_npwp': 'XX.XXX.XXX.X-XXX.XXX',
        'pihak2_bank_account': 'Rekening Bank Mitra',
        
        # Contract Details
        'scope_of_work': 'Layanan logistik dan integrasi sistem sesuai dengan spesifikasi teknis yang telah disepakati bersama',
        'contract_value': 'Rp 10.000.000',
        'contract_value_words': 'Sepuluh Juta Rupiah',
        'payment_terms': 'Pembayaran dilakukan dalam 2 termin',
        'penalty_percentage': '2% per hari keterlambatan',
        'force_majeure_days': '7',
        'start_date': datetime.now().strftime('%d %B %Y'),
        'end_date': (datetime.now() + timedelta(days=90)).strftime('%d %B %Y'),
        'terms': 'Ketentuan teknis dan administratif akan diatur dalam addendum dan lampiran kontrak'
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
- contract_number: {field_mapping.get('contract_number', 'TBD')}
- contract_date: {field_mapping.get('contract_date', 'TBD')}
- pihak1_name: {field_mapping.get('pihak1_name', 'TBD')}
- pihak1_company: {field_mapping.get('pihak1_company', 'TBD')}
- pihak1_address: {field_mapping.get('pihak1_address', 'TBD')}
- pihak1_position: {field_mapping.get('pihak1_position', 'TBD')}
- pihak1_npwp: {field_mapping.get('pihak1_npwp', 'TBD')}
- pihak2_name: {field_mapping.get('pihak2_name', 'TBD')}
- pihak2_company: {field_mapping.get('pihak2_company', 'TBD')}
- pihak2_address: {field_mapping.get('pihak2_address', 'TBD')}
- pihak2_position: {field_mapping.get('pihak2_position', 'TBD')}
- pihak2_npwp: {field_mapping.get('pihak2_npwp', 'TBD')}
- pihak2_bank_account: {field_mapping.get('pihak2_bank_account', 'TBD')}
- scope_of_work: {field_mapping.get('scope_of_work', 'TBD')}
- contract_value: {field_mapping.get('contract_value', 'TBD')}
- contract_value_words: {field_mapping.get('contract_value_words', 'TBD')}
- payment_terms: {field_mapping.get('payment_terms', 'TBD')}
- penalty_percentage: {field_mapping.get('penalty_percentage', 'TBD')}
- force_majeure_days: {field_mapping.get('force_majeure_days', 'TBD')}
- start_date: {field_mapping.get('start_date', 'TBD')}
- end_date: {field_mapping.get('end_date', 'TBD')}
- terms: {field_mapping.get('terms', 'TBD')}

Template:
{html_template[:1000]}...

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
                    "num_predict": 3000
                }
            },
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            filled_html = result.get("response", "").strip()
            
            print(f"[INFO] Gemma response length: {len(filled_html)}")
            
            # Cek apakah Gemma berhasil
            if filled_html and len(filled_html) > 1000 and "{{" not in filled_html:
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
        
        # Basic number to words conversion for Indonesian
        ones = ['', 'Satu', 'Dua', 'Tiga', 'Empat', 'Lima', 'Enam', 'Tujuh', 'Delapan', 'Sembilan']
        teens = ['Sepuluh', 'Sebelas', 'Dua Belas', 'Tiga Belas', 'Empat Belas', 'Lima Belas', 'Enam Belas', 'Tujuh Belas', 'Delapan Belas', 'Sembilan Belas']
        tens = ['', '', 'Dua Puluh', 'Tiga Puluh', 'Empat Puluh', 'Lima Puluh', 'Enam Puluh', 'Tujuh Puluh', 'Delapan Puluh', 'Sembilan Puluh']
        
        if amount == 0:
            return "Nol Rupiah"
        elif amount < 10:
            return f"{ones[amount]} Rupiah"
        elif amount == 10:
            return "Sepuluh Rupiah"
        elif amount < 20:
            return f"{teens[amount - 10]} Rupiah"
        elif amount < 100:
            return f"{tens[amount // 10]} {ones[amount % 10]}".strip() + " Rupiah"
        elif amount == 100:
            return "Seratus Rupiah"
        elif amount < 1000:
            hundreds = amount // 100
            remainder = amount % 100
            result = f"{ones[hundreds] if hundreds > 1 else 'Se'}ratus"
            if remainder > 0:
                if remainder < 10:
                    result += f" {ones[remainder]}"
                elif remainder == 10:
                    result += " Sepuluh"
                elif remainder < 20:
                    result += f" {teens[remainder - 10]}"
                else:
                    result += f" {tens[remainder // 10]} {ones[remainder % 10]}".strip()
            return result + " Rupiah"
        elif amount == 1000:
            return "Seribu Rupiah"
        elif amount < 1000000:
            thousands = amount // 1000
            remainder = amount % 1000
            if thousands == 1:
                result = "Seribu"
            else:
                result = f"{number_to_words_id(str(thousands)).replace(' Rupiah', '')} Ribu"
            if remainder > 0:
                result += f" {number_to_words_id(str(remainder)).replace(' Rupiah', '')}"
            return result + " Rupiah"
        elif amount < 1000000000:
            millions = amount // 1000000
            remainder = amount % 1000000
            result = f"{number_to_words_id(str(millions)).replace(' Rupiah', '')} Juta"
            if remainder > 0:
                result += f" {number_to_words_id(str(remainder)).replace(' Rupiah', '')}"
            return result + " Rupiah"
        elif amount < 1000000000000:
            billions = amount // 1000000000
            remainder = amount % 1000000000
            result = f"{number_to_words_id(str(billions)).replace(' Rupiah', '')} Milyar"
            if remainder > 0:
                result += f" {number_to_words_id(str(remainder)).replace(' Rupiah', '')}"
            return result + " Rupiah"
        else:
            return f"{amount:,} Rupiah"
            
    except Exception as e:
        print(f"[ERROR] Number conversion error: {e}")
        return "Akan ditentukan kemudian"