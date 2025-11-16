# IndexTTS2 RunPod Serverless Deployment Guide

Complete guide for deploying IndexTTS2 as a RunPod serverless endpoint with emotion control and base64 audio I/O.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Steps](#deployment-steps)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Performance & Optimization](#performance--optimization)
- [Cost Estimation](#cost-estimation)

---

## Overview

This deployment provides a serverless TTS endpoint with:

- **8 Emotion Controls**: happy, angry, sad, afraid, disgusted, melancholic, surprised, calm
- **Intensity Scaling**: Fine-tune emotion strength (0.1 to 1.0)
- **Base64 Audio I/O**: Seamless integration with n8n and other workflow tools
- **Voice Cloning**: Use custom reference audio or default Irish voice
- **GPU Optimization**: Configured for 24GB VRAM GPUs with FP16 inference

### Architecture

```
User Request (JSON + base64) → RunPod Endpoint → IndexTTS2 Model → Base64 Audio Response
```

---

## Prerequisites

### 1. RunPod Account

- Create account at [runpod.io](https://www.runpod.io)
- Add credits to your account
- Have a private GitHub repository ready (fork of index-tts)

### 2. GitHub Repository

Since you're using RunPod's GitHub integration:

1. **Fork this repository** to your private GitHub account
2. Ensure `irish_voice.wav` is included (default reference voice)
3. Push all deployment files to your fork:
   - `rp_handler.py`
   - `Dockerfile`
   - `requirements.txt`
   - `.dockerignore`

### 3. GPU Requirements

**Recommended**: 24GB VRAM GPUs

- RTX 4090
- NVIDIA L4
- NVIDIA A5000
- RTX 6000 Ada

**Minimum**: 16GB VRAM (may require adjustments)

---

## Quick Start

### Option 1: RunPod GitHub Integration (Recommended)

1. **Connect GitHub Repository**
   - Go to RunPod Console → Serverless → Endpoints
   - Click "New Endpoint"
   - Select "GitHub" as source
   - Connect your private fork repository
   - RunPod will automatically build from your Dockerfile

2. **Configure Endpoint**
   - Name: `indextts2-emotion`
   - GPU: Select 24GB VRAM option (RTX 4090 / L4 / A5000)
   - Workers: Start with 0 min, 3 max (auto-scaling)
   - Idle Timeout: 5 seconds
   - Execution Timeout: 600 seconds (10 min)

3. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (~15-20 minutes first time)
   - Note your endpoint ID and API key

4. **Test**
   - Use the test input from `test_input.json`
   - See [Testing](#testing) section below

---

## Deployment Steps

### Step 1: Prepare Your Repository

Ensure these files are in your GitHub repository:

```
index-tts/
├── rp_handler.py              # RunPod handler with emotion logic
├── Dockerfile                 # Docker build configuration
├── requirements.txt           # Python dependencies
├── .dockerignore             # Build optimization
├── irish_voice.wav           # Default reference audio
├── indextts/                 # IndexTTS2 source code
│   ├── infer_v2.py
│   ├── gpt/
│   └── ...
└── README_RUNPOD.md          # This file
```

### Step 2: RunPod Configuration

**Container Configuration:**
- Container Disk: 20GB minimum
- Environment Variables: None required (all set in Dockerfile)

**GPU Settings:**
```
GPU Type: RTX 4090 / L4 / A5000
GPU Count: 1
VRAM: 24GB
```

**Scaling Settings:**
```
Min Workers: 0 (no idle cost)
Max Workers: 3 (or based on demand)
GPUs Per Worker: 1
Idle Timeout: 5 seconds
Execution Timeout: 600 seconds
```

**Advanced Settings:**
```
Flash Boot: Disabled (not needed)
Streaming: Disabled
```

### Step 3: Build & Deploy

RunPod will automatically:

1. Clone your GitHub repository
2. Build Docker image using your Dockerfile
3. Download IndexTTS-2 model (~15GB)
4. Deploy workers on demand

**Expected Build Time**: 15-20 minutes (first time)

**Build Steps in Dockerfile**:
- Install CUDA 12.8 base image
- Install system dependencies (ffmpeg, libsndfile, etc.)
- Install Python dependencies
- Download IndexTTS-2 model from HuggingFace
- Pre-cache small models (Qwen tokenizer)

---

## API Reference

### Endpoint URL

```
https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync
```

Replace `{ENDPOINT_ID}` with your actual endpoint ID from RunPod console.

### Authentication

Include your API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

### Request Format

**Endpoint**: POST `/runsync`

**Headers**:
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer YOUR_API_KEY"
}
```

**Body**:
```json
{
  "input": {
    "text": "The text to synthesize into speech",
    "emotion": "calm",
    "intensity": 0.5,
    "reference_audio": null
  }
}
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | ✅ Yes | - | Text to convert to speech (max 5000 chars) |
| `emotion` | string | ✅ Yes | - | Emotion name (see supported emotions) |
| `intensity` | float | ✅ Yes | - | Emotion intensity (0.1 to 1.0) |
| `reference_audio` | string | ❌ No | null | Base64-encoded WAV audio for voice cloning |

### Supported Emotions

| Emotion | Description | Vector Position |
|---------|-------------|-----------------|
| `happy` | Joyful, cheerful expression | 0 |
| `angry` | Intense, forceful expression | 1 |
| `sad` | Sorrowful, melancholic expression | 2 |
| `afraid` | Fearful, anxious expression | 3 |
| `disgusted` | Repulsed, distasteful expression | 4 |
| `melancholic` | Low, depressed expression | 5 |
| `surprised` | Shocked, amazed expression | 6 |
| `calm` | Neutral, peaceful expression | 7 |

### Response Format

**Success Response**:
```json
{
  "audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
  "metadata": {
    "emotion": "calm",
    "intensity": 0.5,
    "emotion_vector": [0, 0, 0, 0, 0, 0, 0, 0.4],
    "text_length": 42,
    "sample_rate": 24000,
    "format": "wav"
  }
}
```

**Error Response**:
```json
{
  "error": "Invalid emotion 'excited'. Supported emotions: happy, angry, sad, afraid, disgusted, melancholic, surprised, calm",
  "error_type": "ValueError"
}
```

### Output Audio Specifications

- **Format**: WAV
- **Sample Rate**: 24000 Hz
- **Channels**: Mono
- **Encoding**: Base64 string
- **Quality**: High-fidelity voice cloning

---

## Testing

### Test Input File

Create `test_input.json`:

```json
{
  "input": {
    "text": "They call it Quad HD or QHD, and yep, it's way sharper than your basic 1080p.",
    "emotion": "calm",
    "intensity": 0.5
  }
}
```

### Using cURL

```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @test_input.json
```

### Using Python

```python
import requests
import base64
import json

# Configuration
ENDPOINT_ID = "your-endpoint-id"
API_KEY = "your-api-key"
URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"

# Request payload
payload = {
    "input": {
        "text": "Oh wow! This is absolutely incredible!",
        "emotion": "surprised",
        "intensity": 0.8
    }
}

# Make request
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

response = requests.post(URL, json=payload, headers=headers)
result = response.json()

# Decode and save audio
if "audio" in result:
    audio_data = base64.b64decode(result["audio"])
    with open("output.wav", "wb") as f:
        f.write(audio_data)
    print("Audio saved to output.wav")
    print("Metadata:", result.get("metadata"))
else:
    print("Error:", result.get("error"))
```

### Using n8n

1. **HTTP Request Node**
   - Method: POST
   - URL: `https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync`
   - Authentication: Header Auth
     - Name: `Authorization`
     - Value: `Bearer YOUR_API_KEY`
   - Body:
     ```json
     {
       "input": {
         "text": "{{ $json.text }}",
         "emotion": "{{ $json.emotion }}",
         "intensity": {{ $json.intensity }}
       }
     }
     ```

2. **Function Node** (Decode Base64 Audio)
   ```javascript
   const audioBase64 = $input.item.json.audio;
   const audioBuffer = Buffer.from(audioBase64, 'base64');

   return {
     binary: {
       data: {
         data: audioBuffer.toString('base64'),
         mimeType: 'audio/wav',
         fileName: 'output.wav'
       }
     }
   };
   ```

3. **Write Binary File Node**
   - File Name: `output.wav`
   - Binary Property: `data`

### Testing Different Emotions

```json
// Happy emotion
{
  "input": {
    "text": "I'm so excited! This is the best day ever!",
    "emotion": "happy",
    "intensity": 0.9
  }
}

// Angry emotion
{
  "input": {
    "text": "This is completely unacceptable! I demand to speak with a manager!",
    "emotion": "angry",
    "intensity": 0.7
  }
}

// Sad emotion
{
  "input": {
    "text": "I can't believe it's over. Everything we worked for is gone.",
    "emotion": "sad",
    "intensity": 0.6
  }
}

// Calm/neutral
{
  "input": {
    "text": "The meeting is scheduled for 3 PM in conference room B.",
    "emotion": "calm",
    "intensity": 0.5
  }
}
```

### Testing Custom Voice

```python
import base64

# Load your custom voice sample
with open("my_voice.wav", "rb") as f:
    voice_data = f.read()
    voice_base64 = base64.b64encode(voice_data).decode('utf-8')

# Request with custom voice
payload = {
    "input": {
        "text": "This is a test with my custom voice.",
        "emotion": "calm",
        "intensity": 0.5,
        "reference_audio": voice_base64
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. Cold Start Timeout

**Symptom**: First request times out

**Solution**:
- Cold starts take 30-60 seconds for model loading
- Increase execution timeout to 600 seconds
- Consider keeping 1 min worker active during business hours

#### 2. Out of Memory (OOM)

**Symptom**: Worker crashes during inference

**Solution**:
- Ensure using 24GB VRAM GPU
- Check that FP16 is enabled in handler
- Reduce `max_mel_tokens` in generation params
- Limit text length to <1000 characters per request

#### 3. Invalid Audio Output

**Symptom**: Generated audio is corrupted or silent

**Solution**:
- Verify input text is valid UTF-8
- Check emotion name spelling (must be exact)
- Ensure intensity is between 0.1 and 1.0
- Validate reference audio is WAV format, 24kHz sample rate

#### 4. Slow Inference

**Symptom**: Requests take >30 seconds

**Solution**:
- Verify GPU is being used (check logs for CUDA messages)
- Enable `use_cuda_kernel=True` in handler
- Use FP16 inference
- Consider using shorter text segments

#### 5. Model Download Failures

**Symptom**: Docker build fails downloading checkpoints

**Solution**:
- Check HuggingFace is accessible from RunPod
- Verify model name: `IndexTeam/IndexTTS-2`
- Use ModelScope mirror if HuggingFace is slow:
  ```dockerfile
  RUN pip install modelscope && \
      modelscope download --model IndexTeam/IndexTTS-2 --local_dir /workspace/checkpoints
  ```

### Debugging Tips

**View Logs**:
- RunPod Console → Your Endpoint → Logs tab
- Check for initialization messages
- Look for GPU detection confirmation

**Test Locally** (optional):
```bash
# Run handler locally for debugging
python rp_handler.py

# In another terminal, simulate RunPod request
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"input": {"text": "test", "emotion": "calm", "intensity": 0.5}}'
```

---

## Performance & Optimization

### Expected Performance

| Metric | Value |
|--------|-------|
| Cold Start | 30-60 seconds |
| Warm Inference (short text) | 2-5 seconds |
| Warm Inference (long text) | 5-15 seconds |
| GPU Memory Usage | 8-12 GB |
| Max Concurrent Requests/GPU | 1 (sequential) |

### Optimization Strategies

#### 1. Reduce Cold Starts

```yaml
# Keep 1 worker warm during business hours
Min Workers: 1 (9 AM - 5 PM)
Min Workers: 0 (off-hours)
```

#### 2. Batch Processing

For multiple texts, send separate requests (model doesn't support batching in handler).

#### 3. Text Segmentation

Long texts (>500 chars) are automatically segmented. Adjust in handler:

```python
max_text_tokens_per_segment=120  # Default
max_text_tokens_per_segment=80   # More segments, faster (more memory)
max_text_tokens_per_segment=150  # Fewer segments, slower (less memory)
```

#### 4. Memory Management

Monitor GPU memory:
```python
import torch
print(f"GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
```

Adjust `max_mel_tokens` if needed:
```python
max_mel_tokens=600  # Default
max_mel_tokens=400  # Reduce for memory savings
```

---

## Cost Estimation

### RunPod Serverless Pricing (Approximate)

**GPU Costs** (per second, active time only):

| GPU Type | Cost/sec | Cost/min | Cost/hour (if active) |
|----------|----------|----------|----------------------|
| RTX 4090 | $0.00014 | $0.0084 | $0.50 |
| NVIDIA L4 | $0.00012 | $0.0072 | $0.43 |
| A5000 | $0.00018 | $0.0108 | $0.65 |

**Example Usage**:

```
Scenario: 1000 requests/day, avg 5 seconds per request

Daily active time: 1000 × 5 = 5000 seconds = 83.3 minutes
Daily cost (L4): 83.3 × $0.0072 = $0.60/day
Monthly cost: $0.60 × 30 = $18/month
```

**Idle Time**: $0 (serverless scales to zero)

### Cost Optimization Tips

1. **Use Auto-Scaling**: Set min workers to 0
2. **Optimize Inference Speed**: Faster requests = lower costs
3. **Choose Right GPU**: L4 is best price/performance for this workload
4. **Batch User Requests**: Queue requests on your end, send in bursts

---

## Advanced Configuration

### Custom Emotion Vectors

Instead of using predefined emotions, you can provide custom emotion vectors:

```json
{
  "input": {
    "text": "This is a mixed emotion example.",
    "emotion": "calm",  // Still required but overridden
    "intensity": 1.0,
    "custom_emotion_vector": [0.3, 0.1, 0, 0, 0, 0, 0.2, 0.3]
  }
}
```

**Note**: Requires handler modification to accept `custom_emotion_vector`.

### Voice Presets

Create common voice+emotion combinations:

```json
{
  "presets": {
    "narrator_calm": {
      "emotion": "calm",
      "intensity": 0.4,
      "reference_audio": "base64_irish_voice"
    },
    "character_excited": {
      "emotion": "happy",
      "intensity": 0.9,
      "reference_audio": "base64_character_voice"
    }
  }
}
```

---

## Support & Maintenance

### Model Updates

When IndexTTS releases a new version:

1. Update Dockerfile model download command
2. Rebuild Docker image on RunPod
3. Test with existing API requests
4. Update this documentation

### Monitoring

**Key Metrics to Track**:
- Request success rate
- Average inference time
- Cold start frequency
- GPU memory usage
- Error types and frequency

**RunPod Metrics**:
- Available in RunPod Console → Analytics
- Monitor costs, usage patterns, errors

### Logs

Access logs via:
```bash
runpod logs {ENDPOINT_ID}
```

Or through RunPod web console.

---

## License & Credits

- **IndexTTS2**: [Bilibili IndexTTS Team](https://github.com/index-tts/index-tts)
- **RunPod**: Serverless GPU infrastructure
- **License**: See `INDEX_MODEL_LICENSE` and `LICENSE` in repository

---

## FAQ

**Q: Can I use this for commercial purposes?**
A: Check the IndexTTS model license. RunPod serverless is commercial-ready.

**Q: How many requests per second can this handle?**
A: Single GPU handles 1 request at a time. Scale workers for concurrent requests.

**Q: Can I use my own voice?**
A: Yes! Encode your voice sample as base64 and pass in `reference_audio`.

**Q: What languages are supported?**
A: English and Chinese (Simplified). Model was trained on both.

**Q: Can I adjust speech speed?**
A: Not directly via API. This would require handler modifications.

**Q: How long does voice cloning take?**
A: Same as regular inference (2-5 seconds warm). Reference audio is cached.

---

## Next Steps

1. ✅ Fork repository to private GitHub
2. ✅ Deploy to RunPod using GitHub integration
3. ✅ Test with provided examples
4. ✅ Integrate into your application (n8n, API, etc.)
5. ✅ Monitor performance and costs
6. ✅ Optimize based on usage patterns

**Need Help?**
- RunPod Discord: [discord.gg/runpod](https://discord.gg/runpod)
- IndexTTS Issues: [github.com/index-tts/index-tts/issues](https://github.com/index-tts/index-tts/issues)

---

**Last Updated**: 2025-11-16
**Version**: 1.0.0
