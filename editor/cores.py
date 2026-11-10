"""Extrai a cor dominante (viva) de uma foto, usando so o ffmpeg. Serve para o acento do Showcase combinar com a imagem."""
import colorsys
import shutil
import subprocess


def cor_dominante(caminho, padrao="#c9a24a"):
    ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ff:
        return padrao
    try:
        r = subprocess.run([ff, "-v", "error", "-i", str(caminho), "-vf", "scale=24:24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True, timeout=30)
    except (subprocess.SubprocessError, OSError):
        return padrao
    d = r.stdout
    if len(d) < 24 * 24 * 3:
        return padrao
    melhor, melhor_score = None, -1.0
    caixas = {}
    for i in range(0, 24 * 24 * 3, 3):
        rr, gg, bb = d[i] / 255, d[i + 1] / 255, d[i + 2] / 255
        h, sat, v = colorsys.rgb_to_hsv(rr, gg, bb)
        if v < 0.25 or sat < 0.25:
            continue
        k = int(h * 18)
        c = caixas.setdefault(k, [0, 0.0, 0.0, 0.0])
        c[0] += 1
        c[1] += h
        c[2] += sat
        c[3] += v
    for k, (n, hs, ss, vs) in caixas.items():
        score = n * (0.5 + ss / n)
        if score > melhor_score:
            melhor_score, melhor = score, (hs / n, ss / n, vs / n)
    if not melhor:
        return padrao
    h, sat, v = melhor
    rr, gg, bb = colorsys.hsv_to_rgb(h, min(1.0, max(0.55, sat)), min(0.95, max(0.7, v)))
    return "#%02x%02x%02x" % (int(rr * 255), int(gg * 255), int(bb * 255))
