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

RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6/wkhtmltox_0.12.6-1_linux-generic-amd64.tar.xz \
    && tar -xvf wkhtmltox_0.12.6-1_linux-generic-amd64.tar.xz \
    && cp wkhtmltox/bin/wkhtmltopdf /usr/local/bin/ \
    && rm -rf wkhtmltox wkhtmltox_0.12.6-1_linux-generic-amd64.tar.xz

# Salin dan install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file project
COPY . .

# Expose port
EXPOSE 8000

# Jalankan FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
