"""Catalog of Kokoro-82M preset voices used by the demos."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Voice:
    id: str
    name: str
    language: str
    lang_code: str
    gender: str
    grade: str
    note: str = ""


# lang_code values match kokoro.KPipeline / misaki conventions.
VOICES: tuple[Voice, ...] = (
    Voice("af_heart", "Heart", "American English", "a", "female", "A", "Default / highest grade"),
    Voice("af_bella", "Bella", "American English", "a", "female", "A-", "Warm & expressive"),
    Voice("af_nicole", "Nicole", "American English", "a", "female", "B-", "Podcast-like"),
    Voice("af_sarah", "Sarah", "American English", "a", "female", "C+"),
    Voice("af_sky", "Sky", "American English", "a", "female", "C-"),
    Voice("af_alloy", "Alloy", "American English", "a", "female", "C"),
    Voice("af_nova", "Nova", "American English", "a", "female", "C"),
    Voice("af_kore", "Kore", "American English", "a", "female", "C+"),
    Voice("am_michael", "Michael", "American English", "a", "male", "C+"),
    Voice("am_fenrir", "Fenrir", "American English", "a", "male", "C+"),
    Voice("am_puck", "Puck", "American English", "a", "male", "C+"),
    Voice("am_adam", "Adam", "American English", "a", "male", "F+"),
    Voice("am_echo", "Echo", "American English", "a", "male", "D"),
    Voice("am_liam", "Liam", "American English", "a", "male", "D"),
    Voice("bf_emma", "Emma", "British English", "b", "female", "B-"),
    Voice("bf_isabella", "Isabella", "British English", "b", "female", "C"),
    Voice("bf_alice", "Alice", "British English", "b", "female", "D"),
    Voice("bm_george", "George", "British English", "b", "male", "C"),
    Voice("bm_fable", "Fable", "British English", "b", "male", "C"),
    Voice("bm_lewis", "Lewis", "British English", "b", "male", "D+"),
    Voice("ef_dora", "Dora", "Spanish", "e", "female", "—", "Needs espeak-ng"),
    Voice("em_alex", "Alex", "Spanish", "e", "male", "—", "Needs espeak-ng"),
    Voice("ff_siwis", "Siwis", "French", "f", "female", "B-", "Needs espeak-ng"),
    Voice("hf_alpha", "Alpha", "Hindi", "h", "female", "C", "Needs espeak-ng"),
    Voice("hm_omega", "Omega", "Hindi", "h", "male", "C", "Needs espeak-ng"),
    Voice("if_sara", "Sara", "Italian", "i", "female", "C", "Needs espeak-ng"),
    Voice("im_nicola", "Nicola", "Italian", "i", "male", "C", "Needs espeak-ng"),
    Voice("pf_dora", "Dora", "Brazilian Portuguese", "p", "female", "—", "Needs espeak-ng"),
    Voice("pm_alex", "Alex", "Brazilian Portuguese", "p", "male", "—", "Needs espeak-ng"),
)


_BY_ID = {voice.id: voice for voice in VOICES}


def get_voice(voice_id: str) -> Voice:
    try:
        return _BY_ID[voice_id]
    except KeyError as exc:
        known = ", ".join(sorted(_BY_ID))
        raise ValueError(f"Unknown voice '{voice_id}'. Known voices: {known}") from exc


def lang_code_for_voice(voice_id: str) -> str:
    return get_voice(voice_id).lang_code


def list_voices() -> list[dict]:
    return [asdict(voice) for voice in VOICES]
