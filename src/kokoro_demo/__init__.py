"""Shared Kokoro TTS helpers for the demo applications."""

from .engine import SynthesisChunk, SynthesisResult, synthesize
from .voices import VOICES, get_voice, lang_code_for_voice, list_voices

__all__ = [
    "SynthesisChunk",
    "SynthesisResult",
    "VOICES",
    "get_voice",
    "lang_code_for_voice",
    "list_voices",
    "synthesize",
]
