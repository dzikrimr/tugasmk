import re

def clean_text(text):
    """
    Basic text cleaning: remove newlines, normalize spaces, etc.
    """
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize_money(text):
    """
    Regex helper untuk cari nominal uang dalam teks.
    """
    money_pattern = re.findall(r"Rp[\s]?[0-9\.\,]+", text)
    return money_pattern

def normalize_duration(text):
    """
    Regex helper untuk cari durasi (contoh: '12 bulan').
    """
    duration_pattern = re.findall(r"\d+\s+bulan", text.lower())
    return duration_pattern
