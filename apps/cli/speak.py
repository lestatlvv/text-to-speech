#!/usr/bin/env python3
"""CLI demo: walk through Kokoro text-to-speech and write a WAV file."""

from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kokoro_demo import list_voices, synthesize  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Demonstrate Kokoro text-to-speech: text → phonemes → waveform.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to speak. Omit to read from --file or stdin.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Read input text from a file.",
    )
    parser.add_argument(
        "-v",
        "--voice",
        default="af_heart",
        help="Kokoro voice id (default: af_heart).",
    )
    parser.add_argument(
        "-s",
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed from 0.5 to 2.0 (default: 1.0).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/speech.wav"),
        help="Where to write the WAV file.",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="Print available demo voices and exit.",
    )
    parser.add_argument(
        "--play",
        action="store_true",
        help="Try to play the WAV with the system default player.",
    )
    return parser


def resolve_text(args: argparse.Namespace) -> str:
    if args.file:
        return args.file.read_text(encoding="utf-8")
    if args.text:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Provide text as an argument, via --file, or on stdin.")


def print_voices() -> None:
    print(f"{'ID':<14} {'Name':<12} {'Language':<22} {'Gender':<8} Grade")
    print("-" * 72)
    for voice in list_voices():
        print(
            f"{voice['id']:<14} {voice['name']:<12} {voice['language']:<22} "
            f"{voice['gender']:<8} {voice['grade']}"
        )


def write_wav(path: Path, audio, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    import numpy as np

    pcm = np.clip(audio, -1.0, 1.0)
    pcm_i16 = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_i16.tobytes())


def maybe_play(path: Path) -> None:
    import shutil
    import subprocess

    for player in ("paplay", "aplay", "ffplay", "afplay"):
        binary = shutil.which(player)
        if not binary:
            continue
        cmd = [binary, str(path)]
        if player == "ffplay":
            cmd = [binary, "-nodisp", "-autoexit", str(path)]
        subprocess.run(cmd, check=False)
        return
    print("No system audio player found (tried paplay/aplay/ffplay/afplay).")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_voices:
        print_voices()
        return 0

    text = resolve_text(args)
    print("Kokoro TTS pipeline")
    print("=" * 72)
    print("1) Input text")
    print(f"   {text[:200]}{'…' if len(text) > 200 else ''}")
    print()
    print(f"2) Loading voice style '{args.voice}' at speed {args.speed:.2f}")
    print("   First run downloads Kokoro-82M weights from Hugging Face.")
    print()

    result = synthesize(text, voice=args.voice, speed=args.speed)

    print("3) Grapheme → phoneme chunks")
    for chunk in result.chunks:
        preview = chunk.graphemes.replace("\n", " ")[:64]
        print(f"   [{chunk.index}] {preview!r}")
        print(f"       phonemes: {chunk.phonemes[:80]}{'…' if len(chunk.phonemes) > 80 else ''}")
        print(f"       audio: {chunk.duration_sec:.2f}s ({chunk.samples} samples)")
    print()

    for step in result.pipeline_steps():
        print(f"• {step['title']}: {step['detail']}")
    print()

    write_wav(args.output, result.audio, result.sample_rate)
    print(f"Wrote {args.output.resolve()}")
    print(
        f"Audio {result.duration_sec:.2f}s generated in {result.elapsed_sec:.2f}s "
        f"(realtime factor {result.realtime_factor:.2f}x)"
    )

    if args.play:
        maybe_play(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
