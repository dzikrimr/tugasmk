from transformers import pipeline
import re

# Load IndoBERT NER pipeline
ner_pipeline = pipeline(
    "token-classification",
    model="cahya/bert-base-indonesian-NER",
    aggregation_strategy="simple"  # supaya hasil entitas gabungan, bukan pecahan token
)

def extract_entities(text: str):
    """
    Ambil entitas dari teks dengan IndoBERT + regex (DATE, MONEY, TIME).
    Output dalam bentuk dict JSON.
    """

    # Hasil IndoBERT
    entities = ner_pipeline(text)

    orgs, pers, locs = [], [], []
    for ent in entities:
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

    # Gabungan hasil
    return {
        "ORG": list(set(orgs)),
        "PER": list(set(pers)),
        "LOC": list(set(locs)),
        "MONEY": list(set(money)),
        "DATE": list(set(date)),
        "TIME": list(set(duration))
    }
