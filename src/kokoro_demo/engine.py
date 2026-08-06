"""Kokoro synthesis engine with pipeline introspection for demos."""

from __future__ import annotations

import io
import threading
import time
import wave
from dataclasses import dataclass, field
from typing import Iterator

import numpy as np

from .voices import get_voice, lang_code_for_voice

SAMPLE_RATE = 24_000

_pipeline_lock = threading.Lock()
_pipelines: dict[str, object] = {}


@dataclass(frozen=True)
class SynthesisChunk:
    index: int
    graphemes: str
    phonemes: str
    samples: int
    duration_sec: float


@dataclass
class SynthesisResult:
    text: str
    voice: str
    language: str
    lang_code: str
    speed: float
    sample_rate: int
    audio: np.ndarray
    chunks: list[SynthesisChunk] = field(default_factory=list)
    elapsed_sec: float = 0.0

    @property
    def duration_sec(self) -> float:
        return float(len(self.audio) / self.sample_rate) if len(self.audio) else 0.0

    @property
    def realtime_factor(self) -> float:
        if self.elapsed_sec <= 0 or self.duration_sec <= 0:
            return 0.0
        return self.duration_sec / self.elapsed_sec

    def to_wav_bytes(self) -> bytes:
        pcm = np.clip(self.audio, -1.0, 1.0)
        pcm_i16 = (pcm * 32767.0).astype(np.int16)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(pcm_i16.tobytes())
        return buffer.getvalue()

    def pipeline_steps(self) -> list[dict]:
        """Human-readable stages that explain how text becomes voice."""
        return [
            {
                "id": "normalize",
                "title": "Normalize text",
                "detail": f"Received {len(self.text)} characters for voice '{self.voice}'.",
            },
            {
                "id": "g2p",
                "title": "Grapheme → phoneme (G2P)",
                "detail": (
                    "Misaki converts spelling into phonemes the model can speak. "
                    f"Produced {len(self.chunks)} chunk(s)."
                ),
            },
            {
                "id": "style",
                "title": "Apply voice style",
                "detail": (
                    f"Kokoro-82M conditions on the '{self.voice}' style vector "
                    f"({self.language}, speed={self.speed:.2f})."
                ),
            },
            {
                "id": "decode",
                "title": "Neural decode to waveform",
                "detail": (
                    f"Generated {len(self.audio):,} samples at {self.sample_rate} Hz "
                    f"({self.duration_sec:.2f}s audio in {self.elapsed_sec:.2f}s, "
                    f"RTF {self.realtime_factor:.2f}x)."
                ),
            },
        ]


def _get_pipeline(lang_code: str):
    with _pipeline_lock:
        pipeline = _pipelines.get(lang_code)
        if pipeline is None:
            from kokoro import KPipeline

            pipeline = KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M")
            _pipelines[lang_code] = pipeline
        return pipeline


def iter_chunks(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0,
    split_pattern: str = r"\n+",
) -> Iterator[tuple[str, str, np.ndarray]]:
    voice_info = get_voice(voice)
    lang_code = voice_info.lang_code
    pipeline = _get_pipeline(lang_code)
    generator = pipeline(
        text.strip(),
        voice=voice,
        speed=speed,
        split_pattern=split_pattern,
    )
    for graphemes, phonemes, audio in generator:
        yield graphemes, phonemes, np.asarray(audio, dtype=np.float32)


def synthesize(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0,
    split_pattern: str = r"\n+",
) -> SynthesisResult:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Text must not be empty.")
    if not 0.5 <= speed <= 2.0:
        raise ValueError("Speed must be between 0.5 and 2.0.")

    voice_info = get_voice(voice)
    started = time.perf_counter()
    chunks: list[SynthesisChunk] = []
    arrays: list[np.ndarray] = []

    for index, (graphemes, phonemes, audio) in enumerate(
        iter_chunks(cleaned, voice=voice, speed=speed, split_pattern=split_pattern)
    ):
        arrays.append(audio)
        chunks.append(
            SynthesisChunk(
                index=index,
                graphemes=graphemes,
                phonemes=phonemes,
                samples=int(audio.shape[0]),
                duration_sec=float(audio.shape[0] / SAMPLE_RATE),
            )
        )

    if not arrays:
        raise RuntimeError("Kokoro produced no audio for the given text.")

    audio = np.concatenate(arrays)
    elapsed = time.perf_counter() - started
    return SynthesisResult(
        text=cleaned,
        voice=voice,
        language=voice_info.language,
        lang_code=lang_code_for_voice(voice),
        speed=speed,
        sample_rate=SAMPLE_RATE,
        audio=audio,
        chunks=chunks,
        elapsed_sec=elapsed,
    )
