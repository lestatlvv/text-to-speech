#!/usr/bin/env python3
"""Interactive web demo for Kokoro text-to-speech."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kokoro_demo import list_voices, synthesize  # noqa: E402
from kokoro_demo.engine import SAMPLE_RATE  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Kokoro TTS Demo",
    description="Interactive demonstration of Kokoro-82M text-to-speech.",
    version="1.0.0",
)

# Allow the Demo Store (typically :5500) to generate clips at startup.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=[
        "X-Voice",
        "X-Language",
        "X-Duration-Sec",
        "X-Elapsed-Sec",
        "X-Realtime-Factor",
    ],
)


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    voice: str = "af_heart"
    speed: float = Field(1.0, ge=0.5, le=2.0)


class SpeakJsonResponse(BaseModel):
    voice: str
    language: str
    lang_code: str
    speed: float
    sample_rate: int
    duration_sec: float
    elapsed_sec: float
    realtime_factor: float
    steps: list[dict]
    chunks: list[dict]


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "model": "Kokoro-82M", "sample_rate": SAMPLE_RATE}


@app.get("/api/voices")
def voices() -> list[dict]:
    return list_voices()


@app.post("/api/speak")
def speak(request: SpeakRequest) -> Response:
    try:
        result = synthesize(request.text, voice=request.voice, speed=request.speed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface model/runtime failures to UI
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    headers = {
        "X-Voice": result.voice,
        "X-Language": result.language,
        "X-Duration-Sec": f"{result.duration_sec:.3f}",
        "X-Elapsed-Sec": f"{result.elapsed_sec:.3f}",
        "X-Realtime-Factor": f"{result.realtime_factor:.3f}",
        "Access-Control-Expose-Headers": (
            "X-Voice, X-Language, X-Duration-Sec, X-Elapsed-Sec, X-Realtime-Factor"
        ),
    }
    return Response(content=result.to_wav_bytes(), media_type="audio/wav", headers=headers)


@app.post("/api/speak/inspect", response_model=SpeakJsonResponse)
def speak_inspect(request: SpeakRequest) -> SpeakJsonResponse:
    try:
        result = synthesize(request.text, voice=request.voice, speed=request.speed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SpeakJsonResponse(
        voice=result.voice,
        language=result.language,
        lang_code=result.lang_code,
        speed=result.speed,
        sample_rate=result.sample_rate,
        duration_sec=result.duration_sec,
        elapsed_sec=result.elapsed_sec,
        realtime_factor=result.realtime_factor,
        steps=result.pipeline_steps(),
        chunks=[
            {
                "index": chunk.index,
                "graphemes": chunk.graphemes,
                "phonemes": chunk.phonemes,
                "samples": chunk.samples,
                "duration_sec": chunk.duration_sec,
            }
            for chunk in result.chunks
        ],
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7860, reload=False)


if __name__ == "__main__":
    main()
