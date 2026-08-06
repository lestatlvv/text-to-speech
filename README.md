# Kokoro text-to-voice demos

Two small applications that show how **text-to-speech** works with the open-weight [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) model:

1. **CLI** — prints each pipeline stage (text → phonemes → waveform) and writes a WAV file
2. **Web studio** — interactive browser UI to pick a voice, generate speech, and inspect grapheme/phoneme chunks

Kokoro is an 82M-parameter TTS model (Apache 2.0) that runs well on CPU and outputs 24&nbsp;kHz audio.

## How text becomes voice

```text
written text
    → G2P (Misaki): spelling → phonemes
    → Kokoro-82M: phonemes + voice style → waveform
    → WAV / browser playback at 24 kHz
```

The demos expose those stages so you can see phonemes and timing, not only hear the result.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional but recommended for non-English voices (Spanish, French, Hindi, Italian, Portuguese) and English out-of-dictionary fallback:

```bash
sudo apt install espeak-ng
```

The first synthesis downloads model weights from Hugging Face into your local cache.

## CLI demo

```bash
./scripts/run_cli.sh "Hello from Kokoro."
./scripts/run_cli.sh --list-voices
./scripts/run_cli.sh -v am_michael -s 1.1 -o output/demo.wav "Text to voice, locally."
./scripts/run_cli.sh --play "Play this aloud if a system player is available."
```

You will see:

- the input text
- each grapheme chunk and its phoneme string
- duration / realtime factor
- a WAV path under `output/`

## Web demo

```bash
./scripts/run_web.sh
```

Open [http://127.0.0.1:7860](http://127.0.0.1:7860).

- **Speak** — synthesize and play audio
- **Show pipeline** — reveal G2P chunks and the four explanation steps

API endpoints used by the UI:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/voices` | Voice catalog |
| `POST` | `/api/speak` | Returns `audio/wav` |
| `POST` | `/api/speak/inspect` | JSON with steps + phoneme chunks |

Example:

```bash
curl -X POST http://127.0.0.1:7860/api/speak \
  -H 'Content-Type: application/json' \
  -d '{"text":"Kokoro speaks.","voice":"af_heart","speed":1.0}' \
  --output speech.wav
```

## Project layout

```text
src/kokoro_demo/     shared engine + voice catalog
apps/cli/speak.py    CLI demonstration
apps/web/            FastAPI server + static studio UI
scripts/             convenience runners
```

## Notes

- Default voice: `af_heart` (American English)
- Speed range: `0.5`–`2.0`
- CPU inference is expected to be slower than GPU, but Kokoro is small enough for interactive demos
- Japanese / Chinese voices need extra Misaki extras (`misaki[ja]`, `misaki[zh]`) if you extend the catalog
