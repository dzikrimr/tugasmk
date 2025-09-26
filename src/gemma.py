import requests

OLLAMA_BASE_URL = "https://ollama.elginbrian.com"  # base URL API Gemma
MODEL_NAME = "gemma"

def fill_template_with_gemma(template_path: str, entities: dict) -> str:
    """
    Kirim template HTML + entities ke Gemma, kembalikan HTML yang sudah terisi.
    Jika gagal, kembalikan template asli.

    Args:
        template_path (str): path ke file template HTML.
        entities (dict): hasil ekstraksi entities dari /analyze.

    Returns:
        str: HTML kontrak yang sudah diisi Gemma.
    """
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    prompt = f"""
Isi template HTML kontrak berikut menggunakan data entitas ini: {entities}.
Template:
{html_template}
Hasilkan HTML penuh yang siap dicetak sebagai PDF.
    """

    try:
        # Endpoint baru Gemma
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "max_tokens": 2000},
            timeout=30  # mencegah request menggantung terlalu lama
        )
        response.raise_for_status()
        data = response.json()
        # Gemma kemungkinan mengembalikan field 'text'
        return data.get("text", html_template)

    except requests.RequestException as e:
        print(f"[Gemma API error] {e}")
        # fallback ke template asli kalau gagal
        return html_template
