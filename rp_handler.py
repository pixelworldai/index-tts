"""
RunPod Serverless Handler for IndexTTS2
Provides emotion-controlled text-to-speech with base64 audio I/O
"""
import os
import io
import base64
import tempfile
import traceback
from typing import Dict, Any, Optional

import runpod
import torch
import torchaudio
import numpy as np

# Set up model cache directory
os.environ['HF_HUB_CACHE'] = './checkpoints/hf_cache'

from indextts.infer_v2 import IndexTTS2


# Emotion mapping: name -> vector position
EMOTION_MAP = {
    "happy": 0,
    "angry": 1,
    "sad": 2,
    "afraid": 3,
    "disgusted": 4,
    "melancholic": 5,
    "surprised": 6,
    "calm": 7,
}


class IndexTTSHandler:
    """Handler class for IndexTTS2 serverless inference"""

    def __init__(self):
        """Initialize the IndexTTS2 model"""
        print(">> Initializing IndexTTS2 model...")

        # Check if model needs to be downloaded
        if not os.path.exists("checkpoints/config.yaml"):
            print(">> Model not found, downloading from HuggingFace...")
            print(">> This will take a few minutes on first run...")
            try:
                import subprocess
                subprocess.run([
                    "huggingface-cli", "download",
                    "IndexTeam/IndexTTS-2",
                    "--local-dir", "checkpoints"
                ], check=True)
                print(">> Model download complete!")
            except Exception as e:
                print(f">> ERROR: Model download failed: {e}")
                raise

        # Determine device
        if torch.cuda.is_available():
            self.device = "cuda:0"
            print(f">> Using CUDA device: {torch.cuda.get_device_name(0)}")
            print(f">> GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        else:
            self.device = "cpu"
            print(">> WARNING: CUDA not available, using CPU (will be slow)")

        # Initialize model with FP16 for 24GB VRAM optimization
        self.model = IndexTTS2(
            cfg_path="checkpoints/config.yaml",
            model_dir="checkpoints",
            use_fp16=True if self.device.startswith("cuda") else False,
            device=self.device,
            use_cuda_kernel=True if self.device.startswith("cuda") else False,
            use_deepspeed=False,  # Not needed for 24GB VRAM
            use_accel=False,  # Disabled (requires flash_attn which is hard to install)
            use_torch_compile=False  # Disabled for compatibility
        )

        # Load default reference audio
        self.default_reference_path = "irish_voice.wav"
        if not os.path.exists(self.default_reference_path):
            raise FileNotFoundError(
                f"Default reference audio not found: {self.default_reference_path}"
            )

        print(f">> Default reference audio: {self.default_reference_path}")
        print(">> IndexTTS2 initialization complete!")

    def base64_to_audio(self, base64_string: str, sample_rate: int = 24000) -> str:
        """
        Convert base64 string to temporary WAV file

        Args:
            base64_string: Base64-encoded audio data
            sample_rate: Expected sample rate (default: 24000)

        Returns:
            Path to temporary WAV file
        """
        try:
            # Decode base64
            audio_bytes = base64.b64decode(base64_string)

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(audio_bytes)
            temp_file.close()

            # Validate audio file
            try:
                audio, sr = torchaudio.load(temp_file.name)
                # Resample if needed
                if sr != sample_rate:
                    audio = torchaudio.transforms.Resample(sr, sample_rate)(audio)
                    torchaudio.save(temp_file.name, audio, sample_rate)
            except Exception as e:
                os.unlink(temp_file.name)
                raise ValueError(f"Invalid audio file: {str(e)}")

            return temp_file.name

        except Exception as e:
            raise ValueError(f"Failed to decode base64 audio: {str(e)}")

    def audio_to_base64(self, audio_path: str) -> str:
        """
        Convert WAV file to base64 string

        Args:
            audio_path: Path to WAV file

        Returns:
            Base64-encoded audio string
        """
        try:
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encode audio to base64: {str(e)}")

    def create_emotion_vector(self, emotion: str, intensity: float) -> list:
        """
        Create emotion vector from emotion name and intensity

        Args:
            emotion: Emotion name (happy, angry, sad, etc.)
            intensity: Intensity value (0.1 to 1.0)

        Returns:
            8-element emotion vector
        """
        # Validate emotion
        emotion = emotion.lower()
        if emotion not in EMOTION_MAP:
            raise ValueError(
                f"Invalid emotion '{emotion}'. Supported emotions: "
                f"{', '.join(EMOTION_MAP.keys())}"
            )

        # Validate intensity
        intensity = max(0.1, min(1.0, float(intensity)))

        # Create vector with all zeros except target emotion
        vector = [0.0] * 8
        vector[EMOTION_MAP[emotion]] = intensity

        return vector

    def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process TTS request

        Args:
            input_data: Request data containing:
                - text: Text to synthesize
                - emotion: Emotion name
                - intensity: Emotion intensity (0.1-1.0)
                - reference_audio: Optional base64-encoded reference audio

        Returns:
            Dictionary containing base64-encoded audio
        """
        temp_files = []

        try:
            # Extract parameters
            text = input_data.get('text')
            emotion = input_data.get('emotion', 'calm')
            intensity = input_data.get('intensity', 0.5)
            reference_audio_b64 = input_data.get('reference_audio')

            # Validate required parameters
            if not text:
                raise ValueError("Missing required parameter: 'text'")

            if not isinstance(text, str) or len(text.strip()) == 0:
                raise ValueError("Parameter 'text' must be a non-empty string")

            # Limit text length to prevent abuse
            max_text_length = 5000
            if len(text) > max_text_length:
                raise ValueError(
                    f"Text too long ({len(text)} chars). Maximum: {max_text_length}"
                )

            print(f">> Processing: text='{text[:50]}...', emotion={emotion}, intensity={intensity}")

            # Create emotion vector
            emo_vector = self.create_emotion_vector(emotion, intensity)

            # Normalize emotion vector (IndexTTS2 requirement)
            emo_vector = self.model.normalize_emo_vec(emo_vector, apply_bias=True)

            # Handle reference audio
            if reference_audio_b64:
                # Use custom reference audio
                reference_path = self.base64_to_audio(reference_audio_b64)
                temp_files.append(reference_path)
                print(f">> Using custom reference audio")
            else:
                # Use default reference audio
                reference_path = self.default_reference_path
                print(f">> Using default reference audio: {reference_path}")

            # Create temporary output file
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            output_file.close()
            temp_files.append(output_file.name)

            # Run inference
            print(">> Starting TTS inference...")
            result = self.model.infer(
                spk_audio_prompt=reference_path,
                text=text,
                output_path=output_file.name,
                emo_vector=emo_vector,
                verbose=False,
                max_text_tokens_per_segment=120,
                # Generation parameters optimized for quality
                do_sample=True,
                top_p=0.8,
                top_k=30,
                temperature=1.0,
                length_penalty=0.0,
                num_beams=3,
                repetition_penalty=10.0,
                max_mel_tokens=600
            )

            if result is None:
                raise RuntimeError("TTS inference failed to generate audio")

            # Convert output to base64
            print(">> Encoding output audio...")
            audio_base64 = self.audio_to_base64(output_file.name)

            return {
                "audio": audio_base64,
                "metadata": {
                    "emotion": emotion,
                    "intensity": intensity,
                    "emotion_vector": emo_vector,
                    "text_length": len(text),
                    "sample_rate": 24000,
                    "format": "wav"
                }
            }

        except Exception as e:
            # Return error with details
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            print(f">> ERROR: {error_msg}")
            print(stack_trace)

            raise RuntimeError(f"TTS processing failed: {error_msg}")

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f">> Warning: Failed to delete temp file {temp_file}: {e}")


# Global handler instance (initialized once, reused across requests)
tts_handler = None


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler function

    Args:
        event: RunPod event containing 'input' data

    Returns:
        Response dictionary with audio data or error
    """
    global tts_handler

    # Initialize handler on first request (lazy loading)
    if tts_handler is None:
        print(">> First request - initializing handler...")
        tts_handler = IndexTTSHandler()

    # Extract input data
    input_data = event.get('input', {})

    try:
        # Process request
        result = tts_handler.process_request(input_data)
        print(">> Request completed successfully")
        return result

    except Exception as e:
        # Return error in RunPod format
        error_response = {
            "error": str(e),
            "error_type": type(e).__name__
        }
        print(f">> Request failed: {error_response}")
        return error_response


# Start RunPod serverless worker
if __name__ == '__main__':
    print(">> Starting RunPod serverless worker...")
    runpod.serverless.start({'handler': handler})
