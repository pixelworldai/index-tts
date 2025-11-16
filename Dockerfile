# IndexTTS2 RunPod Serverless Dockerfile
# Optimized for 24GB VRAM GPUs (RTX 4090, L4, A5000)

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HUB_CACHE=/workspace/checkpoints/hf_cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-dev \
    git \
    git-lfs \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Set working directory
WORKDIR /workspace

# Copy requirements first (for better layer caching)
COPY requirements.txt /workspace/requirements.txt

# Install Python dependencies
# Install PyTorch with CUDA support first
RUN pip install --no-cache-dir \
    torch==2.5.1 \
    torchaudio==2.5.1 \
    --extra-index-url https://download.pytorch.org/whl/cu121

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /workspace/

# Install the indextts package in editable mode
RUN pip install --no-cache-dir -e .

# Download IndexTTS-2 model checkpoints from HuggingFace
RUN pip install --no-cache-dir "huggingface-hub[cli,hf_xet]" && \
    huggingface-cli download IndexTeam/IndexTTS-2 --local-dir /workspace/checkpoints

# Verify critical files exist
RUN ls -la /workspace/irish_voice.wav && \
    ls -la /workspace/checkpoints/config.yaml && \
    ls -la /workspace/rp_handler.py

# Pre-download small models that get auto-downloaded on first run
# This prevents cold start delays
RUN python3 -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')" || true

# Set cache directories
ENV TRANSFORMERS_CACHE=/workspace/checkpoints/hf_cache
ENV HF_HOME=/workspace/checkpoints/hf_cache

# RunPod serverless entry point
CMD ["python3", "-u", "rp_handler.py"]
