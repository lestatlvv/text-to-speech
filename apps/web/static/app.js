const form = document.getElementById("speak-form");
const textEl = document.getElementById("text");
const voiceEl = document.getElementById("voice");
const speedEl = document.getElementById("speed");
const speedValue = document.getElementById("speed-value");
const speakBtn = document.getElementById("speak-btn");
const inspectBtn = document.getElementById("inspect-btn");
const statusEl = document.getElementById("status");
const player = document.getElementById("player");
const meter = document.getElementById("meter");
const stats = document.getElementById("stats");
const pipeline = document.getElementById("pipeline");
const stepsEl = document.getElementById("steps");
const chunksEl = document.getElementById("chunks");

let objectUrl = null;

speedEl.addEventListener("input", () => {
  speedValue.textContent = `${Number(speedEl.value).toFixed(2)}×`;
});

function setBusy(busy, message) {
  speakBtn.disabled = busy;
  inspectBtn.disabled = busy;
  meter.classList.toggle("active", busy);
  statusEl.classList.remove("error");
  if (message) statusEl.textContent = message;
}

function setError(message) {
  setBusy(false);
  statusEl.classList.add("error");
  statusEl.textContent = message;
}

function payload() {
  return {
    text: textEl.value.trim(),
    voice: voiceEl.value,
    speed: Number(speedEl.value),
  };
}

async function loadVoices() {
  const response = await fetch("/api/voices");
  if (!response.ok) throw new Error("Could not load voices.");
  const voices = await response.json();
  voiceEl.innerHTML = "";

  const groups = new Map();
  for (const voice of voices) {
    if (!groups.has(voice.language)) groups.set(voice.language, []);
    groups.get(voice.language).push(voice);
  }

  for (const [language, items] of groups) {
    const optgroup = document.createElement("optgroup");
    optgroup.label = language;
    for (const voice of items) {
      const option = document.createElement("option");
      option.value = voice.id;
      option.textContent = `${voice.name} (${voice.gender}${voice.note ? ` · ${voice.note}` : ""})`;
      if (voice.id === "af_heart") option.selected = true;
      optgroup.appendChild(option);
    }
    voiceEl.appendChild(optgroup);
  }
}

function renderPipeline(data) {
  stepsEl.innerHTML = "";
  chunksEl.innerHTML = "";

  data.steps.forEach((step, index) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="index">${index + 1}</div>
      <div>
        <h3>${step.title}</h3>
        <p>${step.detail}</p>
      </div>
    `;
    stepsEl.appendChild(li);
  });

  for (const chunk of data.chunks) {
    const card = document.createElement("article");
    card.className = "chunk";
    card.innerHTML = `
      <h4>Chunk ${chunk.index + 1} · ${chunk.duration_sec.toFixed(2)}s</h4>
      <p><strong>Text:</strong> ${escapeHtml(chunk.graphemes)}</p>
      <p><strong>Phonemes:</strong> <code>${escapeHtml(chunk.phonemes)}</code></p>
    `;
    chunksEl.appendChild(card);
  }

  pipeline.hidden = false;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function speakAndPlay() {
  const body = payload();
  if (!body.text) {
    setError("Enter some text first.");
    return;
  }

  setBusy(true, "Synthesizing with Kokoro-82M… first run may download model weights.");

  const response = await fetch("/api/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = "Synthesis failed.";
    try {
      const err = await response.json();
      detail = err.detail || detail;
    } catch {
      /* ignore */
    }
    setError(detail);
    return;
  }

  const blob = await response.blob();
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = URL.createObjectURL(blob);
  player.src = objectUrl;
  await player.play().catch(() => {});

  const duration = response.headers.get("X-Duration-Sec");
  const elapsed = response.headers.get("X-Elapsed-Sec");
  const rtf = response.headers.get("X-Realtime-Factor");
  document.getElementById("stat-duration").textContent = duration ? `${Number(duration).toFixed(2)}s` : "—";
  document.getElementById("stat-elapsed").textContent = elapsed ? `${Number(elapsed).toFixed(2)}s` : "—";
  document.getElementById("stat-rtf").textContent = rtf ? `${Number(rtf).toFixed(2)}×` : "—";
  stats.hidden = false;

  setBusy(false, `Playing ${body.voice} · ${response.headers.get("X-Language") || "voice"}`);
}

async function inspectPipeline() {
  const body = payload();
  if (!body.text) {
    setError("Enter some text first.");
    return;
  }

  setBusy(true, "Running the full pipeline for inspection…");
  const response = await fetch("/api/speak/inspect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = "Inspection failed.";
    try {
      const err = await response.json();
      detail = err.detail || detail;
    } catch {
      /* ignore */
    }
    setError(detail);
    return;
  }

  const data = await response.json();
  renderPipeline(data);
  document.getElementById("stat-duration").textContent = `${data.duration_sec.toFixed(2)}s`;
  document.getElementById("stat-elapsed").textContent = `${data.elapsed_sec.toFixed(2)}s`;
  document.getElementById("stat-rtf").textContent = `${data.realtime_factor.toFixed(2)}×`;
  stats.hidden = false;
  setBusy(false, "Pipeline details ready. Use Speak to hear the audio.");
  pipeline.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  speakAndPlay().catch((error) => setError(error.message || String(error)));
});

inspectBtn.addEventListener("click", () => {
  inspectPipeline().catch((error) => setError(error.message || String(error)));
});

loadVoices().catch((error) => setError(error.message || String(error)));
