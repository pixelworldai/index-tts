# IndexTTS2 RunPod Serverless Dockerfile
# Using RunPod's official PyTorch base image

FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt /workspace/requirements.txt

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install RunPod SDK first
RUN pip install --no-cache-dir runpod

# Install core dependencies (without torch since it's in base image)
RUN pip install --no-cache-dir \
    accelerate==1.8.1 \
    cn2an==0.5.22 \
    einops>=0.8.1 \
    librosa==0.10.2.post1 \
    omegaconf>=2.3.0 \
    transformers==4.52.1 \
    torchaudio \
    safetensors==0.5.2 \
    sentencepiece>=0.2.1

# Install remaining dependencies
RUN pip install --no-cache-dir \
    cython==3.0.7 \
    descript-audiotools==0.7.2 \
    ffmpeg-python==0.2.0 \
    g2p-en==2.1.0 \
    jieba==0.42.1 \
    json5==0.10.0 \
    keras==2.9.0 \
    matplotlib==3.8.2 \
    modelscope==1.27.0 \
    munch==4.0.0 \
    numba==0.58.1 \
    numpy==1.26.2 \
    opencv-python==4.9.0.80 \
    pandas==2.3.2 \
    tensorboard==2.9.1 \
    textstat>=0.7.10 \
    tokenizers==0.21.0 \
    tqdm>=4.67.1 \
    WeTextProcessing

# Copy application code
COPY . /workspace/

# Install indextts package
RUN pip install --no-cache-dir -e .

# Create checkpoints directory
RUN mkdir -p /workspace/checkpoints

# Download model checkpoints using huggingface-cli
RUN pip install --no-cache-dir "huggingface-hub[cli]" && \
    huggingface-cli download IndexTeam/IndexTTS-2 --local-dir /workspace/checkpoints && \
    echo "Model download complete"

# Verify critical files
RUN echo "Verifying files..." && \
    ls -lh /workspace/irish_voice.wav && \
    ls -lh /workspace/checkpoints/config.yaml && \
    ls -lh /workspace/rp_handler.py && \
    echo "All files verified!"

# Set environment variables
ENV HF_HOME=/workspace/checkpoints/hf_cache
ENV TRANSFORMERS_CACHE=/workspace/checkpoints/hf_cache

# Pre-download Qwen tokenizer (optional, prevents first-run delay)
RUN python3 -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')" || echo "Qwen download skipped"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import runpod; print('OK')" || exit 1

# RunPod serverless entry point
CMD ["python3", "-u", "rp_handler.py"]
