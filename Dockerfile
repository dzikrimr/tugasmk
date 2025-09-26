# Gunakan image Python resmi
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Tesseract OCR + Poppler + Indo language
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ind \
    poppler-utils \
    libglib2.0-0 \
    xfonts-75dpi \
    xfonts-base \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Salin requirements.txt
COPY requirements.txt .

# Install dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file project ke container
COPY . .

# Expose port FastAPI
EXPOSE 8000

# Jalankan Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
