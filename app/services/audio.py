"""
Azure Speech‑to‑Text wrapper (synchronous, short audio <= 60 s).
Accepts raw bytes (wav/mp3) and returns transcript string.
"""
from __future__ import annotations
import io, os, tempfile
from app.config.settings import settings

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:  # optional dep
    speechsdk = None

class AudioTranscriptionError(Exception):
    ...

def transcribe_audio(audio_bytes: bytes, language: str = "en-US") -> str:
    if not speechsdk:
        raise AudioTranscriptionError("azure-cognitiveservices-speech not installed.")
    if not (settings.azure_speech_key and settings.azure_speech_region):
        raise AudioTranscriptionError("Azure Speech credentials missing in env.")

    # Azure SDK needs a file or stream that supports seek().
    # Wrap bytes in BytesIO; create PullAudioInputStream.
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_wav.write(audio_bytes)
    temp_wav.flush()

    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    speech_config.speech_recognition_language = language

    audio_input = speechsdk.AudioConfig(filename=temp_wav.name)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = recognizer.recognize_once()
    os.unlink(temp_wav.name)

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text.strip()
    else:
        raise AudioTranscriptionError(f"Speech recognition failed: {result.reason}")
