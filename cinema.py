"""cinema.py - acabamento de cinema nas imagens de IA (usa so o ffmpeg, que voce ja tem).
Junta o visual de todas as imagens (mesma cor, mesmo grao), tira o brilho "plastico" e deixa mais parecido com foto de cinema/documentario."""
import shutil
import subprocess
from pathlib import Path

GRADE = (
    "curves=m='0/0 0.15/0.13 0.5/0.5 0.85/0.87 1/1',"          # curva em S suave (mais contraste, sem estourar)
    "eq=saturation=0.9:contrast=1.02:gamma=1.0,"               # cores um pouco menos 'de IA'
    "colorbalance=rs=-0.02:bs=0.035:rm=0.0:bm=0.01:rh=0.02:bh=-0.015,"  # sombras frias, luzes quentes
    "unsharp=5:5:0.5:5:5:0.0,"                                  # nitidez leve nos detalhes
    "noise=alls=5:allf=t+u"                                      # grao fino de pelicula
)


def _ff():
    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")


def qualidade_ok(arq):
    """False se a imagem estiver vazia/uniforme (geracao falha) ou minuscula."""
    arq = Path(arq)
    ff = _ff()
    if not arq.exists() or arq.stat().st_size < 8000:
        return False
    if not ff:
        return True
    try:
        r = subprocess.run([ff, "-v", "error", "-i", str(arq), "-vf", "scale=96:96,format=gray", "-f", "rawvideo", "-"],
                           capture_output=True, timeout=30)
    except (subprocess.SubprocessError, OSError):
        return True
    d = r.stdout
    if len(d) < 96 * 96:
        return False
    media = sum(d) / len(d)
    desvio = (sum((x - media) ** 2 for x in d) / len(d)) ** 0.5
    return desvio >= 7  # imagem quase uma cor so = falha


def tratar(arq):
    """Aplica o visual de cinema na propria imagem (uma vez so: cria o marcador .grade)."""
    arq = Path(arq)
    marca = arq.with_suffix(arq.suffix + ".grade")
    ff = _ff()
    if not ff or marca.exists() or not arq.exists():
        return False
    tmp = arq.with_name(arq.stem + "_tmp.jpg")
    try:
        r = subprocess.run([ff, "-y", "-v", "error", "-i", str(arq), "-vf", GRADE, "-q:v", "2", str(tmp)], capture_output=True, timeout=120)
    except (subprocess.SubprocessError, OSError):
        return False
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 5000:
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(arq)
    marca.write_text("ok")
    return True
