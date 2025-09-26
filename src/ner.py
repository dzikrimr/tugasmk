from transformers import pipeline, AutoTokenizer
import re

# Load IndoBERT NER pipeline
ner_pipeline = pipeline(
    "token-classification",
    model="cahya/bert-base-indonesian-NER",
    aggregation_strategy="simple"
)

tokenizer = AutoTokenizer.from_pretrained("cahya/bert-base-indonesian-NER")

def chunk_text(text, max_length=512):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_length):
        chunks.append(" ".join(words[i:i+max_length]))
    return chunks

def extract_entities(text: str):
    """
    Ambil entitas dari teks dengan IndoBERT + regex (DATE, MONEY, TIME).
    Split teks panjang agar tidak error tensor mismatch.
    """
    all_entities = []
    text_chunks = chunk_text(text, max_length=512)

    for chunk in text_chunks:
        all_entities.extend(ner_pipeline(chunk))

    orgs, pers, locs = [], [], []
    for ent in all_entities:
        if ent["entity_group"] == "ORG":
            orgs.append(ent["word"])
        elif ent["entity_group"] == "PER":
            pers.append(ent["word"])
        elif ent["entity_group"] == "LOC":
            locs.append(ent["word"])

    # Regex tambahan
    money_pattern = r"Rp\s?[\d\.\,]+"
    date_pattern = r"\b(\d{1,2}\s(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s\d{4})\b"
    time_pattern = r"\b(\d+\s(?:hari|bulan|tahun))\b"

    money = re.findall(money_pattern, text)
    date = re.findall(date_pattern, text, flags=re.IGNORECASE)
    duration = re.findall(time_pattern, text, flags=re.IGNORECASE)

    return {
        "ORG": list(set(orgs)),
        "PER": list(set(pers)),
        "LOC": list(set(locs)),
        "MONEY": list(set(money)),
        "DATE": list(set(date)),
        "TIME": list(set(duration))
    }
