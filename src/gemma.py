import requests
import json

OLLAMA_BASE_URL = "https://ollama.elginbrian.com"  # base URL API Gemma
MODEL_NAME = "gemma"

def fill_template_with_gemma(template_path: str, entities: dict) -> str:
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    prompt = f"""
Isi template HTML kontrak berikut menggunakan data entitas ini: {entities}.
Template:
{html_template}
Hasilkan HTML penuh yang siap dicetak sebagai PDF.
    """

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": True},
            timeout=60,
            stream=True
        )
        response.raise_for_status()

        full_output = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    full_output += data["response"]
                if data.get("done", False):
                    break

        return full_output.strip() if full_output else html_template

    except requests.RequestException as e:
        print(f"[Gemma API error] {e}")
        return html_template
