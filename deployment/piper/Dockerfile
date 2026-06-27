# Self-hosted Piper TTS — AGNI's OWN voice engine (no third-party AI voice service).
# Runs the open-source Piper neural TTS on your server and exposes a tiny HTTP endpoint that the
# AGNI backend's /v1/tts calls. CPU-only, offline after build, zero per-use cost.
#
# Choose the voice at build time with --build-arg VOICE_BASE=<huggingface model base url>.
#   Default: en_US-hfc_female (natural English female).
#   Indian female (Hindi): use the hi_IN-priyamvada base (see use-piper.sh).
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Self-contained Piper binary (bundles onnxruntime + espeak-ng data) — no heavy pip installs.
RUN curl -fsSL -o piper.tar.gz \
      https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz \
    && tar -xzf piper.tar.gz && rm piper.tar.gz

# Voice model (configurable). Default: English female.
ARG VOICE_BASE=https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/hfc_female/medium/en_US-hfc_female-medium
RUN curl -fsSL -o /app/voice.onnx      "${VOICE_BASE}.onnx?download=true" \
    && curl -fsSL -o /app/voice.onnx.json "${VOICE_BASE}.onnx.json?download=true"

COPY serve.py /app/serve.py
EXPOSE 5002
CMD ["python", "serve.py"]
