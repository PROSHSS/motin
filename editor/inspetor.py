# -*- coding: utf-8 -*-
"""AI Quality Inspector (so medicoes OBJETIVAS, 100% local: ffmpeg/ffprobe).
Inspeciona o MP4 ja renderizado e escreve RELATORIO_QUALIDADE.txt/.json com, para cada problema:
timestamp, categoria, gravidade, evidencia, correcao proposta e resultado da verificacao apos a correcao.
Correcao automatica (segura e localizada): so o AUDIO (volume/pico), sem re-renderizar imagem; ate 3 rodadas, guarda a melhor versao.
LIMITES (ditos no relatorio): nao mede estetica, nem legibilidade/enquadramento de texto, nem sincronia fina entre
legenda e fala (isso vem da transcricao com marcas de tempo). Pontuacao nunca e 100: mede so o que foi medido."""
import json
import re
import shutil
import subprocess
from pathlib import Path

FF = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
FP = shutil.which("ffprobe") or shutil.which("ffprobe.exe")


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


def sonda(arq):
    r = _run([FP, "-v", "error", "-count_frames", "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,r_frame_rate,nb_read_frames,duration",
              "-show_entries", "format=duration", "-of", "json", str(arq)])
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def _fps(txt):
    try:
        a, b = str(txt).split("/")
        return float(a) / float(b) if float(b) else 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0


def medir_audio(arq):
    """Loudness integrado (LUFS), pico real (dBTP), pico de amostra (dB) e silencios longos."""
    r = _run([FF, "-hide_banner", "-nostats", "-i", str(arq), "-af", "ebur128=peak=true,volumedetect,silencedetect=n=-45dB:d=1.2", "-vn", "-f", "null", "-"])
    t = r.stderr
    resumo = t[t.rfind("Summary:"):] if "Summary:" in t else ""
    lufs = re.search(r"I:\s+(-?[\d.]+) LUFS", resumo)
    pico = re.search(r"Peak:\s+(-?[\d.]+) dBFS", resumo)
    maxv = re.search(r"max_volume:\s*(-?[\d.]+) dB", t)
    sil = [(float(a), float(b)) for a, b in re.findall(r"silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+)", t)]
    return {"lufs": float(lufs.group(1)) if lufs else None, "pico_dbtp": float(pico.group(1)) if pico else None,
            "max_volume_db": float(maxv.group(1)) if maxv else None, "silencios": sil}


def medir_video(arq):
    r = _run([FF, "-hide_banner", "-nostats", "-i", str(arq), "-vf", "blackdetect=d=0.3:pix_th=0.06,freezedetect=n=-55dB:d=1.5", "-an", "-f", "null", "-"])
    t = r.stderr
    pretos = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", t)]
    ini = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", t)]
    dur = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", t)]
    return {"pretos": pretos, "congelados": list(zip(ini, dur))}


