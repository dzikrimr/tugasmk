import requests
import json
import re
from datetime import datetime, timedelta

OLLAMA_BASE_URL = "https://ollama.elginbrian.com"
MODEL_NAME = "gemma"

def number_to_words_id(num_str: str) -> str:
    """
    Convert number string (ex: Rp 3.500.000) ke tulisan Indonesia.
    """
    try:
        num = re.sub(r'[^\d]', '', num_str)
        if not num:
            return "Akan ditentukan kemudian"
        amount = int(num)

        ones = ['', 'Satu', 'Dua', 'Tiga', 'Empat', 'Lima', 'Enam', 'Tujuh', 'Delapan', 'Sembilan']
        teens = ['Sepuluh', 'Sebelas', 'Dua Belas', 'Tiga Belas', 'Empat Belas', 'Lima Belas',
                 'Enam Belas', 'Tujuh Belas', 'Delapan Belas', 'Sembilan Belas']
        tens = ['', '', 'Dua Puluh', 'Tiga Puluh', 'Empat Puluh', 'Lima Puluh',
                'Enam Puluh', 'Tujuh Puluh', 'Delapan Puluh', 'Sembilan Puluh']

        if amount == 0:
            return "Nol Rupiah"
        elif amount < 10:
            return f"{ones[amount]} Rupiah"
        elif amount < 20:
            return f"{teens[amount - 10]} Rupiah"
        elif amount < 100:
            return f"{tens[amount // 10]} {ones[amount % 10]}".strip() + " Rupiah"
        elif amount < 1000:
            hundreds = amount // 100
            remainder = amount % 100
            result = f"{ones[hundreds]} Ratus" if hundreds > 1 else "Seratus"
            if remainder > 0:
                result += " " + number_to_words_id(str(remainder)).replace(" Rupiah", "")
            return result + " Rupiah"
        elif amount < 1000000:
            thousands = amount // 1000
            remainder = amount % 1000
            result = "Seribu" if thousands == 1 else number_to_words_id(str(thousands)).replace(" Rupiah", "") + " Ribu"
            if remainder > 0:
                result += " " + number_to_words_id(str(remainder)).replace(" Rupiah", "")
            return result + " Rupiah"
        elif amount < 1000000000:
            millions = amount // 1000000
            remainder = amount % 1000000
            result = number_to_words_id(str(millions)).replace(" Rupiah", "") + " Juta"
            if remainder > 0:
                result += " " + number_to_words_id(str(remainder)).replace(" Rupiah", "")
            return result + " Rupiah"
        else:
            return f"{amount:,} Rupiah"
    except:
        return "Akan ditentukan kemudian"

def extract_mapping_from_entities(entities: dict) -> dict:
    """
    Ekstrak entitas hasil OCR/NER lalu mapping ke placeholder template kontrak.
    """
    mapping = {}

    # ORG → perusahaan pihak kedua
    orgs = entities.get("ORG", [])
    if orgs:
        candidates = [o for o in orgs if len(o) > 4]
        if candidates:
            mapping['pihak2_company'] = candidates[0].title()

    # PER → nama perwakilan
    persons = entities.get("PER", [])
    if persons:
        valid_persons = [p.title() for p in persons if not p.startswith("##") and len(p) > 3]
        if valid_persons:
            mapping['pihak1_name'] = valid_persons[0]
        if len(valid_persons) > 1:
            mapping['pihak2_name'] = valid_persons[1]

    # LOC → alamat
    locs = entities.get("LOC", [])
    if locs:
        best_loc = max(locs, key=len)
        mapping['pihak1_address'] = best_loc.title()
        mapping['pihak2_address'] = best_loc.title()

    # MONEY → nilai kontrak
    money = entities.get("MONEY", [])
    if money:
        amounts = []
        for m in money:
            num_str = re.sub(r"[^\d]", "", m)
            if num_str:
                amounts.append((int(num_str), m))
        if amounts:
            max_amt = max(amounts, key=lambda x: x[0])
            mapping['contract_value'] = max_amt[1]
            mapping['contract_value_words'] = number_to_words_id(max_amt[1])

    # DATE → tanggal kontrak
    dates = entities.get("DATE", [])
    if dates:
        mapping['contract_date'] = dates[0]
        mapping['start_date'] = dates[0]
        mapping['end_date'] = dates[-1]

    # Defaults (kalau entitas nggak lengkap)
    defaults = {
        "contract_number": f"ILCS/{datetime.now().year}/{datetime.now().month:02d}/{datetime.now().day:02d}",
        "contract_date": datetime.now().strftime("%d %B %Y"),

        "pihak1_name": "Direktur Utama ILCS",
        "pihak1_company": "PT Integrasi Logistik Cipta Solusi",
        "pihak1_address": "Jakarta, Indonesia",
        "pihak1_position": "Direktur Utama",
        "pihak1_npwp": "01.234.567.8-999.000",

        "pihak2_name": "Nama Perwakilan Mitra",
        "pihak2_company": "Perusahaan Mitra",
        "pihak2_address": "Alamat Mitra",
        "pihak2_position": "Direktur",
        "pihak2_npwp": "09.876.543.2-111.000",
        "pihak2_bank_account": "Bank ABC 1234567890",

        "scope_of_work": "Pekerjaan sesuai proposal dan lampiran.",
        "contract_value": "Rp 10.000.000",
        "contract_value_words": "Sepuluh Juta Rupiah",
        "payment_terms": "Pembayaran 2 termin sesuai progres",
        "penalty_percentage": "2% per hari keterlambatan",
        "force_majeure_days": "7",
        "start_date": datetime.now().strftime("%d %B %Y"),
        "end_date": (datetime.now() + timedelta(days=90)).strftime("%d %B %Y"),
        "terms": "Penyelesaian sengketa melalui musyawarah atau arbitrase."
    }

    # Merge default kalau kosong
    for k, v in defaults.items():
        if k not in mapping:
            mapping[k] = v

    return mapping

def fill_template_with_gemma(template_path: str, entities: dict) -> str:
    """
    Isi template HTML kontrak pakai Gemma.
    """
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    field_mapping = extract_mapping_from_entities(entities)

    prompt = f"""
Ganti semua placeholder {{...}} dalam template berikut dengan data kontrak.

Data:
{json.dumps(field_mapping, indent=2, ensure_ascii=False)}

Template:
{html_template}

Outputkan hanya HTML penuh yang sudah terisi.
"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        html = result.get("response", "").strip()

        if html and "{{" not in html:
            return html
        else:
            # fallback manual replace
            return fill_template_manual(html_template, field_mapping)
    except Exception as e:
        print(f"[Gemma error] {e}")
        return fill_template_manual(html_template, field_mapping)

def fill_template_manual(html_template: str, field_mapping: dict) -> str:
    """
    Fallback: ganti placeholder manual.
    """
    html = html_template
    for key, val in field_mapping.items():
        html = html.replace(f"{{{{{key}}}}}", str(val))
    return html
