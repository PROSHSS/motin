# -*- coding: utf-8 -*-
"""Analisador de videos de referencia (100% local, so ffmpeg + Pillow).
Mede: duracao, numero de cortes, duracao media dos planos, ritmo, energia de movimento, paleta dominante e
brilho. Gera um PERFIL em estilos/ref_<nome>.json no mesmo formato dos estilos do sistema, que o criar.py usa com
    python criar.py --estilo ref_<nome>
Uso:  python referencias.py video1.mp4 [video2.mp4 ...]      (ou uma pasta com videos)
Honestidade: ele mede ritmo, cores e quantidade de cortes. NAO "copia" a composicao: escolhe, entre as cenas que o
sistema realmente sabe renderizar, as que combinam com o ritmo e as cores medidas."""
import colorsys
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FF = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
FP = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
VIDEOS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}


def duracao(arq):
    r = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(arq)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def cortes(arq, limiar=0.32):
    """Instantes (s) de mudanca de plano, via deteccao de cena do ffmpeg."""
    r = subprocess.run([FF, "-hide_banner", "-i", str(arq), "-vf", f"select='gt(scene,{limiar})',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def energia(arq):
    """Movimento medio entre quadros (0 a 1), amostrando 4 quadros por segundo em baixa resolucao."""
    from PIL import Image
    import numpy as np
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([FF, "-v", "error", "-i", str(arq), "-vf", "fps=4,scale=64:-1,format=gray", "-an", f"{td}/f_%04d.png"], capture_output=True)
        fs = sorted(Path(td).glob("f_*.png"))[:240]
        if len(fs) < 3:
            return 0.0
        a = [np.asarray(Image.open(f), dtype="float32") / 255 for f in fs]
        return float(np.mean([np.abs(a[i] - a[i - 1]).mean() for i in range(1, len(a))]))


def paleta(arq, n=12):
    """Cor de destaque (a mais saturada e frequente) + brilho medio, de n quadros espalhados pelo video."""
    from PIL import Image
    import numpy as np
    d = duracao(arq) or 1
    cores, brilhos = [], []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([FF, "-v", "error", "-i", str(arq), "-vf", f"fps={n / d:.4f},scale=96:-1", "-an", f"{td}/p_%03d.png"], capture_output=True)
        for f in sorted(Path(td).glob("p_*.png")):
            im = Image.open(f).convert("RGB")
            px = np.asarray(im).reshape(-1, 3) / 255.0
            brilhos.append(float(px.mean()))
            for r, g, b in px[::7]:
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                if s > 0.45 and v > 0.45:
                    cores.append(round(h * 360 / 15) * 15 % 360)
    if not cores:
        return None, (sum(brilhos) / len(brilhos) if brilhos else 0.3)
    return max(set(cores), key=cores.count), sum(brilhos) / len(brilhos)


def nome_paleta(h):
    """Matiz (graus) -> nome de paleta ESCURA do sistema (o documentario e sempre escuro)."""
    if h is None:
        return "grafite"
    if h < 12 or h >= 345:
        return "vermelho"
    if h < 38:
        return "laranjaesc"
    if h < 52:
        return "ambar"
    if h < 70:
        return "amarelo"
    if h < 135:
        return "neon"
    if h < 165:
        return "verde"
    if h < 200:
        return "ciano"
    if h < 255:
        return "azul"
    return "violeta"


def perfil(arq):
    arq = Path(arq)
    d = duracao(arq)
    if d <= 0:
        raise RuntimeError("video ilegivel")
    cs = cortes(arq)
    n_planos = len(cs) + 1
    media = d / n_planos
    en = energia(arq)
    h, br = paleta(arq)
    por_min = 60.0 / media
    if media < 1.6:
        preferir = ["cartaz", "glitch", "pilula", "rajada", "checklist", "contador"]
        ritmo = 0.8
        nivel = "muito rapido"
    elif media < 3.0:
        preferir = ["cartaz", "pilula", "busca", "pasta", "comparacao", "alerta", "ranking"]
        ritmo = 0.95
        nivel = "rapido"
    else:
        preferir = ["busca", "pasta", "linha_tempo", "citacao", "foto_moldura", "comparacao"]
        ritmo = 1.1
        nivel = "calmo"
    if en > 0.12:   # muito movimento: mais cenas de impacto
        preferir = ["glitch", "cartaz"] + [x for x in preferir if x not in ("glitch", "cartaz")]
    return {
        "descricao": f"Perfil medido de {arq.name}: {n_planos} planos em {d:.0f}s (media {media:.1f}s, ritmo {nivel}), movimento {en:.2f}, brilho {br:.2f}",
        "paleta": [nome_paleta(h)],
        "gancho": ["digitando", "carimbo"],
        "preferir": preferir[:6],
        "evitar": [],
        "ritmo": ritmo,
        "classicas": ["cinetica", "frase", "explicativa", "imagem"],
        "mistura": 0.35,
        "medido": {"duracao_s": round(d, 1), "planos": n_planos, "plano_medio_s": round(media, 2), "cortes_por_min": round(por_min, 1),
                   "movimento": round(en, 3), "brilho": round(br, 3), "matiz": h},
    }


def main(args):
    if not FF or not FP:
        print("ERRO: ffmpeg/ffprobe nao encontrados.")
        return 1
    arqs = []
    for a in args:
        p = Path(a)
        arqs += sorted(x for x in p.iterdir() if x.suffix.lower() in VIDEOS) if p.is_dir() else [p]
    if not arqs:
        print("Uso: python referencias.py video.mp4 [outro.mp4 ...]   (ou uma pasta)")
        return 1
    saida = RAIZ / "estilos"
    saida.mkdir(exist_ok=True)
    for a in arqs:
        try:
            pf = perfil(a)
        except Exception as e:   # noqa: BLE001 - um video ruim nao derruba os outros
            print(f"[pulado] {a.name}: {e}")
            continue
        nome = "ref_" + re.sub(r"[^a-z0-9]+", "_", a.stem.lower())[:24].strip("_")
        pf["nome"] = nome
        (saida / f"{nome}.json").write_text(json.dumps(pf, ensure_ascii=False, indent=2), encoding="utf-8")
        m = pf["medido"]
        print(f"{nome}: {m['planos']} planos, media {m['plano_medio_s']}s, movimento {m['movimento']}, paleta {pf['paleta'][0]}, preferir {', '.join(pf['preferir'][:3])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
