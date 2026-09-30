"""Voice through ElevenLabs (an event tech partner): read text aloud, and transcribe speech.

    from hack import voice
    if voice.available():
        mp3 = voice.speak("Your balance is 1,240 euro.")   -> MP3 bytes, e.g. for st.audio
        text = voice.transcribe(wav_bytes)                  -> str

Needs ELEVENLABS_API_KEY in .env; the app hides voice features without it. The default
voice and models support Dutch and French as well as English.
"""

from functools import cache
from io import BytesIO

from hack.config import env


def available() -> bool:
    return bool(env("ELEVENLABS_API_KEY"))


def speak(text: str) -> bytes:
    audio = _client().text_to_speech.convert(
        voice_id=env("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"),
        text=text,
        model_id=env("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2"),
        output_format="mp3_44100_128",
    )
    return b"".join(audio)


def transcribe(audio: bytes) -> str:
    result = _client().speech_to_text.convert(
        file=BytesIO(audio), model_id=env("ELEVENLABS_STT_MODEL", "scribe_v2")
    )
    return result.text


def reset() -> None:
    _client.cache_clear()


@cache
def _client():
    from elevenlabs.client import ElevenLabs

    return ElevenLabs(api_key=env("ELEVENLABS_API_KEY"))
