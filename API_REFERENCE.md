# IndexTTS2 RunPod API Quick Reference

## Endpoint URL
```
POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync
```

## Authentication
```
Authorization: Bearer YOUR_API_KEY
```

## Request Format

### Headers
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer YOUR_API_KEY"
}
```

### Body
```json
{
  "input": {
    "text": "Your text here",
    "emotion": "calm",
    "intensity": 0.5,
    "reference_audio": null
  }
}
```

## Parameters

| Parameter | Type | Required | Range/Options | Default |
|-----------|------|----------|---------------|---------|
| `text` | string | ✅ Yes | 1-5000 chars | - |
| `emotion` | string | ✅ Yes | See emotions below | - |
| `intensity` | float | ✅ Yes | 0.1 - 1.0 | - |
| `reference_audio` | string | ❌ No | Base64 WAV | null (uses irish_voice.wav) |

## Supported Emotions

| Emotion | Use Case | Recommended Intensity |
|---------|----------|----------------------|
| `happy` | Joyful, cheerful | 0.7 - 0.9 |
| `angry` | Forceful, intense | 0.6 - 0.8 |
| `sad` | Sorrowful, melancholic | 0.5 - 0.7 |
| `afraid` | Fearful, anxious | 0.6 - 0.8 |
| `disgusted` | Repulsed, distasteful | 0.6 - 0.8 |
| `melancholic` | Low, depressed | 0.5 - 0.7 |
| `surprised` | Shocked, amazed | 0.7 - 0.9 |
| `calm` | Neutral, peaceful | 0.3 - 0.6 |

## Response Format

### Success
```json
{
  "audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAu...",
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

### Error
```json
{
  "error": "Error message here",
  "error_type": "ValueError"
}
```

## Common Examples

### Basic Request
```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "input": {
      "text": "Hello world!",
      "emotion": "calm",
      "intensity": 0.5
    }
  }'
```

### Happy Emotion
```json
{
  "input": {
    "text": "This is amazing! I love it!",
    "emotion": "happy",
    "intensity": 0.8
  }
}
```

### Angry Emotion
```json
{
  "input": {
    "text": "This is unacceptable!",
    "emotion": "angry",
    "intensity": 0.7
  }
}
```

### Professional/Neutral
```json
{
  "input": {
    "text": "The meeting is at 3 PM.",
    "emotion": "calm",
    "intensity": 0.3
  }
}
```

### Custom Voice
```json
{
  "input": {
    "text": "Using my custom voice.",
    "emotion": "calm",
    "intensity": 0.5,
    "reference_audio": "UklGRiQAAABXQVZF..."
  }
}
```

## Python Example
```python
import requests
import base64

response = requests.post(
    f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    },
    json={
        "input": {
            "text": "Your text here",
            "emotion": "calm",
            "intensity": 0.5
        }
    }
)

result = response.json()
audio_bytes = base64.b64decode(result["audio"])
with open("output.wav", "wb") as f:
    f.write(audio_bytes)
```

## Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing required parameter: 'text'` | No text provided | Include text in input |
| `Invalid emotion 'X'` | Unknown emotion name | Use supported emotion |
| `Text too long` | Text > 5000 chars | Reduce text length |
| `Invalid audio file` | Bad base64 or WAV format | Check reference audio |
| Timeout | Request too slow | Increase timeout or reduce text |

## Performance

| Metric | Value |
|--------|-------|
| Cold Start | 30-60s |
| Warm Request | 2-5s |
| Max Text | 5000 chars |
| Sample Rate | 24000 Hz |
| Audio Format | WAV, Mono |

## Rate Limits

RunPod serverless has no hard rate limits, but:
- Workers scale based on demand (0-3 default)
- Each worker handles 1 request at a time
- Cold starts add latency
- Cost scales with active time

## Tips

1. **Text Length**: Shorter text = faster response
2. **Intensity**: Start with 0.5, adjust based on results
3. **Emotions**: Test different emotions for your use case
4. **Caching**: Same reference audio is cached automatically
5. **Batching**: Send requests sequentially for better quality

## n8n Integration

```javascript
// HTTP Request Node
{
  "method": "POST",
  "url": "https://api.runpod.ai/v2/YOUR_ENDPOINT/runsync",
  "authentication": "headerAuth",
  "headerAuth": {
    "name": "Authorization",
    "value": "Bearer YOUR_API_KEY"
  },
  "body": {
    "input": {
      "text": "{{ $json.text }}",
      "emotion": "{{ $json.emotion }}",
      "intensity": {{ $json.intensity }}
    }
  }
}

// Code Node to decode base64
const audioBase64 = $input.item.json.audio;
const audioBuffer = Buffer.from(audioBase64, 'base64');
return {
  binary: {
    data: audioBuffer.toString('base64')
  }
};
```

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Timeout on first request | Normal - cold start takes 30-60s |
| Audio sounds robotic | Increase intensity (0.7-0.9) |
| Audio too emotional | Decrease intensity (0.3-0.5) |
| Wrong voice | Check reference_audio parameter |
| Empty response | Check RunPod logs for errors |

---

**For full documentation, see `README_RUNPOD.md`**
