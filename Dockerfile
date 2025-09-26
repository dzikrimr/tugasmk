# Gunakan image Python resmi
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies sistem + Tesseract + Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ind \
    poppler-utils \
    libglib2.0-0 \
    xfonts-75dpi \
    xfonts-base \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf manual (static build, tidak perlu libjpeg-turbo8)
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6-1/wkhtmltox_0.12.6-1_linux-generic-amd64.tar.xz \
    && tar -xvf wkhtmltox_0.12.6-1_linux-generic-amd64.tar.xz \
    && cp wkhtmltox/bin/wkhtmltopdf /usr/local/bin/ \
    && rm -rf wkhtmltox wkhtmltox_0.12.6-1_linux-generic-amd64.tar.xz

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
