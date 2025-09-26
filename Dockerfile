FROM python:3.11-slim

WORKDIR /app

# Install sistem dependencies
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
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf statically linked
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb \
    && apt install -y ./wkhtmltox_0.12.6-1.bionic_amd64.deb \
    && rm -f wkhtmltox_0.12.6-1.bionic_amd64.deb

# Salin dan install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file project
COPY . .

# Expose port
EXPOSE 8000

# Jalankan FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
