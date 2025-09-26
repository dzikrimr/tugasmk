# Gunakan Python resmi
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies sistem + Tesseract + Poppler + font + wget
RUN apt-get update && apt-get install -y \
    wget \
    xfonts-75dpi xfonts-base \
    tesseract-ocr tesseract-ocr-ind \
    poppler-utils \
    libglib2.0-0 \
    libssl3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install libjpeg-turbo8 (dependency wkhtmltox)
RUN wget http://mirrors.kernel.org/ubuntu/pool/main/libj/libjpeg-turbo/libjpeg-turbo8_2.1.2-0ubuntu1_amd64.deb \
    && dpkg -i libjpeg-turbo8_2.1.2-0ubuntu1_amd64.deb \
    && rm libjpeg-turbo8_2.1.2-0ubuntu1_amd64.deb

# Install wkhtmltopdf (.deb untuk Jammy)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2_linux-generic-amd64.tar.xz \
    && tar -xf wkhtmltox_0.12.6.1-2_linux-generic-amd64.tar.xz \
    && cp wkhtmltox/bin/wkhtmltopdf /usr/local/bin/ \
    && rm -rf wkhtmltox wkhtmltox_0.12.6.1-2_linux-generic-amd64.tar.xz

# Salin requirements.txt dan install dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file project
COPY . .

# Expose port FastAPI
EXPOSE 8000

# Jalankan Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
