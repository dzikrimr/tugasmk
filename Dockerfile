# Gunakan Python resmi
FROM python:3.11-slim

WORKDIR /app

# Salin wkhtmltopdf .deb yang sudah diunduh
COPY wkhtmltox_0.12.6.1-2.jammy_amd64.deb .

# Install dependencies sistem + Tesseract + Poppler + wkhtmltopdf
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ind \
    poppler-utils \
    xfonts-75dpi \
    xfonts-base \
    libglib2.0-0 \
    libssl3 \
    ca-certificates \
    wget \
    && apt install -y ./wkhtmltox_0.12.6.1-2.jammy_amd64.deb \
    && rm -f wkhtmltox_0.12.6.1-2.jammy_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Salin requirements.txt & install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file project
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