def inspecionar(arq, esperado_s=None, resolucao=(1080, 1920)):
    """Devolve {'achados': [...], 'pontuacao': {...}, 'medidas': {...}}. Nunca levanta erro: falha vira achado."""
    arq = Path(arq)
    ach = []

    def add(ts, cat, grav, evid, corr):
        ach.append({"timestamp": ts, "categoria": cat, "gravidade": grav, "evidencia": evid, "correcao": corr, "verificacao": "pendente"})

    if not FF or not FP or not arq.exists():
        add(None, "arquivo", "grave", "ffmpeg/ffprobe indisponivel ou arquivo ausente", "instalar ffmpeg / renderizar de novo")
        return {"achados": ach, "pontuacao": {}, "medidas": {}}
    info = sonda(arq)
    vs = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    au = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
    dur = float((info.get("format") or {}).get("duration") or 0)
    med = {"duracao_s": round(dur, 2)}
    if not vs:
        add(None, "arquivo", "grave", "sem stream de video", "renderizar de novo")
        return {"achados": ach, "pontuacao": {}, "medidas": med}
    fps = _fps(vs.get("avg_frame_rate"))
    nq = int(vs.get("nb_read_frames") or 0)
    med.update({"resolucao": f"{vs.get('width')}x{vs.get('height')}", "fps": round(fps, 2), "codec_video": vs.get("codec_name"), "pix_fmt": vs.get("pix_fmt"),
                "quadros": nq, "codec_audio": au.get("codec_name") if au else None})
    # formato / compatibilidade
    if (vs.get("width"), vs.get("height")) != resolucao:
        add(None, "formato", "grave", f"resolucao {vs.get('width')}x{vs.get('height')} (esperado {resolucao[0]}x{resolucao[1]})", "renderizar com a composicao 1080x1920")
    if vs.get("codec_name") != "h264" or vs.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
        add(None, "compatibilidade", "atencao", f"codec {vs.get('codec_name')} / {vs.get('pix_fmt')} (TikTok prefere h264 + yuv420p)", "recodificar com ffmpeg -c:v libx264 -pix_fmt yuv420p")
    if au is None:
        add(None, "audio", "grave", "o video nao tem trilha de audio", "refazer o mix de audio")
    elif au.get("codec_name") != "aac":
        add(None, "compatibilidade", "atencao", f"audio {au.get('codec_name')} (esperado aac)", "recodificar o audio para aac")
    # quedas de quadros / FPS variavel: quadros lidos x (duracao*fps)
    if fps and dur and nq:
        esperado_q = dur * fps
        if abs(nq - esperado_q) / esperado_q > 0.02:
            add(None, "fluidez", "atencao", f"{nq} quadros lidos, {esperado_q:.0f} esperados ({abs(nq - esperado_q) / esperado_q * 100:.1f}% de diferenca)", "renderizar de novo com menos concorrencia")
    if esperado_s and dur and abs(dur - esperado_s) > 1.5:
        add(None, "sincronia", "atencao", f"duracao do video {dur:.1f}s x narracao+margem {esperado_s:.1f}s", "conferir o fim do video e a narracao")
    # video: preto e congelado
    mv = medir_video(arq)
    for a, b in mv["pretos"]:
        if a > 0.3 and b < dur - 0.5:
            add(f"{a:.1f}s", "quadro_preto", "grave", f"tela preta de {a:.1f}s a {b:.1f}s", "conferir a cena nesse trecho e renderizar de novo")
    for a, d in mv["congelados"]:
        add(f"{a:.1f}s", "imagem_parada", "atencao" if d < 3 else "grave", f"imagem sem nenhuma mudanca por {d:.1f}s", "trocar a cena por uma com movimento")
    # audio
    if au is not None:
        ma = medir_audio(arq)
        med.update({"lufs": ma["lufs"], "pico_dbtp": ma["pico_dbtp"]})
        if ma["lufs"] is not None and not (-17.0 <= ma["lufs"] <= -11.0):
            add(None, "audio_volume", "atencao", f"volume integrado {ma['lufs']:.1f} LUFS (faixa boa: -17 a -11)", "normalizar para -14 LUFS")
        if ma["pico_dbtp"] is not None and ma["pico_dbtp"] > -0.5:
            add(None, "audio_estouro", "atencao", f"pico real {ma['pico_dbtp']:.1f} dBTP (risco de distorcer)", "limitar o pico a -1.5 dBTP")
        if ma["max_volume_db"] is not None and ma["max_volume_db"] < -35:
            add(None, "audio_volume", "grave", f"audio quase mudo (max {ma['max_volume_db']:.0f} dB)", "refazer o mix")
        for a, b in ma["silencios"]:
            if a > 0.5 and b < dur - 0.5:
                add(f"{a:.1f}s", "audio_silencio", "atencao", f"silencio total de {a:.1f}s a {b:.1f}s", "conferir se a narracao/musica falhou")
    # pontuacao (so o que foi medido; nunca 100)
    def nota(cats, peso_grave=45, peso_at=15):
        p = 99
        for x in ach:
            if x["categoria"] in cats:
                p -= peso_grave if x["gravidade"] == "grave" else peso_at
        return max(0, p)
    pont = {
        "Integridade do arquivo": {"nota": nota({"arquivo", "formato"}), "medido": "streams, resolucao, duracao", "limite": "nao detecta corrupcao parcial no meio do arquivo"},
        "Compatibilidade": {"nota": nota({"compatibilidade"}), "medido": "codec h264, yuv420p, aac", "limite": "nao testa em cada aplicativo/telefone"},
        "Audio": {"nota": nota({"audio", "audio_volume", "audio_estouro", "audio_silencio"}), "medido": "LUFS, pico real, silencios", "limite": "nao mede clareza da voz"},
        "Fluidez": {"nota": nota({"fluidez", "imagem_parada", "quadro_preto"}), "medido": "quadros lidos x esperados, tela preta, imagem parada", "limite": "nao mede suavidade das animacoes"},
        "Sincronia": {"nota": nota({"sincronia"}), "medido": "duracao do video x narracao", "limite": "NAO mede sincronia fina palavra-por-palavra"},
    }
    return {"achados": ach, "pontuacao": pont, "medidas": med,
            "nao_medido": ["legibilidade de textos", "enquadramento/area segura", "estetica e coerencia com a narrativa", "sincronia fina da legenda"]}


