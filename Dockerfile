# Gunakan Python resmi
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies sistem untuk WeasyPrint + Tesseract + Poppler + font
RUN apt-get update && apt-get install -y \
    wget \
    xfonts-75dpi xfonts-base \
    tesseract-ocr tesseract-ocr-ind \
    poppler-utils \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    libssl3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Salin requirements.txt dan install dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file project
COPY . .

# Expose port FastAPI
EXPOSE 8000

# Jalankan Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
