"""
tts_chatterbox.py - narracao com o Chatterbox Multilingual (MIT, portugues, so CPU).

Mesma interface do tts_kokoro.py: le roteiro.json e cria narracao.wav + tempos_cenas.json.

Teste rapido da voz (sem roteiro):
    python tts_chatterbox.py --teste
    python tts_chatterbox.py --variacoes   (gera 4 versoes com ajustes diferentes)

Voz de referencia (opcional, mas MUITO recomendada): um audio .wav de 10 a 20 segundos
de uma pessoa falando portugues do Brasil, com voz propria ou autorizada. Coloque em
    voz_referencia.wav   (na pasta principal do projeto)
Sem referencia, o Chatterbox usa a voz padrao dele, que pode sair com sotaque.
"""
import json
import os
import random
import re
import sys
import time

import numpy as np
import soundfile as sf
import torch

# ---------------- CONFIGURACAO ----------------
EXAGERO = 0.4         # 0.3 = voz calma e seria | 0.7 = mais emotiva
CFG = 0.3             # menor = fala mais lenta e calma | maior = segue mais o ritmo e o sotaque da referencia
TEMPERATURA = 0.7
SEMENTE = 7
# ----------------------------------------------

random.seed(SEMENTE)
torch.manual_seed(SEMENTE)
torch.set_num_threads(max(1, (os.cpu_count() or 4) - 2))

# Os pesos do modelo foram salvos para GPU: forca a leitura na CPU
_torch_load = torch.load
torch.load = lambda *a, **k: _torch_load(*a, **{**k, "map_location": torch.device("cpu")})

from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # noqa: E402


def achar_referencia():
    candidatos = [os.environ.get("VOZ_REFERENCIA", ""), "voz_referencia.wav"]
    for c in candidatos:
        if c and os.path.exists(c):
            return c
    return None


print("Carregando o modelo de voz (a primeira vez baixa alguns GB)...", flush=True)
modelo = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
SR = modelo.sr
REF = achar_referencia()
print("Voz de referencia:", REF if REF else "nenhuma (voz padrao)", flush=True)


def silencio(seg):
    return np.zeros(int(SR * seg), dtype=np.float32)


def limpar(texto):
    texto = re.sub(r"R\$\s*([\d.,]+)", r"\1 reais", texto)
    texto = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", texto)
    texto = texto.replace("%", " por cento").replace("&", " e ")
    return re.sub(r"\s+", " ", texto).strip()


def dividir_frases(texto):
    frases = re.split(r"(?<=[.!?…])\s+", texto)
    saida = []
    for f in frases:
        f = f.strip()
        if not f:
            continue
        if len(f) > 160 and "," in f:
            partes = [p.strip() for p in f.split(",") if p.strip()]
            for i, p in enumerate(partes):
                saida.append(p + ("," if i < len(partes) - 1 else ""))
        else:
            saida.append(f)
    return saida


def pausa_apos(frase):
    # o modelo ja coloca pausas naturais dentro da frase; aqui so o respiro entre frases
    if frase.endswith(("?", "!")):
        return random.uniform(0.30, 0.42)
    if frase.endswith("…"):
        return random.uniform(0.45, 0.60)
    if frase.endswith(","):
        return random.uniform(0.08, 0.15)
    return random.uniform(0.22, 0.34)


def aparar(audio, limiar=0.012):
    """Tira o silencio e o ruido do comeco e do fim de cada trecho."""
    idx = np.where(np.abs(audio) > limiar)[0]
    if len(idx) == 0:
        return audio
    a = max(0, idx[0] - int(SR * 0.03))
    b = min(len(audio), idx[-1] + int(SR * 0.08))
    return audio[a:b]


