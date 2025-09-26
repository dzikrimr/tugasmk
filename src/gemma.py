import requests

OLLAMA_BASE_URL = "https://ollama.elginbrian.com"  # ganti sesuai base URL
MODEL_NAME = "gemma"

def fill_template_with_gemma(template_path: str, entities: dict) -> str:
    """
    Kirim template HTML + entities ke Gemma, kembalikan HTML yang sudah terisi.
    """
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    prompt = f"""
Isi template HTML kontrak berikut menggunakan data entitas ini: {entities}.
Template:
{html_template}
Hasilkan HTML penuh yang siap dicetak sebagai PDF.
    """

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/models/{MODEL_NAME}/generate",
        json={"prompt": prompt, "max_tokens": 2000}
    )

    response.raise_for_status()
    data = response.json()
    # Asumsi Gemma mengembalikan HTML di field 'text'
    return data.get("text", html_template)
