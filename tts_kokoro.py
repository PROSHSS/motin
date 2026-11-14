import json, re, random
import numpy as np
import soundfile as sf
from kokoro import KPipeline

# ---------------- CONFIGURAÇÃO ----------------
VOZ = "pm_alex"          # teste também: "pm_alex"
VELOCIDADE = 0.92         # 0.88 a 0.95 = ritmo de documentário
SR = 24000                # taxa de amostragem do Kokoro
SEMENTE = 7               # fixa as pausas aleatórias (resultado repetível)
# ----------------------------------------------

random.seed(SEMENTE)
pipe = KPipeline(lang_code="p")   # p = português do Brasil


def silencio(segundos):
    return np.zeros(int(SR * segundos), dtype=np.float32)


def limpar(texto):
    """Prepara o texto para soar mais natural na leitura."""
    texto = texto.replace("%", " por cento")
    texto = texto.replace("&", " e ")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def dividir_frases(texto):
    """Divide em frases e quebra frases longas nas vírgulas."""
    frases = re.split(r"(?<=[.!?…])\s+", texto)
    saida = []
    for f in frases:
        f = f.strip()
        if not f:
            continue
        if len(f) > 140 and "," in f:
            partes = [p.strip() for p in f.split(",") if p.strip()]
            for i, p in enumerate(partes):
                saida.append(p + ("," if i < len(partes) - 1 else ""))
        else:
            saida.append(f)
    return saida


def pausa_apos(frase):
    """Pausa variável conforme a pontuação, como numa locução real."""
    if frase.endswith(("?", "!")):
        return random.uniform(0.40, 0.55)
    if frase.endswith("…"):
        return random.uniform(0.55, 0.75)
    if frase.endswith(","):
        return random.uniform(0.15, 0.25)
    return random.uniform(0.30, 0.45)


def falar(frase):
    partes = []
    for _, _, audio in pipe(frase, voice=VOZ, speed=VELOCIDADE):
        partes.append(np.asarray(audio, dtype=np.float32))
    return np.concatenate(partes) if partes else silencio(0)


def fade(audio, ms=12):
    """Fade curto no início e no fim para evitar estalos entre trechos."""
    n = min(int(SR * ms / 1000), len(audio) // 2)
    if n > 0:
        audio[:n] *= np.linspace(0, 1, n, dtype=np.float32)
        audio[-n:] *= np.linspace(1, 0, n, dtype=np.float32)
    return audio


roteiro = json.load(open("roteiro.json", encoding="utf-8"))

trechos = [silencio(0.4)]                       # respiro inicial
tempos_cenas = []                               # duração de cada cena (útil para o vídeo)

for i, cena in enumerate(roteiro["cenas"], start=1):
    inicio = sum(len(t) for t in trechos) / SR
    for frase in dividir_frases(limpar(cena["narracao"])):
        trechos.append(fade(falar(frase)))
        trechos.append(silencio(pausa_apos(frase)))
    trechos.append(silencio(random.uniform(0.35, 0.55)))   # pausa entre cenas
    fim = sum(len(t) for t in trechos) / SR
    tempos_cenas.append({"cena": i, "inicio": round(inicio, 2), "fim": round(fim, 2)})
    print(f"Cena {i}/{len(roteiro['cenas'])} ok")

trechos.append(silencio(0.6))                   # respiro final

audio = np.concatenate(trechos)
pico = np.max(np.abs(audio))
if pico > 0:
    audio = audio / pico * 0.95                 # normaliza sem estourar

sf.write("narracao.wav", audio, SR)
json.dump(tempos_cenas, open("tempos_cenas.json", "w", encoding="utf-8"), indent=2)
print("OK: narracao.wav e tempos_cenas.json criados")