def fade(audio, ms=15):
    n = min(int(SR * ms / 1000), len(audio) // 2)
    if n > 0:
        audio[:n] *= np.linspace(0, 1, n, dtype=np.float32)
        audio[-n:] *= np.linspace(1, 0, n, dtype=np.float32)
    return audio


def falar(frase, exagero=None, cfg=None, temperatura=None, usar_ref=True):
    t0 = time.time()
    kwargs = dict(
        language_id="pt",
        exaggeration=EXAGERO if exagero is None else exagero,
        cfg_weight=CFG if cfg is None else cfg,
        temperature=TEMPERATURA if temperatura is None else temperatura,
    )
    if REF and usar_ref:
        kwargs["audio_prompt_path"] = REF
    wav = modelo.generate(frase, **kwargs)
    audio = wav.squeeze().detach().cpu().numpy().astype(np.float32)
    audio = fade(aparar(audio))
    dur = len(audio) / SR
    print(f"   {dur:4.1f}s de audio em {time.time() - t0:4.1f}s  | {frase[:60]}", flush=True)
    return audio


def principal():
    if "--variacoes" in sys.argv:
        texto = (
            "No segundo turno, cada voto conta muito. "
            "Para vencer, o candidato precisa de mais da metade dos votos válidos. "
            "E é por isso que essa decisão importa para todo o país."
        )
        palavras = len(texto.split())
        presets = {
            "A": dict(exagero=0.35, cfg=0.30, temperatura=0.70, usar_ref=True),
            "B": dict(exagero=0.35, cfg=0.65, temperatura=0.70, usar_ref=True),
            "C": dict(exagero=0.55, cfg=0.30, temperatura=0.75, usar_ref=True),
            "D": dict(exagero=0.35, cfg=0.30, temperatura=0.70, usar_ref=False),
        }
        for nome, pr in presets.items():
            print(f"\n== Versao {nome}: {pr}", flush=True)
            partes = []
            for fr in dividir_frases(texto):
                partes.append(falar(fr, **pr))
                partes.append(silencio(pausa_apos(fr)))
            audio = np.concatenate(partes)
            sf.write(f"teste_voz_{nome}.wav", audio, SR)
            print(f"   ritmo geral: {palavras / (len(audio) / SR):.2f} palavras/s (documentario calmo: 2,2 a 2,8)", flush=True)
        print("\nOK: teste_voz_A.wav, _B, _C e _D criados. Ouca cada um e me diga qual ficou melhor.")
        return

    if "--teste" in sys.argv:
        texto = (
            "No segundo turno, cada voto conta muito. "
            "Para vencer, o candidato precisa de mais da metade dos votos válidos. "
            "E é por isso que essa decisão importa para todo o país."
        )
        partes = []
        for fr in dividir_frases(texto):
            partes.append(falar(fr))
            partes.append(silencio(pausa_apos(fr)))
        sf.write("teste_voz.wav", np.concatenate(partes), SR)
        print("OK: teste_voz.wav criado. Ouca com: start teste_voz.wav")
        return

    roteiro = json.load(open("roteiro.json", encoding="utf-8"))
    trechos = [silencio(0.4)]
    tempos = []
    for i, cena in enumerate(roteiro["cenas"], start=1):
        inicio = sum(len(t) for t in trechos) / SR
        for frase in dividir_frases(limpar(cena["narracao"])):
            trechos.append(falar(frase))
            trechos.append(silencio(pausa_apos(frase)))
        trechos.append(silencio(random.uniform(0.35, 0.55)))
        fim = sum(len(t) for t in trechos) / SR
        tempos.append({"cena": i, "inicio": round(inicio, 2), "fim": round(fim, 2)})
        print(f"Cena {i}/{len(roteiro['cenas'])} ok", flush=True)
    trechos.append(silencio(0.6))

    audio = np.concatenate(trechos)
    pico = float(np.max(np.abs(audio))) if len(audio) else 0.0
    if pico > 0:
        audio = audio / pico * 0.95
    sf.write("narracao.wav", audio, SR)
    json.dump(tempos, open("tempos_cenas.json", "w", encoding="utf-8"), indent=2)
    print("OK: narracao.wav e tempos_cenas.json criados")


principal()
