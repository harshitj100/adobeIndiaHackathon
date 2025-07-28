# Use Python slim image
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for llama-cpp-python and fitz
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . /app

# Create models folder and download TinyLlama model
RUN mkdir -p models && \
    curl -L -o models/tinyllama-1.1b-chat-v1.0.Q4_0.gguf \
    https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_0.gguf

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt \
 && python -m spacy download en_core_web_sm

# Run main script
CMD ["python", "main.py"]