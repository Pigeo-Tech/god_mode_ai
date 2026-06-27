"""Tiny HTTP wrapper around the Piper TTS binary — AGNI's own self-hosted voice engine.

POST /tts {"text": "..."}  -> audio/wav bytes (synthesized by Piper, CPU, offline)
GET  /health               -> {"status":"ok"}

Stdlib only (no pip deps) so the container stays small and reliable on a tiny server.
"""
import json
import os
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PIPER = "/app/piper/piper"
MODEL = os.environ.get("PIPER_MODEL", "/app/voice.onnx")
PORT = int(os.environ.get("PORT", "5002"))


def synth(text: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        out = f.name
    try:
        subprocess.run([PIPER, "-m", MODEL, "-f", out],
                       input=text.encode("utf-8"), capture_output=True, timeout=30, check=True)
        with open(out, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.unlink(out)
        except OSError:
            pass


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send(200, b'{"status":"ok"}')
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            text = (data.get("text") or "").strip()[:2000]
            if not text:
                self._send(400, b'{"error":"text required"}')
                return
            self._send(200, synth(text), "audio/wav")
        except Exception as exc:  # noqa: BLE001 - report error to caller
            self._send(500, json.dumps({"error": str(exc)}).encode())

    def log_message(self, *args):  # silence default logging
        pass


if __name__ == "__main__":
    print(f"Piper voice engine listening on :{PORT} (model {MODEL})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
