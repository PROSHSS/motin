import json
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel

# Lê o áudio sem usar o pacote "av"
audio, sr = sf.read("narracao.wav", dtype="float32")
if audio.ndim > 1:
    audio = audio.mean(axis=1)            # converte para mono
if sr != 16000:
    audio = resample_poly(audio, 16000, sr).astype(np.float32)   # o Whisper exige 16 kHz

modelo = WhisperModel("small", device="cpu", compute_type="int8")

segmentos, info = modelo.transcribe(
    audio,
    language="pt",
    word_timestamps=True,
    vad_filter=False,
)

palavras = []
for seg in segmentos:
    for p in seg.words:
        palavras.append({
            "palavra": p.word.strip(),
            "inicio": round(p.start, 3),
            "fim": round(p.end, 3),
        })

json.dump(palavras, open("palavras.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(f"OK: palavras.json criado com {len(palavras)} palavras")
