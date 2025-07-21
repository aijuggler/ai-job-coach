from app.services.audio import transcribe_audio, AudioTranscriptionError
import pytest, io

def test_transcribe_dummy(monkeypatch):
    # Monkeypatch Azure call so we don't hit network
    def fake_transcribe(*args, **kw):
        return "dummy transcript"
    monkeypatch.setattr("app.services.audio.transcribe_audio", fake_transcribe)
    assert transcribe_audio(b"123") == "dummy transcript"