def corrigir_audio(arq, lufs=-14.0, tp=-1.5):
    """Normaliza SO o audio (video copiado sem re-renderizar). Devolve True se o arquivo novo foi validado e substituiu o antigo."""
    arq = Path(arq)
    tmp = arq.with_name(arq.stem + "_fix.mp4")
    antes = float((sonda(arq).get("format") or {}).get("duration") or 0)
    r = _run([FF, "-y", "-v", "error", "-i", str(arq), "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11",
              "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(tmp)])
    if r.returncode != 0 or not tmp.exists():
        tmp.unlink(missing_ok=True)
        return False
    depois = float((sonda(tmp).get("format") or {}).get("duration") or 0)
    if not antes or abs(depois - antes) > 0.25:
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(arq)
    return True


def inspecionar_e_refinar(arq, esperado_s=None, rodadas=3, lufs=-14.0, log=print):
    """Inspeciona; se houver problema de AUDIO corrigivel, corrige (ate N rodadas) e REINSPECIONA; guarda a melhor versao.
    Os demais achados so sao reportados (a correcao exigiria renderizar a cena de novo)."""
    arq = Path(arq)
    rel = inspecionar(arq, esperado_s)
    ini = [dict(x) for x in rel["achados"]]
    corrigiveis = {"audio_volume", "audio_estouro"}
    n = 0
    while n < rodadas and any(x["categoria"] in corrigiveis and x["gravidade"] != "grave" for x in rel["achados"]):
        n += 1
        bak = arq.with_name(arq.stem + "_antes_ajuste.mp4")
        shutil.copyfile(arq, bak)
        pior = len(rel["achados"])
        if corrigir_audio(arq, lufs) is False:
            bak.unlink(missing_ok=True)
            log("   inspetor: nao consegui ajustar o audio (mantive o original).")
            break
        novo = inspecionar(arq, esperado_s)
        if len(novo["achados"]) <= pior:
            bak.unlink(missing_ok=True)
            rel = novo
            log(f"   inspetor: audio ajustado (rodada {n}): problemas {pior} -> {len(novo['achados'])}.")
        else:   # piorou: restaura a melhor versao
            shutil.copyfile(bak, arq)
            bak.unlink(missing_ok=True)
            log("   inspetor: o ajuste nao melhorou; restaurei a versao anterior.")
            break
    # resultado da verificacao por achado inicial
    final = {(x["categoria"], x["timestamp"]) for x in rel["achados"]}
    for x in ini:
        x["verificacao"] = ("persistiu apos correcao" if n else "nao corrigido automaticamente") if (x["categoria"], x["timestamp"]) in final else "resolvido e reverificado"
    rel["achados_iniciais"] = ini
    rel["rodadas_refino"] = n
    return rel


def escrever(rel, pasta, nome_base):
    pasta = Path(pasta)
    (pasta / "RELATORIO_QUALIDADE.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["RELATORIO DE QUALIDADE (medicoes objetivas do arquivo final)", ""]
    for k, v in rel.get("pontuacao", {}).items():
        L.append(f"{k}: {v['nota']}/100  (medido: {v['medido']}; limite: {v['limite']})")
    m = rel.get("medidas", {})
    L += ["", "Medidas: " + ", ".join(f"{k}={v}" for k, v in m.items() if v is not None), ""]
    ini = rel.get("achados_iniciais") or rel.get("achados", [])
    if ini:
        L.append("PROBLEMAS (timestamp | categoria | gravidade | evidencia | correcao | verificacao):")
        for x in ini:
            L.append(f"- {x['timestamp'] or 'geral'} | {x['categoria']} | {x['gravidade']} | {x['evidencia']} | {x['correcao']} | {x['verificacao']}")
    else:
        L.append("Nenhum problema encontrado nas verificacoes acima.")
    L += ["", "NAO MEDIDO (confira assistindo): " + "; ".join(rel.get("nao_medido", [])),
          "As notas medem so o que esta escrito em 'medido'. Nao sao garantia de qualidade profissional."]
    (pasta / "RELATORIO_QUALIDADE.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return pasta / "RELATORIO_QUALIDADE.txt"


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python inspetor.py video.mp4   (so inspeciona, nao altera o arquivo)")
        sys.exit(1)
    r = inspecionar(sys.argv[1])
    print(escrever(r, Path(sys.argv[1]).parent, "x").read_text(encoding="utf-8"))
