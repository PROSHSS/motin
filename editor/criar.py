"""
criar.py - gera um video completo a partir de um tema (ou briefing).

Uso:
    python criar.py "Como funciona o segundo turno"
    python criar.py "Tema do video" --fatos fatos.txt
    python criar.py "Tema do video" --novo        (cria uma pasta nova, sem reaproveitar)
    python criar.py "Tema do video" --rerender    (renderiza de novo, depois de mudar o visual)

Cada video fica em:  projetos\\<nome-do-tema>\\
O MP4 final fica em: saidas\\<nome-do-tema>.mp4
Se der erro no meio, rode o mesmo comando de novo: ele continua de onde parou.
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import zlib
from pathlib import Path

import requests

import cinema

RAIZ = Path(__file__).resolve().parent
CONFIG = RAIZ / "config.json"
OLLAMA_URL = "http://localhost:11434"
WINDOWS = os.name == "nt"

PADRAO = {
    "cf_account_id": "",
    "cf_api_token": "",
    "gerenciar_ollama": True,     # abre e fecha o Ollama sozinho (sem usar a placa de video)
    "modelo_ollama": "qwen3.5:9b",
    "modelo_visao": "",           # opcional: modelo que OLHA a foto e confere se combina (ex.: "qwen3.5:9b" ja enxerga | "gemma4:12b"). Vazio = desligado
    "modelo_juiz": "",            # opcional: modelo MAIOR so para conferir as frases (ex.: "gemma4:12b"). Vazio = o mesmo modelo
    "concorrencia": 4,            # nucleos usados na renderizacao (4 a 6 com 16 GB de RAM)
    "motor_voz": "kokoro",        # "kokoro" (rapido) ou "chatterbox" (mais natural, mais lento)
    "python_voz": "",             # caminho do python do ambiente do Chatterbox (veja o LEIAME)
    "voz_referencia": "voz_referencia.wav",   # audio de 10 a 20 s de uma voz autorizada (opcional)
    "musica": True,               # musica de fundo (pasta musicas; se vazia, usa uma trilha gerada)
    "efeitos": True,              # efeitos sonoros (whoosh, impacto, pop...)
    "volume_efeitos": 1.0,        # volume geral dos efeitos (0.5 = metade)
    "gerar_capa": True,           # salva saidas\\<tema>_capa.png (quadro de abertura para a capa do TikTok)
    "grade_cinema": True,         # acabamento de cinema nas imagens de IA (cor, grao, contraste)
    "polir_voz": True,            # acabamento de estudio na voz (compressao/EQ). false = voz crua
    "legenda": "documentario",    # "documentario" (texto branco com sombra) | "pilula" (caixa)
    "edicao": "motion",
    "intensidade_motion": "equilibrado",
    "variedade_motion": "criativa",
    "camada_documentario": True,  # camera com tremor leve, zoom nas frases, vinheta, cor de cinema, barra de progresso
    "som_transicao": True,        # false = sem o som de deslize nas trocas de cena
    "volume_musica": 1.0,         # 0.5 = mais baixa | 1.0 = padrao | 1.5 = mais alta
    "normalizar_volume": True,    # ajusta o volume final para o padrao do TikTok
    "lufs": -14,                  # alvo de volume (-14 e o padrao de TikTok/Reels)
    "cta": "Siga para mais",      # botao de chamada no final do video ("" = sem botao)
    "show_source_labels": False,  # False = NENHUMA etiqueta "Fonte:"/"Foto:"/credito sobre a imagem (creditos ficam em NOME_CREDITOS.txt). True = mostra no canto
    "marca": "",                  # seu @ (ex: "@meuperfil"): aparece no canto e no botao final
    "pesquisar": True,            # pesquisa fontes na internet antes de escrever e confere cada frase (mais lento, bem mais seguro)
    "imagens": True,              # cenas com foto de IA (Cloudflare). false = so cenas animadas
    "n_pontos": 11,               # tamanho do roteiro (11 = ~70 s). Menos = video mais curto
    "ritmo_fala": 0.94,           # 1.0 = velocidade normal | 0.9 = mais devagar (a voz fica no mesmo tom)
    "respiro": 0.3,               # segundos de pausa ao fim de cada cena
    "fotos_reais": "retratos",    # "retratos" = imagens de IA realistas em tudo; foto real livre so para PESSOAS/instituicoes citadas
                                  # "auto" = tenta foto real livre antes da IA em todas as cenas | "so_reais" = nunca usa IA | "nunca" = so IA
    "estilo_imagem": "realista",  # "realista" | "cinematografico" | "editorial" | "limpo" (visual claro antigo)
    "imagens_por_video": 11,      # total de imagens de IA por video (cenas de foto + fundos das cenas animadas). ~95 imagens/dia na Cloudflare
    "permitir_cc_by_sa": False,   # true = aceita tambem fotos CC BY-SA (exigem compartilhar igual; deixe false por seguranca)
    "rotular_ia": True,           # marca na tela 'Imagem ilustrativa (gerada por IA)' (recomendado em documentario)
    "recorte": "auto",            # retrato sem fundo nas cenas de perfil (precisa: pip install rembg onnxruntime) | "nunca"
    "max_fotos": 7,               # quantas cenas de foto por video (a cota da Cloudflare e ~95 fotos/dia)
    "mistura": None,              # 0 = so Showcase | 0.5 = metade classico | None = decide o estilo sorteado
    "pasta_dados": "",            # ex: "D:/doc-tiktok-dados" -> projetos e videos prontos vao para outro disco (HD)
}


# ----------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------
def log(msg=""):
    print(msg, flush=True)


def titulo_etapa(n, total, nome):
    log("")
    log("=" * 60)
    log(f" [{n}/{total}] {nome}")
    log("=" * 60)


SEM_PERGUNTAS = bool(os.environ.get("CRIAR_SEM_PERGUNTAS"))  # painel: nunca esperar digitacao no CMD


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return (t[:50].strip("-")) or "video"


def carregar_config():
    cfg = dict(PADRAO)
    if CONFIG.exists():
        try:
            cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            log("AVISO: config.json esta com erro de formato. Apague o arquivo para recriar.")
            sys.exit(1)
    alterado = False
    if len(str(cfg["cf_account_id"])) < 16:
        cfg["cf_account_id"] = ""  # valor de teste/invalido (ex.: "x")
    if len(str(cfg["cf_api_token"])) < 20:
        cfg["cf_api_token"] = ""
    try:
        ajustes_painel = json.loads(os.environ.get('CRIAR_CONFIG_JSON') or '{}')
    except ValueError:
        ajustes_painel = {}
    precisa_cf = ajustes_painel.get('imagens', cfg.get('imagens', True)) is not False
    if precisa_cf and not cfg["cf_account_id"]:
        if SEM_PERGUNTAS:
            log("ERRO: falta o Account ID da Cloudflare. Abra o painel e preencha 'Cloudflare' no topo da pagina.")
            sys.exit(1)
        cfg["cf_account_id"] = input("Cole o Account ID da Cloudflare: ").strip()
        alterado = True
    if precisa_cf and not cfg["cf_api_token"]:
        if SEM_PERGUNTAS:
            log("ERRO: falta o token da Cloudflare. Abra o painel e preencha 'Cloudflare' no topo da pagina.")
            sys.exit(1)
        cfg["cf_api_token"] = input("Cole o token da Cloudflare: ").strip()
        alterado = True
    if alterado or not CONFIG.exists():
        CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        log("Configuracao salva em config.json (nao compartilhe esse arquivo).")
    # ajustes so deste video (vindos do painel); nao sao gravados no config.json
    try:
        ov = json.loads(os.environ.get("CRIAR_CONFIG_JSON") or "{}")
    except ValueError:
        ov = {}
    for k, v in ov.items():
        if k == "motion_pedido" and isinstance(v,str) and re.fullmatch(r"[0-9a-f]{16,40}",v):
            cfg[k]=v
            continue
        if k == "intensidade_motion" and v in ("suave", "equilibrado", "dinamico"):
            cfg[k] = v
            continue
        if k == "variedade_motion" and v in ("consistente", "criativa", "maxima"):
            cfg[k] = v
            continue
        if k == "edicao" and v in ("motion", "anterior"):
            cfg[k] = v
            continue
        if k in ("n_pontos", "imagens_por_video", "max_fotos") and isinstance(v, int) and 3 <= v <= 14:
            cfg[k] = v
        elif k == "estilo_imagem" and v in ("realista", "cinematografico", "editorial", "limpo"):
            cfg[k] = v
        elif k in ('imagens', 'mascote_falas_exatas') and isinstance(v, bool):
            cfg[k] = v
        elif k == 'fotos_reais' and v in ('retratos', 'auto', 'so_reais', 'nunca'):
            cfg[k] = v
        elif k == 'mascote_voz':
            from mascote import normalizar_perfil
            cfg[k] = normalizar_perfil(v)
        elif k == "show_source_labels" and isinstance(v, bool):
            cfg[k] = v
        elif k == "ritmo_fala" and isinstance(v, (int, float)) and 0.8 <= v <= 1.1:
            cfg[k] = float(v)
    return cfg


def rodar(cmd, cwd, env=None, nome=""):
    """Roda um comando mostrando a saida. Para o programa se falhar."""
    r = subprocess.run(cmd, cwd=str(cwd), env=env)
    if r.returncode != 0:
        log(f"\nERRO na etapa: {nome or cmd[0]} (codigo {r.returncode})")
        log("Corrija o problema e rode o mesmo comando de novo: ele continua de onde parou.")
        sys.exit(r.returncode)


def env_base(cfg):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONWARNINGS"] = "ignore"
    env["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    env["MODELO_OLLAMA"] = cfg["modelo_ollama"]
    env["CF_ACCOUNT_ID"] = cfg["cf_account_id"]
    env["CF_API_TOKEN"] = cfg["cf_api_token"]
    env["IMG_ESTILO"] = str(cfg.get("estilo_imagem", "realista"))
    return env


# ----------------------------------------------------------------------
# Ollama (abre sem GPU, usa, e fecha para liberar a memoria)
# ----------------------------------------------------------------------
def ollama_no_ar():
    try:
        return requests.get(f"{OLLAMA_URL}/api/tags", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def matar_ollama():
    if WINDOWS:
        for nome in ("ollama app.exe", "ollama.exe", "ollama_llama_server.exe"):
            subprocess.run(["taskkill", "/F", "/IM", nome], capture_output=True)
    else:
        subprocess.run(["pkill", "-f", "ollama"], capture_output=True)
    time.sleep(2)


def garantir_modelos(cfg):
    """Baixa sozinho (ollama pull) os modelos escolhidos que ainda nao estao instalados."""
    try:
        tem = {m["name"] for m in requests.get("http://localhost:11434/api/tags", timeout=10).json().get("models", [])}
    except (requests.RequestException, ValueError, KeyError):
        return
    for m in {cfg.get("modelo_ollama"), cfg.get("modelo_juiz"), cfg.get("modelo_visao")} - {None, ""}:
        if m in tem or f"{m}:latest" in tem:
            continue
        log(f"Baixando o modelo {m} (so na primeira vez; pode ser varios GB)...")
        try:
            r = subprocess.run(["ollama", "pull", m])
        except FileNotFoundError:
            return
        if r.returncode != 0:
            log(f"AVISO: nao consegui baixar {m}. Confira o nome em ollama.com/library")


def iniciar_ollama(cfg):
    if not cfg["gerenciar_ollama"]:
        if not ollama_no_ar():
            log("ERRO: o Ollama nao esta aberto. Abra-o ou use gerenciar_ollama = true.")
            sys.exit(1)
        garantir_modelos(cfg)
        return None
    log("Preparando o Ollama (somente CPU, para nao travar)...")
    matar_ollama()
    env = os.environ.copy()
    env["OLLAMA_VULKAN"] = "0"
    env["OLLAMA_NUM_PARALLEL"] = "1"
    try:
        proc = subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if WINDOWS else 0,
        )
    except FileNotFoundError:
        log("ERRO: o comando 'ollama' nao foi encontrado. Reinstale o Ollama ou reinicie o Prompt.")
        sys.exit(1)
    for _ in range(60):
        if ollama_no_ar():
            log("Ollama pronto.")
            garantir_modelos(cfg)
            return proc
        time.sleep(1)
    log("ERRO: o Ollama nao respondeu em 60 segundos.")
    proc.terminate()
    sys.exit(1)


def parar_ollama(cfg, proc):
    if not cfg["gerenciar_ollama"]:
        return
    log("Fechando o Ollama para liberar memoria...")
    try:
        requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": cfg["modelo_ollama"], "keep_alive": 0},
            timeout=10,
        )
    except requests.RequestException:
        pass
    if proc is not None:
        proc.terminate()
    matar_ollama()


# ----------------------------------------------------------------------
# etapas
# ----------------------------------------------------------------------
def preparar_audio(proj, cfg, env, py, nome, sem_musica=False, lufs_musica=-30):
    """Copia efeitos + musica para o projeto e escreve public/audio.json."""
    pub = proj / "public"
    usar_musica = bool(cfg.get("musica", True)) and not sem_musica
    usar_efeitos = bool(cfg.get("efeitos", True))
    ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")

    if usar_efeitos:
        wh = RAIZ / "audio" / "sfx" / "whoosh.wav"
        if not wh.exists() or wh.stat().st_mtime < (RAIZ / "sfx.py").stat().st_mtime:
            log("Criando os efeitos sonoros (uma vez so)...")
            rodar([py, str(RAIZ / "sfx.py")], RAIZ, env, "efeitos sonoros")
        (pub / "sfx").mkdir(exist_ok=True)
        for f in (RAIZ / "audio" / "sfx").glob("*.wav"):
            shutil.copyfile(f, pub / "sfx" / f.name)

    if usar_musica and not ffmpeg:
        log("AVISO: ffmpeg nao encontrado, o video sai sem musica.")
        usar_musica = False
    if usar_musica:
        pasta = RAIZ / "musicas"
        pasta.mkdir(exist_ok=True)
        exts = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}
        proprias = sorted(f for f in pasta.iterdir() if f.suffix.lower() in exts and not f.name.startswith("ambiente_gerada"))
        if not proprias:
            geradas = sorted(pasta.glob("ambiente_gerada_*.wav"))
            if not geradas:
                log("Nenhuma musica na pasta 'musicas'; criando 3 trilhas ambiente gratis (leva 1 a 2 minutos)...")
                rodar([py, str(RAIZ / "sfx.py"), "--musica"], RAIZ, env, "musica ambiente")
                geradas = sorted(pasta.glob("ambiente_gerada_*.wav"))
            proprias = geradas
        escolhida = proprias[zlib.crc32(nome.encode()) % len(proprias)]
        log(f"Musica: {escolhida.name}")
        r = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-i", str(escolhida), "-vn",
             "-af", f"loudnorm=I={lufs_musica}:TP=-3:LRA=7", "-ar", "44100", "-b:a", "192k", str(pub / "musica.mp3")],
        )
        if r.returncode != 0:
            log("AVISO: nao consegui preparar a musica; o video sai sem musica.")
            usar_musica = False
    (pub / "visual.json").write_text(
        json.dumps({"cta": cfg.get("cta", "Siga para mais"), "marca": cfg.get("marca", "")}, ensure_ascii=False),
        encoding="utf-8",
    )
    (pub / "audio.json").write_text(
        json.dumps({
            "musica": usar_musica,
            "sfx": usar_efeitos,
            "volumeMusica": float(cfg.get("volume_musica", 1.0)),
            "volumeSfx": float(cfg.get("volume_efeitos", 1.0)),
            "transicao": bool(cfg.get("som_transicao", True)),
            "legenda": str(cfg.get("legenda", "documentario")),
            "documentario": bool(cfg.get("camada_documentario", True)),
        }),
        encoding="utf-8",
    )


def normalizar_volume(arquivo, lufs):
    """Passe duplo de loudnorm: deixa o audio do MP4 no volume padrao, sem recodificar o video."""
    ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ffmpeg:
        return
    alvo = f"I={lufs}:TP=-1.5:LRA=11"
    p1 = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(arquivo), "-af", f"loudnorm={alvo}:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p1.stderr, re.S)
    filtro = f"loudnorm={alvo}"
    if m:
        try:
            d = json.loads(m.group(0))
            filtro += (f":measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}"
                       f":measured_thresh={d['input_thresh']}:offset={d['target_offset']}:linear=true")
        except (KeyError, json.JSONDecodeError):
            pass
    tmp = arquivo.with_name(arquivo.stem + "_vol.mp4")
    r = subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-i", str(arquivo), "-c:v", "copy", "-af", filtro,
         "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(tmp)],
    )
    if r.returncode == 0 and tmp.exists():
        tmp.replace(arquivo)
        log(f"Volume ajustado para {lufs} LUFS.")
    else:
        log("AVISO: nao consegui ajustar o volume; o video foi mantido como saiu.")
        tmp.unlink(missing_ok=True)


def roteiro_completo(proj):
    f = proj / "roteiro.json"
    if not f.exists():
        return False
    try:
        r = json.loads(f.read_text(encoding="utf-8"))
        return bool(r.get("cenas")) and all(
            c.get("prompt_imagem") or c.get("tipo") in ("frase", "lista_caixas", "painel") for c in r["cenas"]
        )
    except json.JSONDecodeError:
        return False



# ----------------------------------------------------------------------
# MODO PRINCIPAL: video narrado com a edicao Showcase (tudo em um lugar)
# ----------------------------------------------------------------------
def _palavras_limpas(texto):
    t = re.sub(r"\s+", " ", texto.replace("%", " por cento")).strip()
    return [w for w in t.split(" ") if w]


def estimar_palavras(proj):
    """Plano B das legendas: distribui as palavras de cada cena pelo tempo da fala."""
    dados = json.loads((proj / "roteiro.json").read_text(encoding="utf-8"))
    tempos = json.loads((proj / "tempos_cenas.json").read_text(encoding="utf-8"))
    saida = []
    for cena, tp in zip(dados["cenas"], tempos):
        pal = _palavras_limpas(cena.get("narracao", ""))
        if not pal:
            continue
        ini, fim = tp["inicio"] + 0.05, max(tp["inicio"] + 0.6, tp["fim"] - 0.45)
        pesos = [max(2, len(w)) + (4 if w[-1] in ".,!?…" else 0) for w in pal]
        total = float(sum(pesos))
        t = ini
        for w, pe in zip(pal, pesos):
            d = (fim - ini) * pe / total
            saida.append({"palavra": w, "inicio": round(t, 2), "fim": round(t + d * 0.92, 2)})
            t += d
    (proj / "palavras.json").write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")


def desacelerar(proj, fator):
    """Deixa a fala um pouco mais lenta sem mudar o tom (ffmpeg atempo) e acompanha os tempos das cenas."""
    if not fator or abs(fator - 1.0) < 0.01:
        return
    ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ff:
        return
    orig = proj / "narracao.wav"
    tmp = proj / "narracao_lenta.wav"
    r = subprocess.run([ff, "-y", "-v", "error", "-i", str(orig), "-filter:a", f"atempo={fator}", str(tmp)])
    if r.returncode != 0 or not tmp.exists():
        return
    tmp.replace(orig)
    tempos = json.loads((proj / "tempos_cenas.json").read_text(encoding="utf-8"))
    for t in tempos:
        t["inicio"] = round(t["inicio"] / fator, 2)
        t["fim"] = round(t["fim"] / fator, 2)
    (proj / "tempos_cenas.json").write_text(json.dumps(tempos, indent=2), encoding="utf-8")
    log(f"Fala desacelerada para {int(fator * 100)}% da velocidade.")


def validar_roteiro(proj, dados):
    """Antes de renderizar: nenhuma cena pode apontar para arquivo que nao existe (evita erro de render).
    Cena de foto sem foto vira citacao com a propria narracao; imagem de fundo faltando e removida."""
    pub = proj / "public"
    n = 0
    for i, c in enumerate(dados["cenas"]):
        if c.get("video") and not (pub / c["video"]["arquivo"]).is_file():
            raise ValueError(f"O vídeo da cena {i+1} está faltando. Reenvie o arquivo.")
        for k in ("foto", "recorte", "objeto"):
            if c.get(k) and not (pub / c[k]).exists():
                c.pop(k, None)
                n += 1
        cl = c.get("cena") if c.get("tipo") == "classica" else None
        if cl and cl.get("imagem") and not (pub / cl["imagem"]).exists():
            cl.pop("imagem", None)
            n += 1
        precisa_foto = str(c.get("tipo", "")).startswith("foto_")
        if precisa_foto and not c.get("foto") and not c.get("video"):
            nar = c.get("narracao", "")
            partes = [p.strip() for p in re.split(r"(?<=[.!?])\s+", nar) if p.strip()]
            dados["cenas"][i] = {"tipo": "citacao", "narracao": nar, "manchete": [], "duracao": c.get("duracao", 3.0),
                                 "citacao": {"texto": (partes[0] if partes else nar)[:90].rstrip(" ,;"), "autor": ""},
                                 **{k: c[k] for k in ("fonte", "evidencia", "fatos") if c.get(k)}}
            n += 1
    if n:
        log(f"Conferencia antes do render: {n} referencia(s) a arquivo faltando corrigida(s) automaticamente.")
    return n


def auditar_texto_tela(proj, dados):
    """Ultima barreira: confere TODO texto que aparece na tela (nao so a narracao). Cena com texto estranho
    (palavra cortada, termina em 'de/o/que', palavra repetida, 'undefined', parenteses abertos...) e trocada por
    uma cena segura que so usa a propria narracao. Escreve TEXTO_NA_TELA.txt para voce conferir."""
    import showcase_gen as G
    import roteirista as R
    ruim = re.compile(r"undefined|\bnull\b|\bNaN\b|\[object|\{\{|\}\}|lorem|\bTODO\b", re.I)
    linhas, trocadas = [], 0
    for i, c in enumerate(dados["cenas"]):
        achados = []
        base_pal = {R.norm(w) for w in re.findall(r"[\wÀ-ÿ%$-]+", f"{c.get('narracao', '')} {c.get('evidencia', '')} {dados.get('titulo', '')} {dados.get('marca', '')}")}
        if c.get("fantasma") and R.norm(str(c["fantasma"])) not in base_pal:   # palavra de fundo cortada ou inventada
            antigo = c["fantasma"]
            c["fantasma"] = G.fantasma_ok("", c.get("narracao", ""), 12)
            linhas.append(f"Cena {i + 1:02d}: palavra de fundo '{antigo}' nao era uma palavra inteira da narracao -> '{c['fantasma']}'")
        textos = [t.strip() for t in R.textos_da_cena({k: v for k, v in c.items() if k not in ("credito", "aviso", "rotulo_ia")}) if isinstance(t, str) and t.strip()]
        mpartes = [p_["t"].strip() for ln_ in (c.get("manchete") or []) for p_ in ln_ if isinstance(p_, dict) and p_.get("t")]
        meio_manchete = set(mpartes[:-1])   # a manchete quebra em varias partes: so a ULTIMA precisa fechar a frase
        for t in textos:
            pal = t.split()
            if ruim.search(t):
                achados.append(f"texto invalido: {t!r}")
            if re.search(r"\s{2,}|\s[,.;:!?]", t):
                achados.append(f"espacamento estranho: {t!r}")
            if len(pal) > 1 and pal[-1].lower().strip(".,;:!?…") in G._PENDENTES and c.get("tipo") not in ("fecho",) and t not in meio_manchete:
                achados.append(f"termina em palavra solta: {t!r}")
            if re.search(r"\b([A-Za-zÀ-ÿ]{3,})\s+\1\b", t, re.I):
                achados.append(f"palavra repetida: {t!r}")
            if t.count("(") != t.count(")") or t.count('"') % 2:
                achados.append(f"parenteses/aspas abertos: {t!r}")
            for w in R.norm(t).split():
                if len(w) >= 5 and w not in base_pal and any(b.startswith(w) and len(b) - len(w) >= 2 for b in base_pal):
                    achados.append(f"palavra cortada: {w.upper()!r}")
                    break
            if len(t) > 120:
                achados.append(f"texto longo demais: {t[:40]!r}...")
        linhas.append(f"Cena {i + 1:02d} [{c.get('tipo')}]" + (f"   <-- PROBLEMA: {'; '.join(achados)}" if achados else ""))
        for t in textos:
            linhas.append(f"    {t}")
        if achados and c.get("tipo") not in ("fecho", "gancho") and c.get("narracao"):
            evitar = [x["tipo"] for x in dados["cenas"][max(0, i - 2): i + 3]]
            seg = R.cena_segura({"narracao": c["narracao"]}, random.Random(i), False, i, evitar)
            novo = G.sanear_cena(seg, random.Random(i), {"nome": dados.get("estilo", ""), "paleta": [dados.get("paleta", "ouro")]})
            if novo:
                for k in ("narracao", "fonte", "evidencia", "fatos", "video", "credito_video"):
                    if c.get(k):
                        novo[k] = c[k]
                dados["cenas"][i] = novo
                trocadas += 1
                linhas.append("    (cena trocada por uma versao segura)")
    (proj / "TEXTO_NA_TELA.txt").write_text("TODO TEXTO QUE APARECE NO VIDEO, cena por cena:\n\n" + "\n".join(linhas) + "\n", encoding="utf-8")
    if trocadas:
        log(f"Conferencia de texto na tela: {trocadas} cena(s) com texto estranho foram trocadas por versoes seguras.")
    else:
        log("Conferencia de texto na tela: ok (lista completa em TEXTO_NA_TELA.txt).")
    return trocadas


def polir_voz(origem, destino):
    """Acabamento de estudio na narracao (so no arquivo do video): corta grave de ruido, comprime e deixa mais presente.
    Nao muda a duracao, entao legendas e cenas continuam sincronizadas."""
    ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ff:
        shutil.copyfile(origem, destino)
        return False
    import soundfile as sf
    try:
        sr = sf.info(str(origem)).samplerate
    except Exception:
        sr = 24000
    filtro = ("highpass=f=80,acompressor=threshold=0.125:ratio=3:attack=8:release=120:makeup=2,"
              "equalizer=f=3200:t=q:w=1.2:g=2.5,equalizer=f=220:t=q:w=1:g=1.5,alimiter=limit=0.9")
    tmp = destino.with_suffix(".tmp.wav")
    r = subprocess.run([ff, "-y", "-v", "error", "-i", str(origem), "-af", filtro, "-ar", str(sr), str(tmp)])
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 1000:
        tmp.unlink(missing_ok=True)
        shutil.copyfile(origem, destino)
        return False
    d0, d1 = sf.info(str(origem)).duration, sf.info(str(tmp)).duration
    if abs(d0 - d1) > 0.05:  # nunca arriscar dessincronizar
        tmp.unlink(missing_ok=True)
        shutil.copyfile(origem, destino)
        return False
    tmp.replace(destino)
    return True


def gerar_capa(proj, saida, npx, env, concorrencia=2):
    """Capa (imagem de abertura) para escolher no TikTok: um quadro forte do comeco do video."""
    destino = saida.with_name(saida.stem + "_capa.png")
    try:
        r = subprocess.run([npx, "remotion", "still", "src/index.ts", "Showcase", str(destino), "--frame=42",
                            f"--public-dir={proj / 'public'}"], cwd=str(RAIZ), env=env, capture_output=True, text=True, timeout=300)
    except (subprocess.SubprocessError, OSError):
        return
    if r.returncode == 0 and destino.exists():
        log(f"Capa do video: {destino}")
    else:
        log("AVISO: nao consegui gerar a capa (o video esta ok).")


def relatorio_final(proj, dados, saida, problemas_qa):
    """Resumo de confianca do video: o que foi conferido e se esta pronto para postar. Alimenta a pagina 'Meus videos'."""
    serio = dados.get("modo") == "serio"
    cenas = dados.get("cenas", [])
    fontes = sorted({str(c.get("fonte")) for c in cenas if c.get("fonte")})
    com_fonte = sum(1 for c in cenas if c.get("fonte"))
    n_fatos = len(dados.get("fatos_usados") or [])
    ia = sum(1 for c in cenas if (c.get("foto") and not c.get("real")) or c.get("fundo_foto"))
    reais = sum(1 for c in cenas if c.get("real"))
    try:
        tela = (proj / "TEXTO_NA_TELA.txt").read_text(encoding="utf-8")
    except OSError:
        tela = ""
    trocas = tela.count("cena trocada") + len(re.findall(r"palavra de fundo", tela))
    itens, grave, atencao = [], [], []

    def item(ok, txt, gravidade="atencao"):
        itens.append({"ok": bool(ok), "txt": txt})
        if not ok:
            (grave if gravidade == "grave" else atencao).append(txt)

    item(problemas_qa is not None and not problemas_qa, "Conferencia do arquivo: audio presente, volume ok, sem tela preta" if not problemas_qa else "Arquivo: " + "; ".join(problemas_qa or ["nao foi possivel conferir (ffmpeg)"]), "grave" if problemas_qa else "atencao")
    item(n_fatos >= 3 or not serio, f"{n_fatos} fato(s) com fonte usados no roteiro" if n_fatos >= 3 or not serio else f"Poucos fatos com fonte ({n_fatos}) para um assunto serio", "grave" if serio and n_fatos == 0 else "atencao")
    item(com_fonte >= 2 or not serio, f"{com_fonte} cena(s) mostram a fonte na tela" if com_fonte >= 2 or not serio else "Poucas cenas mostram fonte na tela")
    item(trocas <= 2, "Texto na tela sem problemas relevantes" if trocas <= 2 else f"{trocas} ajustes automaticos de texto: leia TEXTO_NA_TELA.txt")
    item(True, f"Imagens: {ia} geradas por IA (sem etiqueta na tela; ative o rotulo de IA do TikTok) e {reais} fotos reais com credito")
    if serio:
        atencao.append("Assunto serio: leia o arquivo CONFERIR antes de postar")
    veredito = "NAO POSTAR (corrigir antes)" if grave else ("CONFERIR ANTES DE POSTAR" if atencao else "PRONTO PARA POSTAR")
    rel = {"veredito": veredito, "itens": itens, "fontes": fontes, "serio": serio, "avisos": atencao + grave}
    (proj / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    linhas = [f"VEREDITO: {veredito}", ""] + [("[ok] " if i["ok"] else "[!!] ") + i["txt"] for i in itens]
    if serio:
        linhas.append("[!!] Assunto serio: leia o arquivo CONFERIR antes de postar")
    if fontes:
        linhas += ["", "Fontes citadas: " + "; ".join(fontes)]
    (proj / "RELATORIO.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    shutil.copyfile(proj / "RELATORIO.txt", saida.with_name(saida.stem + "_RELATORIO.txt"))
    log(f"Veredito: {veredito}")
    return rel


_STOP_TAG = {"para", "como", "sobre", "entre", "mais", "isso", "esse", "essa", "este", "esta", "pelo", "pela", "quando", "onde", "porque", "caso", "qual", "quais", "tudo", "todos"}


def pacote_postagem(proj, dados, saida):
    """Texto pronto para colar no TikTok: legenda com fontes, hashtags e 3 opcoes de titulo na capa."""
    titulo = str(dados.get("titulo", "")).strip()
    sem_ac = lambda t: unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()  # noqa: E731
    palavras = [w for w in re.findall(r"[A-Za-zÀ-ÿ0-9]+", titulo) if len(w) > 3 and w.lower() not in _STOP_TAG]
    tags, vistos = [], set()
    for w in palavras:
        t = "#" + sem_ac(w).lower()
        if t not in vistos:
            vistos.add(t)
            tags.append(t)
    tags = tags[:4] + (["#noticias", "#brasil"] if dados.get("modo") == "serio" else ["#curiosidades", "#documentario"]) + ["#fyp"]
    legenda = ""
    try:
        legenda = (proj / "legenda_post.txt").read_text(encoding="utf-8").strip()
    except OSError:
        pass
    base_t = titulo.rstrip("?.! ")
    opcoes = [titulo, "Entenda: " + base_t, base_t + " (os fatos)"]
    txt = ["PACOTE DE POSTAGEM", "", "--- LEGENDA (copie e cole) ---", legenda, "", " ".join(tags), "",
           "--- 3 opcoes de titulo para a capa (escolha a que combina) ---"] + [f"{i}. {o}" for i, o in enumerate(opcoes, 1)] + \
          ["", "Dicas: poste entre 18h e 21h; fixe um comentario com a fonte; responda os primeiros comentarios na primeira hora."]
    arq = saida.with_name(saida.stem + "_POSTAGEM.txt")
    arq.write_text("\n".join(txt) + "\n", encoding="utf-8")
    log(f"Pacote de postagem (legenda + hashtags): {arq}")


def qa_video(arquivo):
    """Conferencia final: tem audio? duracao razoavel? quadros pretos? Escreve o resultado no log."""
    ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ff or not Path(arquivo).exists():
        return None
    r = subprocess.run([ff, "-hide_banner", "-i", str(arquivo), "-vf", "blackdetect=d=0.4:pix_th=0.06", "-af", "volumedetect",
                        "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    t = r.stderr
    problemas = []
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", t)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0
    if "Audio:" not in t:
        problemas.append("o video ficou SEM AUDIO")
    mv = re.search(r"max_volume:\s*(-?[\d.]+) dB", t)
    if mv and float(mv.group(1)) < -35:
        problemas.append("audio muito baixo")
    pretos = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", t)
    pretos = [(a, b) for a, b in pretos if float(a) > 0.3 and float(b) < dur - 0.5]
    if pretos:
        problemas.append("tela preta em " + ", ".join(f"{float(a):.1f}s" for a, _ in pretos[:4]))
    if dur and (dur < 12 or dur > 175):
        problemas.append(f"duracao estranha ({dur:.0f}s)")
    if problemas:
        log("ATENCAO (conferencia final): " + "; ".join(problemas) + ". Assista antes de postar.")
    else:
        log(f"Conferencia final: ok ({dur:.0f}s, audio presente, sem tela preta).")
    return problemas


def ajustar_minimos(proj, dados, respiro=0.3, escala=1.2):
    """Cada cena precisa de um tempo minimo para a animacao aparecer inteira e de um respiro no fim:
    insere silencio se a fala for curta."""
    import numpy as np
    import soundfile as sf
    import showcase_gen as G
    audio, sr = sf.read(str(proj / "narracao.wav"), dtype="float32")
    tempos = json.loads((proj / "tempos_cenas.json").read_text(encoding="utf-8"))
    pecas, cursor, deslocamento = [], 0, 0.0
    novos = []
    for cena, tp in zip(dados["cenas"], tempos):
        minimo = G.DUR.get(cena["tipo"], 2.5) * escala
        if cena["tipo"] == "fato_real" and not cena.get("numero"):
            minimo = 4.8 * escala
        dur = tp["fim"] - tp["inicio"]
        falta = max(float(respiro), minimo - dur)
        fim_amostra = int(round(tp["fim"] * sr))
        pecas.append(audio[cursor:fim_amostra])
        if falta > 0.05:
            pecas.append(np.zeros((int(sr * falta),) + audio.shape[1:], dtype=np.float32))
        cursor = fim_amostra
        novos.append({"cena": tp.get("cena", len(novos) + 1), "inicio": round(tp["inicio"] + deslocamento, 2),
                      "fim": round(tp["fim"] + deslocamento + falta, 2)})
        deslocamento += falta
    pecas.append(audio[cursor:])
    sf.write(str(proj / "narracao.wav"), np.concatenate(pecas), sr)
    (proj / "tempos_cenas.json").write_text(json.dumps(novos, indent=2), encoding="utf-8")


def mistura_efetiva(args, cfg):
    if getattr(args, "so_showcase", False):
        return 0.0
    if getattr(args, "mistura", None) is not None:
        return args.mistura
    return cfg.get("mistura")


def usar_imagens(args, cfg):
    if getattr(args, "sem_imagens", False) or not cfg.get("imagens", True):
        return False
    return bool(cfg.get("cf_account_id") and cfg.get("cf_api_token"))


def eh_foto(c):
    if c.get("video"):
        return False
    return c["tipo"].startswith("foto_") or c["tipo"] == "fato_real" or (c["tipo"] == "classica" and (c.get("cena") or {}).get("tipo") == "imagem")


def quer_imagem(c):
    if c.get("video"):
        return False
    return eh_foto(c) or bool(c.get("fundo_foto"))


def _texto_puro(linhas):
    return " ".join(re.sub(r"[*_]", "", str(x)) for x in (linhas or []))


def fotos_prompts(proj, dados, cfg, env, py, ia=True):
    """Passo 1 das fotos (precisa do Ollama): escreve a descricao de cada foto."""
    idx = [i for i, c in enumerate(dados["cenas"]) if quer_imagem(c)]
    if not idx:
        return
    tmp = proj / "_img"
    (tmp / "public").mkdir(parents=True, exist_ok=True)
    cenas = []
    for i, c in enumerate(dados["cenas"]):
        dest = (c.get("cena") or {}).get("destaque", "") if c["tipo"] == "classica" else _texto_puro(c.get("manchete"))
        if c["tipo"] == "fato_real":
            dest = c.get("titulo", "")
        if c["tipo"] == "foto_moldura":
            dest = " ".join(c.get("tags") or [])
        sem_ia = c["tipo"] == "fato_real" and (c.get("pessoa", True))   # retrato de pessoa real: nunca inventar com IA
        t_img = "frase"
        if i in idx and not sem_ia:
            t_img = "imagem" if eh_foto(c) else "fundo"
        cenas.append({"tipo": t_img, "narracao": c.get("narracao", ""),
                      "destaque": dest or c.get("titulo", "")})
    ant = tmp / "roteiro.json"
    if ant.exists():
        try:
            velho = json.loads(ant.read_text(encoding="utf-8"))["cenas"]
            for n, v in zip(cenas, velho):
                if v.get("prompt_imagem"):
                    n["prompt_imagem"] = v["prompt_imagem"]
        except (json.JSONDecodeError, KeyError):
            pass
    ant.write_text(json.dumps({"titulo": dados["titulo"], "cenas": cenas}, ensure_ascii=False), encoding="utf-8")
    if cfg.get("fotos_reais", "retratos") != "nunca":
        consultas_reais(dados, [i for i in idx if eh_foto(dados["cenas"][i])], cfg["modelo_ollama"])
    if not ia:
        ant.write_text(json.dumps({"titulo": dados["titulo"], "cenas": cenas}, ensure_ascii=False), encoding="utf-8")
        return
    log(f"Descrevendo {len(idx)} foto(s)...")
    r = subprocess.run([py, str(RAIZ / "prompts.py")], cwd=str(tmp), env=env)
    if r.returncode != 0:
        log("AVISO: nao consegui descrever as fotos; essas cenas viram cenas sem foto.")


def consultas_reais(dados, idx, modelo):
    """Pede a IA uma busca curta por foto REAL de cada cena de foto (lugar, objeto, situacao generica).
    Nas cenas 'fato_real' (perfil): busca do retrato (o proprio nome), do objeto e se e pessoa."""
    import verdade as V
    gen = [i for i in idx if dados["cenas"][i]["tipo"] != "fato_real"]
    fatos = [i for i in idx if dados["cenas"][i]["tipo"] == "fato_real"]
    if gen:
        schema = {"type": "object", "properties": {"buscas": {"type": "array", "items": {"type": "string"}}}, "required": ["buscas"]}
        itens = "\n".join(f"{n + 1}. {dados['cenas'][i].get('narracao', '')}" for n, i in enumerate(gen))
        prompt = (
            "Para cada frase de um video, escreva uma BUSCA CURTA (2 a 5 palavras, em INGLES) para achar uma foto real num banco de imagens livres "
            "(Wikimedia Commons). Descreva algo concreto e fotografavel: um lugar, predio, objeto, cena do dia a dia ou evento. "
            "Se a frase citar um lugar, instituicao ou evento especifico, use o nome dele. NAO use nome de pessoa a menos que a frase cite. "
            f"Devolva exatamente {len(gen)} buscas, na mesma ordem.\n{itens}"
        )
        try:
            r = V.pedir_json(prompt, schema, modelo, temperatura=0.2)
            bs = [re.sub(r"[^\w\s'-]", " ", str(b)).strip() for b in r.get("buscas", [])]
        except Exception:  # noqa: BLE001
            bs = []
        for n, i in enumerate(gen):
            if n < len(bs) and bs[n]:
                dados["cenas"][i]["busca_real"] = bs[n][:60]
    if fatos:
        schema = {"type": "object", "properties": {"itens": {"type": "array", "items": {"type": "object", "properties": {
            "e_pessoa": {"type": "boolean"}, "busca_objeto": {"type": "string"}}, "required": ["e_pessoa", "busca_objeto"]}}}, "required": ["itens"]}
        itens = "\n".join(f"{n + 1}. ASSUNTO: {dados['cenas'][i].get('titulo', '')} | FRASE: {dados['cenas'][i].get('narracao', '')}" for n, i in enumerate(fatos))
        prompt = (
            "Para cada item: e_pessoa = true se o ASSUNTO e uma pessoa (nome de gente). busca_objeto = busca curta em INGLES (1 a 4 palavras) por uma foto de um "
            "OBJETO concreto ligado a frase (ex.: banknote, contract document, oil refinery, ballot box, hospital building); use string vazia se nao houver objeto claro. "
            f"Devolva exatamente {len(fatos)} itens na mesma ordem.\n{itens}"
        )
        try:
            r = V.pedir_json(prompt, schema, modelo, temperatura=0.1)
            its = r.get("itens", [])
        except Exception:  # noqa: BLE001
            its = []
        for n, i in enumerate(fatos):
            c = dados["cenas"][i]
            c["busca_real"] = re.sub(r"[^\w\s'-]", " ", c.get("titulo", "")).strip()[:60]
            if n < len(its):
                c["pessoa"] = bool(its[n].get("e_pessoa"))
                bo = re.sub(r"[^\w\s'-]", " ", str(its[n].get("busca_objeto", ""))).strip()[:50]
                if bo:
                    c["busca_objeto"] = bo


def usar_fotos_reais(proj, dados, cfg, args):
    """Poe fotos reais nas cenas (pasta fotos\\ do projeto primeiro, depois Wikimedia Commons).
    Devolve a lista de registros para conferencia. Nunca derruba o video."""
    import fotos_reais as F
    import roteirista as R
    import showcase_gen as G
    modo = "nunca" if getattr(args, "sem_fotos_reais", False) else cfg.get("fotos_reais", "retratos")
    pub = proj / "public"
    pub.mkdir(exist_ok=True)
    numeradas, livres = F.fotos_da_pasta(proj / "fotos")
    creditos = F.ler_creditos_pasta(proj / "fotos")
    registros = []
    usados = {c.get("titulo_real") for c in dados["cenas"] if c.get("titulo_real")}
    livres = list(livres)
    for i, c in enumerate(dados["cenas"]):
        if c.get("video"):
            continue
        destino = pub / f"img_{i + 1}.jpg"
        if c.get("real") and destino.exists():
            registros.append(c.get("registro_real", ""))
            continue
        arq = numeradas.get(i + 1)
        if arq is not None and (F.arquivo_extra(proj / "fotos", i + 1, "objeto") or F.arquivo_extra(proj / "fotos", i + 1, "recorte")) \
                and c["tipo"] != "fato_real" and c.get("evidencia") is not None:
            fr = R.montar_fato_real({"narracao": c.get("narracao", ""), "evidencia": c.get("evidencia", "")}, dados.get("titulo", ""), random.Random(i))
            if fr:
                for k in ("narracao", "fonte", "evidencia", "fatos", "video", "credito_video"):
                    if c.get(k):
                        fr[k] = c[k]
                dados["cenas"][i] = c = fr
        if arq is None and livres and eh_foto(c):
            arq = livres.pop(0)
        if arq is not None:
            if not eh_foto(c):   # voce escolheu uma foto para esta cena: ela vira cena de foto
                seg = R.cena_segura({"narracao": c.get("narracao", "")}, random.Random(i), True, i, [x["tipo"] for x in dados["cenas"][max(0, i - 1): i + 2]])
                novo = G.sanear_cena(seg, random.Random(i), {"nome": dados.get("estilo", ""), "paleta": [dados.get("paleta", "ouro")]})
                if novo:
                    for k in ("narracao", "fonte", "evidencia", "fatos", "video", "credito_video"):
                        if c.get(k):
                            novo[k] = c[k]
                    dados["cenas"][i] = c = novo
            try:
                _converter_local(arq, destino)
            except Exception as e:  # noqa: BLE001
                log(f"AVISO: nao consegui usar {arq.name}: {e}")
                continue
            cred, aviso = F.credito_da_pasta(arq, creditos)
            if c["tipo"] == "fato_real":
                ob = F.arquivo_extra(proj / "fotos", i + 1, "objeto")
                rc = F.arquivo_extra(proj / "fotos", i + 1, "recorte")
                if ob:
                    _converter_local(ob, pub / f"obj_{i + 1}.jpg")
                    c["objeto"] = f"obj_{i + 1}.jpg"
                if rc:
                    shutil.copyfile(rc, pub / f"rec_{i + 1}.png")
                    c["recorte"] = f"rec_{i + 1}.png"
            c["real"], c["credito"] = True, cred
            c["registro_real"] = f"cena {i + 1}: {arq.name} | {cred or '(sem credito)'} | sua pasta fotos"
            registros.append(c["registro_real"])
            log(f"Cena {i + 1}: foto da sua pasta ({arq.name})" + (f"  AVISO: {aviso}" if aviso else ""))
            continue
        if modo == "nunca" or not eh_foto(c) or not c.get("busca_real") or c["tipo"] == "classica":
            continue
        if modo == "retratos" and not (c["tipo"] == "fato_real" and c.get("pessoa", True)):
            continue   # modo padrao: imagem de IA realista; foto real so para pessoa/instituicao citada
        achados = []
        try:
            sa = bool(cfg.get("permitir_cc_by_sa", False))
            if c["tipo"] == "fato_real" and c.get("pessoa") is not False:
                achados += F.buscar_entidade(c["busca_real"], sa, usados)      # foto principal da Wikipedia da pessoa/lugar
            if not achados or c["tipo"] != "fato_real":
                achados += F.buscar_commons(c["busca_real"], sa, usados=usados)
            if not achados and not (c["tipo"] == "fato_real" and c.get("pessoa")):
                try:
                    achados += F.buscar_openverse(c["busca_real"], sa, usados)   # outros bancos livres (nao para pessoas)
                except Exception:  # noqa: BLE001
                    pass
        except Exception as e:  # noqa: BLE001
            log(f"AVISO: busca de foto real indisponivel agora ({type(e).__name__}).")
            break
        feito = False
        for cand in achados[:4]:
            try:
                if F.baixar_como_jpg(cand["url"], destino):
                    if cfg.get("modelo_visao") and c["tipo"] != "fato_real":
                        if not F.foto_combina(destino, c.get("busca_real", ""), cfg["modelo_visao"]):
                            log(f"   a IA de visao recusou '{cand['titulo'][:50]}' (nao combina); tentando outra...")
                            destino.unlink(missing_ok=True)
                            continue
                    c["real"], c["credito"], c["titulo_real"] = True, cand["credito"], cand["titulo"]
                    c["registro_real"] = f"cena {i + 1}: {cand['titulo']} | {cand['credito']} | {cand['pagina']} | busca: {c['busca_real']}" + (f" | {cand['origem']}" if cand.get("origem") else "")
                    registros.append(c["registro_real"])
                    usados.add(cand["titulo"])
                    log(f"Cena {i + 1}: foto real do Commons -> {cand['titulo']} ({cand['licenca']})")
                    feito = True
                    break
            except Exception as e:  # noqa: BLE001
                log(f"   download falhou ({type(e).__name__}); tentando outra...")
        if feito and c["tipo"] == "fato_real" and c.get("busca_objeto") and not c.get("objeto"):
            try:
                obs = F.buscar_commons(c["busca_objeto"], permitir_sa=bool(cfg.get("permitir_cc_by_sa", False)), usados=usados)
                if not obs:
                    obs = F.buscar_openverse(c["busca_objeto"], bool(cfg.get("permitir_cc_by_sa", False)), usados)
                for ob in obs[:2]:
                    if F.baixar_como_jpg(ob["url"], pub / f"obj_{i + 1}.jpg"):
                        c["objeto"] = f"obj_{i + 1}.jpg"
                        c["credito"] = (c["credito"] + " | " + ob["credito"])[:170]
                        c["registro_real"] += f" || objeto: {ob['titulo']} | {ob['credito']} | {ob['pagina']}"
                        usados.add(ob["titulo"])
                        log(f"   objeto da cena {i + 1}: {ob['titulo']}")
                        break
            except Exception:  # noqa: BLE001
                pass
        if not feito:
            log(f"Cena {i + 1}: nenhuma foto real segura para '{c['busca_real']}'" + ("; vou gerar com IA." if modo != "so_reais" else "."))
    return registros


def _converter_local(arq, destino):
    ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ff:
        shutil.copyfile(arq, destino)
        return
    subprocess.run([ff, "-y", "-v", "error", "-i", str(arq), "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", str(destino)], check=True)


def fotos_gerar(proj, dados, cfg, env, py, args=None, ia=True):
    """Passo 2 das fotos (Cloudflare). Nunca derruba o video: sem foto, a cena vira outra cena sem foto.
    Depois de gerar, a cor de destaque de cada cena de foto sai da propria imagem."""
    import showcase_gen as G
    import roteirista as R
    import cores
    tmp = proj / "_img"
    (proj / "public").mkdir(exist_ok=True)
    proc_visao = iniciar_ollama(cfg) if (args is not None and cfg.get("modelo_visao")) else None
    try:
        registros = usar_fotos_reais(proj, dados, cfg, args) if args is not None else []
    finally:
        if proc_visao is not None:
            parar_ollama(cfg, proc_visao)
    if ia and (tmp / "roteiro.json").exists():
        (tmp / "public").mkdir(parents=True, exist_ok=True)
        for f in (proj / "public").glob("img_*.jpg"):
            shutil.copyfile(f, tmp / "public" / f.name)
        log("Gerando as fotos com IA (Cloudflare) nas cenas que ficaram sem foto real...")
        r = subprocess.run([py, str(RAIZ / "imagens.py")], cwd=str(tmp), env=env)
        if r.returncode != 0:
            log("AVISO: as fotos nao foram geradas (limite diario?). As cenas com foto viram cenas sem foto.")
        for f in (tmp / "public").glob("img_*.jpg"):
            shutil.copyfile(f, proj / "public" / f.name)
    (proj / "public").mkdir(exist_ok=True)
    trocadas = 0
    for i, c in enumerate(dados["cenas"]):
        if c.get("fundo_foto") and not eh_foto(c):
            arq = proj / "public" / f"img_{i + 1}.jpg"
            if arq.exists() and cinema.qualidade_ok(arq):
                if cfg.get("grade_cinema", True) and not c.get("real"):
                    cinema.tratar(arq)
                if c["tipo"] == "classica":
                    c["cena"]["imagem"] = arq.name
                else:
                    c["foto"] = arq.name
                    c["acento"] = cores.cor_dominante(arq)
            else:
                c.pop("fundo_foto", None)   # sem imagem: a cena segue animada normalmente
            continue
        if not eh_foto(c):
            continue
        arq = proj / "public" / f"img_{i + 1}.jpg"
        ok = arq.exists() and cinema.qualidade_ok(arq)
        if ok and cfg.get("grade_cinema", True) and not c.get("real"):
            cinema.tratar(arq)
        if c["tipo"] == "classica":
            if ok:
                c["cena"]["imagem"] = arq.name
            continue
        if ok:
            c["foto"] = arq.name
            c["acento"] = cores.cor_dominante(arq)
            if c["tipo"] == "fato_real" and c.get("pessoa") and not c.get("recorte") and cfg.get("recorte", "auto") != "nunca":
                import fotos_reais as _F
                if _F.remover_fundo(arq, proj / "public" / f"rec_{i + 1}.png"):
                    c["recorte"] = f"rec_{i + 1}.png"
                    log(f"Cena {i + 1}: retrato recortado (sem fundo).")
            if not c.get("real") and cfg.get("rotular_ia", True):
                c["credito"] = "Imagem ilustrativa (gerada por IA)"
            continue
        evitar = [x["tipo"] for x in dados["cenas"][max(0, i - 2): i + 3]]
        seg = R.cena_segura({"narracao": c.get("narracao", "")}, random.Random(i), False, i, evitar)
        novo = G.sanear_cena(seg, random.Random(i), {"nome": dados.get("estilo", ""), "paleta": [dados.get("paleta", "ouro")]})
        if novo:
            for k in ("narracao", "fonte", "evidencia", "fatos", "video", "credito_video"):
                if c.get(k):
                    novo[k] = c[k]
            dados["cenas"][i] = novo
            trocadas += 1
    G.sem_foto_faltando(dados, proj / "public")
    if trocadas:
        log(f"{trocadas} cena(s) sem foto viraram cenas animadas sem imagem.")
    (proj / "roteiro.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    reais = [c for c in dados["cenas"] if c.get("real")]
    linhas = ["FOTOS REAIS USADAS (confira se cada uma combina com a cena):"] + [c.get("registro_real", "") for c in reais]
    ia_n = sum(1 for c in dados["cenas"] if c.get("foto") and not c.get("real"))
    if ia_n:
        linhas.append(f"{ia_n} foto(s) gerada(s) por IA, (sem etiqueta na tela; veja NOME_CREDITOS.txt).")
    (proj / "creditos_fotos.txt").write_text("\n".join(linhas), encoding="utf-8")
    ia_total = sum(1 for c in dados["cenas"] if (c.get("foto") and not c.get("real")) or c.get("fundo_foto") or (c.get("cena") or {}).get("imagem"))
    if ia_total:
        lp = proj / "legenda_post.txt"
        antigo = lp.read_text(encoding="utf-8") if lp.exists() else ""
        if "geradas por IA" not in antigo:
            lp.write_text(antigo.rstrip() + "\nImagens ilustrativas geradas por IA.\n", encoding="utf-8")
    cr = sorted({c["credito"] for c in reais if c.get("credito")})
    if cr:
        lp = proj / "legenda_post.txt"
        antigo = lp.read_text(encoding="utf-8") if lp.exists() else ""
        antigo = antigo.split("\nCréditos das fotos:")[0]
        lp.write_text(antigo.rstrip() + "\nCréditos das fotos: " + "; ".join(cr) + "\n", encoding="utf-8")
    if reais and getattr(args, "sem_aprovar", False) is False and (dados.get("modo") == "serio"):
        print("\nTEMA SERIO - fotos reais escolhidas automaticamente:")
        for c in reais:
            print("  -", c.get("registro_real", ""))
        if SEM_PERGUNTAS:
            log("Modo sem perguntas: segui adiante. Confira as fotos em CONFERIR_ANTES_DE_POSTAR.txt.")
            r = "s"
        else:
            try:
                r = input("As fotos combinam com o assunto? S = continuar | N = trocar por imagens ilustrativas de IA: ").strip().lower()
            except EOFError:
                r = "s"
        if r not in ("s", "sim", "y"):
            for i, c in enumerate(dados["cenas"]):
                if c.get("real") and "Commons" in c.get("credito", ""):
                    (proj / "public" / f"img_{i + 1}.jpg").unlink(missing_ok=True)
                    for k in ("real", "credito", "foto", "registro_real", "titulo_real"):
                        c.pop(k, None)
            log("Fotos do Commons removidas. Rode de novo para gerar as imagens de IA (ou coloque suas fotos em fotos\\).")
            (proj / "roteiro.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
            sys.exit(3)


def fatos_para_roteirista(base):
    """Converte a base de pesquisa (verdade.py) para o formato do roteirista. Numero que so aparece em UMA
    fonte nao oficial fica de fora (evita dado errado)."""
    out = []
    for f in (base or {}).get("fatos", []):
        if not (f.get("tipo") == "usuario" or f.get("oficial") or f.get("corroborado") or not re.search(r"\d", f["texto"])):
            continue
        out.append({"id": f["id"], "texto": f["texto"], "fonte": f.get("fonte", ""), "data": f.get("data", ""), "tipo": f.get("tipo", "")})
    return out


def escrever_roteiro_showcase(proj, tema, args, cfg):
    import showcase_gen as G
    import verdade as V
    import roteirista as R
    base_dir = Path(cfg["pasta_dados"]) if cfg.get("pasta_dados") else RAIZ
    memoria_arq = base_dir / "memoria.json"
    mem = G.ler_memoria(memoria_arq)
    semente = args.semente if args.semente is not None else random.randrange(10**6)
    rnd = random.Random(semente)
    estilo = G.escolher_estilo(args.estilo, rnd, evitar=[m.get("estilo") for m in mem[-2:]])
    log(f"Estilo sorteado: {estilo['nome']} ({estilo.get('descricao', '')})")
    fatos_usuario = (proj / "fatos.txt").read_text(encoding="utf-8") if (proj / "fatos.txt").exists() else ""
    modelo = cfg["modelo_ollama"]
    serio_auto, _ = R.classificar(tema)
    serio = True if getattr(args, "serio", False) else (False if getattr(args, "normal", False) else serio_auto)
    sens = serio or V.eh_sensivel(tema)

    # ---- pesquisa com fontes (cache em pesquisa.json; --repesquisar refaz) ----
    base = None
    if cfg.get("pesquisar", True) and not getattr(args, "sem_pesquisa", False):
        pj = proj / "pesquisa.json"
        if pj.exists() and not getattr(args, "repesquisar", False):
            base = json.loads(pj.read_text(encoding="utf-8"))
            log(f"Pesquisa de {base.get('data', '?')} ja existe; reaproveitando. (--repesquisar para atualizar)")
        else:
            base = V.montar_base(tema, modelo)
            pj.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        base = {"tema": tema, "data": time.strftime("%Y-%m-%d"), "sensivel": sens, "fatos": [], "fontes": []}
    if fatos_usuario.strip():
        base = V.juntar_fatos_usuario(base, fatos_usuario)
    fatos = fatos_para_roteirista(base)
    log(f"Fatos aproveitados: {len(fatos)} | tema serio: {'sim' if sens else 'nao'}")
    if sens and len(fatos) < 3:
        log("")
        log("PAREI DE PROPOSITO: este tema e serio (politica, saude, crime, dinheiro...) e nao encontrei fontes suficientes")
        log("na internet agora. Para evitar informacao errada, o video NAO foi criado.")
        log("O que fazer: confira sua conexao e tente de novo, ou escreva fatos conferidos em fatos.txt (uma frase por linha).")
        sys.exit(2)
    if len(fatos) < 3:
        log("AVISO: poucas fontes; o roteiro usara apenas dicas gerais, sem numeros nem nomes.")
        fatos = []

    max_fotos = int(cfg.get("max_fotos", 6)) if (usar_imagens(args, cfg) or cfg.get("fotos_reais", "retratos") != "nunca") else 0
    dados = None
    for tentativa in range(3):
        try:
            dados = R.gerar(tema, fatos, estilo, modelo, rnd, modelo_juiz=(cfg.get("modelo_juiz") or None), max_fotos=max_fotos, max_imagens=(int(cfg.get("imagens_por_video", 11)) if usar_imagens(args, cfg) else 0), n_pontos=int(cfg.get("n_pontos", 11)), serio=sens, marca=cfg.get("marca", ""), log=log)
            break
        except (RuntimeError, ValueError) as e:
            log(f"  roteiro incompleto ({e}); tentando de novo...")
            dados = None
    if dados is None:
        log("ERRO: nao consegui um roteiro valido com apoio nas fontes. Tente de novo ou use --repesquisar.")
        sys.exit(1)
    dados["data_pesquisa"] = base.get("data", "")
    log("Revisando ortografia dos textos...")
    G.revisar_dados(dados, modelo)
    for cn in dados["cenas"]:   # as linhas do perfil sempre vem da narracao ja revisada
        if cn["tipo"] == "fato_real":
            cn["linhas"] = R.quebrar_linhas(cn.get("narracao", "")) or cn["linhas"]
    G.gravar_memoria(memoria_arq, dados)
    (proj / "roteiro.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    # arquivo legivel para conferir + legenda do post com as fontes
    linhas = [f"TEMA: {tema}", f"DATA DA PESQUISA: {base.get('data', '')}", f"MODO: {dados.get('modo')}", ""]
    for k, c in enumerate(dados["cenas"], 1):
        linhas.append(f"{k:02d} [{c['tipo'] if c['tipo'] != 'classica' else 'c:' + c['cena']['tipo']}] {c.get('narracao', '')}")
        if c.get("evidencia"):
            linhas.append(f"     evidencia: \"{c['evidencia']}\"  fatos: {','.join(c.get('fatos', []))}")
    usados = dados.get("fatos_usados", [])
    if usados:
        linhas += ["", "FATOS USADOS:"] + [f"[{f['id']}] {f['texto']} (Fonte: {f['fonte']} {f.get('data', '')})" for f in usados]
    (proj / "roteiro_para_conferir.txt").write_text("\n".join(linhas), encoding="utf-8")
    nomes = sorted({f["fonte"] for f in usados if f.get("fonte")})
    legenda = [dados["titulo"], ""]
    if dados.get("aviso"):
        legenda.append(dados["aviso"])
    if nomes:
        legenda.append("Fontes: " + ", ".join(nomes) + f" (consultadas em {base.get('data', '')}).")
    (proj / "legenda_post.txt").write_text("\n".join(legenda), encoding="utf-8")
    log("Cenas: " + " > ".join(c["tipo"] if c["tipo"] != "classica" else "c:" + c["cena"]["tipo"] for c in dados["cenas"]))
    log(f"Fotos planejadas: {sum(1 for c in dados['cenas'] if eh_foto(c))}")
    log(f"Para conferir: {proj / 'roteiro_para_conferir.txt'}")

    precisa = sens and not getattr(args, "sem_aprovar", False)
    if sens or getattr(args, "revisar", False):
        reais_ = [c for c in dados["cenas"] if c.get("credito")]
        txt = ["CONFERIR ANTES DE POSTAR", "Tema: " + str(dados.get("titulo", "")), "",
               "O que e falado, com a fonte de cada frase:"]
        for k, c in enumerate(dados["cenas"], 1):
            txt.append(f"  {k:02d}. {c.get('narracao', '')}   [{c.get('fonte', '-')}]")
        if reais_:
            txt += ["", "Fotos reais usadas (credito/licenca):"] + [f"  - {c['credito']}" for c in reais_]
        txt += ["", "Se algo estiver errado: corrija fatos.txt e rode de novo com --novo, ou nao publique."]
        (proj / "CONFERIR_ANTES_DE_POSTAR.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    if SEM_PERGUNTAS and (precisa or getattr(args, "revisar", False)):
        log("Modo sem perguntas: nao vou esperar aprovacao. O que e falado esta em CONFERIR_ANTES_DE_POSTAR.txt.")
    elif getattr(args, "revisar", False) or precisa:
        print()
        if precisa:
            print("TEMA SERIO - confira o que sera falado, com a fonte de cada frase:")
            for k, c in enumerate(dados["cenas"], 1):
                print(f"  {k:02d}. {c.get('narracao', '')}   [{c.get('fonte', '-')}]")
            print()
        try:
            r = input("Esta tudo correto? Digite S para continuar ou N para cancelar: ").strip().lower()
        except EOFError:
            r = "s"
        if r not in ("s", "sim", "y"):
            log("Cancelado. Edite roteiro.json/fatos.txt se quiser e rode de novo.")
            sys.exit(3)
    return dados


def etapa_narracao(proj, cfg, env, py, motor, refazer):
    assinatura = None
    if motor == 'mascote':
        import hashlib
        from mascote import normalizar_perfil
        from tts_mascote import VERSAO_VOZ
        from voz_referencia import identidade_referencia
        cfg['mascote_voz'] = normalizar_perfil(cfg.get('mascote_voz', 'referencia'))
        assinatura = hashlib.sha256(((proj / 'roteiro.json').read_text(encoding='utf-8') + cfg['mascote_voz'] + VERSAO_VOZ + identidade_referencia()).encode()).hexdigest()
        marcador = proj / '.voz_mascote'
        refazer = refazer or not marcador.exists() or marcador.read_text(encoding='utf-8') != assinatura
    if refazer and motor != 'mascote':
        for arq in ("narracao.wav", "tempos_cenas.json", "palavras.json"):
            (proj / arq).unlink(missing_ok=True)
    if not refazer and (proj / "narracao.wav").exists() and (proj / "tempos_cenas.json").exists():
        log("Ja existe, pulando. (use --refazer-voz para trocar a voz)")
        return False
    if motor == 'mascote':
        env_mascote = dict(env, MASCOTE_VOZ=cfg.get('mascote_voz', 'referencia'))
        from voz_referencia import python_voz
        rodar([python_voz(), str(RAIZ / 'tts_mascote.py')], proj, env_mascote, 'voz do personagem')
    elif motor == "chatterbox":
        py_voz = cfg["python_voz"] or py
        if not Path(py_voz).exists() and py_voz != py:
            log(f"ERRO: python_voz nao encontrado: {py_voz}")
            log("Veja o LEIAME da voz ou use motor_voz = kokoro no config.json.")
            sys.exit(1)
        env_voz = dict(env)
        ref = Path(cfg["voz_referencia"])
        ref = ref if ref.is_absolute() else RAIZ / ref
        if ref.exists():
            env_voz["VOZ_REFERENCIA"] = str(ref)
        rodar([py_voz, str(RAIZ / "tts_chatterbox.py")], proj, env_voz, "narracao (chatterbox)")
    else:
        rodar([py, str(RAIZ / "tts_kokoro.py")], proj, env, "narracao")
    if assinatura:
        (proj / '.voz_mascote').write_text(assinatura, encoding='utf-8')
    return True


def produzir_showcase(tema, args, cfg, env):
    inicio = time.time()
    nome = os.environ.get("CRIAR_NOME_PROJETO") or slug(tema)   # o painel escolhe o nome da pasta (tema com mais de 50 letras)
    base = Path(cfg["pasta_dados"]) if cfg.get("pasta_dados") else RAIZ
    proj = base / "projetos" / nome
    if args.novo and proj.exists():
        proj = base / "projetos" / f"{nome}-{time.strftime('%Y%m%d-%H%M%S')}"
        nome = proj.name
    (proj / "public").mkdir(parents=True, exist_ok=True)
    (base / "saidas").mkdir(parents=True, exist_ok=True)
    saida = base / "saidas" / f"{nome}.mp4"
    log(f"Tema:    {tema}")
    log(f"Projeto: {proj}")
    if args.fatos:
        shutil.copyfile(args.fatos, proj / "fatos.txt")
    py = sys.executable
    TOTAL = 5

    titulo_etapa(1, TOTAL, "Roteiro, narracao e cenas (Ollama)")
    if (proj / "roteiro.json").exists():
        log("Ja existe, pulando. (apague a pasta do projeto para refazer o roteiro)")
        dados = json.loads((proj / "roteiro.json").read_text(encoding="utf-8"))
        if not dados.get("narrado"):
            log("ERRO: esta pasta tem um roteiro do modo antigo. Use --novo ou apague a pasta.")
            sys.exit(1)
    elif (proj / 'falas_mascote.txt').exists():
        from mascote import roteiro_direto
        dados = roteiro_direto(proj, tema)
        (proj / 'roteiro.json').write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
        log('Usando suas falas exatas, uma cena por linha. Sem gerar roteiro com IA.')
    else:
        proc = iniciar_ollama(cfg)
        try:
            log("Escrevendo o roteiro... (alguns minutos)")
            dados = escrever_roteiro_showcase(proj, tema, args, cfg)
            from motion_editor import preparar_midias
            preparar_midias(proj, dados)
            ia = usar_imagens(args, cfg)
            if ia or cfg.get("fotos_reais", "retratos") != "nunca":
                fotos_prompts(proj, dados, cfg, env, py, ia)
        finally:
            parar_ollama(cfg, proc)

    (proj / "public").mkdir(exist_ok=True)
    tem_video_mascote = False
    if (proj / 'mascote.json').exists():
        mc_fundo = json.loads((proj / 'mascote.json').read_text(encoding='utf-8'))
        tem_video_mascote = mc_fundo.get('ativo') and mc_fundo.get('fundo') == 'video'
    if not tem_video_mascote:
        from motion_editor import preparar_midias
        preparar_midias(proj, dados)
        fotos_gerar(proj, dados, cfg, env, py, args, usar_imagens(args, cfg))

    motor = args.voz or cfg["motor_voz"]
    if (proj / 'mascote.json').exists():
        mc = json.loads((proj / 'mascote.json').read_text(encoding='utf-8'))
        if mc.get('ativo'):
            motor = 'mascote'
            from mascote import normalizar_perfil
            cfg['mascote_voz'] = normalizar_perfil(mc.get('voz', 'referencia'))
            cfg['ritmo_fala'] = 1.0
    titulo_etapa(2, TOTAL, f"Narracao ({motor})")
    refeita = etapa_narracao(proj, cfg, env, py, motor, args.refazer_voz)
    if refeita or args.refazer_voz or not (proj / ".tempos_ok").exists():
        if motor != 'mascote':
            if cfg.get('edicao','motion') == 'anterior':
                desacelerar(proj, float(cfg.get("ritmo_fala", 0.94)))
                ajustar_minimos(proj, dados, float(cfg.get("respiro", 0.3)))
            if refeita or args.refazer_voz:
                (proj / "palavras.json").unlink(missing_ok=True)
        (proj / ".tempos_ok").write_text("ok")

    titulo_etapa(3, TOTAL, "Legendas palavra por palavra (Whisper)")
    if (proj / "palavras.json").exists():
        log("Ja existe, pulando.")
    else:
        r = subprocess.run([py, str(RAIZ / "align.py")], cwd=str(proj), env=env)
        if r.returncode != 0 or not (proj / "palavras.json").exists():
            log("AVISO: o Whisper nao funcionou; usando legendas por estimativa de tempo.")
            estimar_palavras(proj)

    titulo_etapa(4, TOTAL, "Montando os arquivos do video")
    for arq in ("tempos_cenas.json", "palavras.json"):
        shutil.copyfile(proj / arq, proj / "public" / arq)
    if motor == 'mascote':
        shutil.copyfile(proj / 'narracao.wav', proj / 'public' / 'narracao.wav')
        log('Narração gerada com a voz de referência, sem efeitos de pitch ou velocidade.')
    elif cfg.get("polir_voz", True) and polir_voz(proj / "narracao.wav", proj / "public" / "narracao.wav"):
        log("Voz com acabamento de estudio (corte de grave, compressao, presenca).")
    elif not (proj / "public" / "narracao.wav").exists() or not cfg.get("polir_voz", True):
        shutil.copyfile(proj / "narracao.wav", proj / "public" / "narracao.wav")
    validar_roteiro(proj, dados)
    auditar_texto_tela(proj, dados)
    validar_roteiro(proj, dados)
    from mascote import preparar as preparar_mascote
    preparar_mascote(proj, dados, RAIZ)
    from motion_editor import dirigir,assinatura as assinatura_edicao
    modo_edicao=cfg.get('edicao','motion') if not tem_video_mascote else 'anterior'
    from motion_variacao import preparar_direcao, registrar_sucesso
    contexto_direcao=preparar_direcao(dados,proj,base,cfg.get('motion_pedido','')) if modo_edicao=='motion' else None
    if contexto_direcao:
        contexto_direcao={**contexto_direcao,
                          'intensidade_motion':cfg.get('intensidade_motion','equilibrado'),
                          'variedade_motion':cfg.get('variedade_motion','criativa')}
    dirigir(dados,json.loads((proj/'tempos_cenas.json').read_text(encoding='utf-8')),json.loads((proj/'palavras.json').read_text(encoding='utf-8')),modo_edicao,contexto=contexto_direcao)
    nova_edicao=assinatura_edicao(dados,proj,modo_edicao)
    marcador_edicao=proj/'.edicao_motion'
    edicao_refeita=not marcador_edicao.exists() or marcador_edicao.read_text(encoding='utf-8')!=nova_edicao
    (proj/'PLANO_MOTION.json').write_text(json.dumps([{'cena':i+1,'visual':c.get('motion'),'video':c.get('video')} for i,c in enumerate(dados['cenas'])],ensure_ascii=False,indent=2),encoding='utf-8')
    dados["mostrar_fontes"] = bool(cfg.get("show_source_labels", False))   # padrao: sem etiquetas de fonte/foto na imagem
    (proj / "public" / "showcase.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    preparar_audio(proj, cfg, env, py, nome, args.sem_musica)
    af = proj / "public" / "audio.json"
    a = json.loads(af.read_text(encoding="utf-8"))
    a["narracao"] = True
    af.write_text(json.dumps(a), encoding="utf-8")
    log("Arquivos prontos.")

    titulo_etapa(5, TOTAL, "Edicao Showcase e renderizacao (Remotion) - esta etapa demora")
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        log("ERRO: o 'npx' nao foi encontrado. Instale o Node.js.")
        sys.exit(1)
    if saida.exists() and not args.rerender and not refeita and not edicao_refeita:
        log("O video ja existe. Use --rerender para renderizar de novo.")
        log(f"Video: {saida}")
        return saida
    alvo_render = saida.with_name(saida.stem + '.novo.mp4') if saida.exists() else saida
    rodar([npx, "remotion", "render", "src/index.ts", "Showcase", str(alvo_render),
           f"--public-dir={proj / 'public'}", f"--concurrency={cfg['concorrencia']}"], RAIZ, env, "renderizacao")
    if alvo_render != saida:
        alvo_render.replace(saida)
    marcador_edicao.write_text(nova_edicao,encoding='utf-8')
    if modo_edicao=='motion' and not registrar_sucesso(dados,proj,base):
        log('AVISO: vídeo exportado; não foi possível atualizar a memória visual.')
    if cfg.get("normalizar_volume", True):
        normalizar_volume(saida, cfg.get("lufs", -14))
    problemas_qa = qa_video(saida)
    try:   # inspetor de qualidade: medicoes objetivas + correcao segura so do audio (ate 3 rodadas) + relatorio
        import inspetor
        esp = None
        try:
            tp_ = json.loads((proj / "tempos_cenas.json").read_text(encoding="utf-8"))
            esp = float(tp_[-1]["fim"]) + 0.8
        except (OSError, ValueError, KeyError, IndexError):
            pass
        rq = inspetor.inspecionar_e_refinar(saida, esp, rodadas=int(cfg.get("rodadas_refino", 3)), lufs=cfg.get("lufs", -14), log=log)
        arq_q = inspetor.escrever(rq, proj, saida.stem)
        shutil.copyfile(arq_q, saida.with_name(saida.stem + "_QUALIDADE.txt"))
        graves_q = [x["evidencia"] for x in rq["achados"] if x["gravidade"] == "grave"]
        problemas_qa = list(problemas_qa or [])
        problemas_qa += [g for g in graves_q if not any(g[:12] in p_ for p_ in problemas_qa)]
        log(f"Relatorio de qualidade: {saida.stem}_QUALIDADE.txt ({len(rq['achados'])} problema(s) restante(s))")
    except Exception as e:  # noqa: BLE001 - o inspetor nunca derruba um video pronto
        log(f"AVISO: inspetor de qualidade falhou ({type(e).__name__}: {e}). O video esta ok.")
    try:
        relatorio_final(proj, dados, saida, problemas_qa)
        pacote_postagem(proj, dados, saida)
    except Exception as e:  # noqa: BLE001 - relatorio nunca pode derrubar um video pronto
        log(f"AVISO: nao consegui montar o relatorio ({type(e).__name__}: {e}). O video esta ok.")
    if cfg.get("gerar_capa", True):
        gerar_capa(proj, saida, npx, env)
    try:   # creditos e fontes ficam FORA da imagem, numa lista separada (atribuicao de licencas preservada)
        L_ = ["CREDITOS E FONTES (nao aparecem no video; use na legenda/comentario fixado quando a licenca exigir)", ""]
        for k_, c_ in enumerate(dados["cenas"], 1):
            partes_ = [x_ for x_ in (c_.get("fonte"), c_.get("credito")) if x_]
            if partes_:
                L_.append(f"Cena {k_:02d}: " + " | ".join(partes_))
        for c_ in dados["cenas"]:
            if c_.get("registro_real"):
                L_.append("  registro: " + c_["registro_real"])
        if any(c_.get("foto") and not c_.get("real") for c_ in dados["cenas"]):
            L_ += ["", "Imagens geradas por IA: ao publicar, ative o rotulo 'conteudo gerado por IA' do TikTok."]
        saida.with_name(saida.stem + "_CREDITOS.txt").write_text("\n".join(L_) + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log(f"AVISO: nao consegui gravar a lista de creditos ({type(e).__name__}).")
    conf = proj / "CONFERIR_ANTES_DE_POSTAR.txt"
    if conf.exists():
        shutil.copyfile(conf, saida.with_name(saida.stem + "_CONFERIR.txt"))
        log(f"Conferir antes de postar: {saida.with_name(saida.stem + '_CONFERIR.txt')}")
    log("")
    log("=" * 60)
    log(f" PRONTO em {(time.time() - inicio) / 60:.1f} minutos")
    log(f" Video: {saida}")
    log("=" * 60)
    return saida


def verificar():
    """Confere se tudo que o programa precisa esta no lugar e diz o que falta."""
    obrigatorios = [
        "criar.py", "criar.bat", "painel.py", "painel.bat", "showcase_gen.py", "verdade.py", "roteirista.py", "cores.py", "fotos_reais.py", "estilo_imagem.py", "cinema.py", "sfx.py", "referencias.py", "inspetor.py", "package.json", "tsconfig.json",
        "mascote.py", "tts_mascote.py", "mascote_panel.html", "assets/painel-mascote.js", "assets/painel-mascote.css",
        "src/Mascote.tsx", "src/index.ts", "src/Root.tsx", "src/Video.tsx", "src/Showcase.tsx", "src/Efeitos.tsx",
        "src/CenasNovas.tsx", "src/CenasDados.tsx", "src/CenasExtras.tsx", "src/CenasEstilo.tsx",
        "src/showcase/Base.tsx", "src/showcase/Guarda.tsx", "src/showcase/Documentario.tsx", "src/showcase/CenasFoto.tsx", "src/showcase/CenaFato.tsx", "src/showcase/CenasVar.tsx", "src/showcase/Objetos.tsx", "src/showcase/Cenas.tsx", "src/showcase/Cenas2.tsx",
        "estilos/varejo_ouro.json", "prompts.py", "imagens.py", "tts_chatterbox.py",
    ]
    faltam = [f for f in obrigatorios if not (RAIZ / f).exists()]
    print("\n=== VERIFICACAO ===")
    print(f"Pasta: {RAIZ}")
    if faltam:
        print("\nFALTAM ESTES ARQUIVOS (copie do pacote para o mesmo lugar):")
        for f in faltam:
            print("   X", f.replace("/", "\\"))
    else:
        print("[ok] todos os arquivos do programa estao no lugar")
    for nome, ok, dica in [
        ("node_modules (Remotion instalado)", (RAIZ / "node_modules").exists(), "rode:  npm install   nesta pasta"),
        ("npx (Node.js)", bool(shutil.which("npx") or shutil.which("npx.cmd")), "instale o Node.js"),
        ("ffmpeg", bool(shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")), "instale o ffmpeg e coloque no PATH"),
        ("ollama", bool(shutil.which("ollama") or shutil.which("ollama.exe")), "instale o Ollama"),
        ("config.json", CONFIG.exists(), "rode o criar.bat uma vez: ele pergunta as chaves e cria o arquivo"),
    ]:
        print(("[ok] " if ok else "[FALTA] ") + nome + ("" if ok else f"  -> {dica}"))
    try:
        cfg = dict(PADRAO)
        if CONFIG.exists():
            cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
        if cfg["motor_voz"] == "chatterbox":
            py_voz = cfg["python_voz"]
            print(("[ok] " if py_voz and Path(py_voz).exists() else "[FALTA] ") + f"python_voz = {py_voz or '(vazio)'}")
            ref = Path(cfg["voz_referencia"])
            ref = ref if ref.is_absolute() else RAIZ / ref
            print(("[ok] " if ref.exists() else "[aviso] ") + f"voz de referencia: {ref}")
        else:
            print(("[ok] " if (RAIZ / "tts_kokoro.py").exists() else "[FALTA] ") + "tts_kokoro.py (voz Kokoro)")
    except json.JSONDecodeError:
        print("[FALTA] config.json com erro de formato (apague e rode de novo)")
    try:
        import numpy, scipy, soundfile, requests  # noqa: F401
        print("[ok] bibliotecas Python (numpy, scipy, soundfile, requests)")
    except ImportError as e:
        print(f"[FALTA] biblioteca Python: {e.name}  -> pip install numpy scipy soundfile requests")
    print("")


def main():
    ap = argparse.ArgumentParser(description="Cria um video completo a partir de um tema.")
    ap.add_argument("tema", nargs="?", help="tema ou briefing do video (entre aspas)")
    ap.add_argument("--lote", help="arquivo .txt com um tema por linha (faz todos)")
    ap.add_argument("--estilo", default="auto", help="estilo da pasta estilos (padrao: sorteia)")
    ap.add_argument("--semente", type=int, help="repete o mesmo sorteio visual")
    ap.add_argument("--mistura", type=float, help="0 = so Showcase, 0.5 = metade cenas classicas (padrao: o estilo decide)")
    ap.add_argument("--sem-pesquisa", action="store_true", help="nao pesquisa na internet (so para temas atemporais)")
    ap.add_argument("--repesquisar", action="store_true", help="refaz a pesquisa na internet (dados atualizados)")
    ap.add_argument("--serio", action="store_true", help="forca o modo serio (verificacao maxima + confirmacao)")
    ap.add_argument("--normal", action="store_true", help="forca o modo normal mesmo que o tema pareca serio")
    ap.add_argument("--sem-aprovar", action="store_true", help="nao pede confirmacao em tema serio (uso em lote)")
    ap.add_argument("--sem-fotos-reais", action="store_true", help="nao busca fotos reais (so IA e a sua pasta fotos)")
    ap.add_argument("--modelo", help="usa outro modelo do Ollama so desta vez (ex.: --modelo gemma4:12b)")
    ap.add_argument("--revisar", action="store_true", help="pausa para voce ler o roteiro antes de gerar voz e video")
    ap.add_argument("--so-showcase", action="store_true", help="so cenas Showcase (sem cenas classicas)")
    ap.add_argument("--sem-imagens", action="store_true", help="sem fotos de IA (nao usa a Cloudflare)")
    ap.add_argument("--verificar", action="store_true", help="confere se todos os arquivos necessarios estao no lugar")
    ap.add_argument("--classico", action="store_true", help="usa o modo antigo (documentario com imagens)")
    ap.add_argument("--fatos", help="arquivo .txt com fatos e numeros reais para o roteiro")
    ap.add_argument("--novo", action="store_true", help="cria uma pasta nova em vez de continuar a anterior")
    ap.add_argument("--voz", choices=["kokoro", "chatterbox"], help="escolhe o motor de voz so desta vez")
    ap.add_argument("--refazer-voz", action="store_true", help="apaga narracao e legendas deste projeto e gera de novo")
    ap.add_argument("--sem-musica", action="store_true", help="renderiza sem musica de fundo")
    ap.add_argument("--rerender", action="store_true", help="renderiza o video de novo mesmo que o MP4 ja exista (use depois de mudar o visual)")
    args = ap.parse_args()
    if args.verificar:
        verificar()
        return

    inicio = time.time()
    cfg = carregar_config()
    if args.modelo:
        cfg["modelo_ollama"] = args.modelo
    env = env_base(cfg)

    if not args.classico:
        temas = []
        if args.lote:
            temas = [l.strip() for l in Path(args.lote).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
        elif args.tema:
            temas = [args.tema]
        else:
            ap.print_help()
            sys.exit(1)
        prontos = []
        for k, tema in enumerate(temas, 1):
            if len(temas) > 1:
                log(f"\n######## VIDEO {k} de {len(temas)} ########")
            prontos.append(produzir_showcase(tema, args, cfg, env))
        if len(prontos) > 1:
            log("\nVideos prontos:")
            for p in prontos:
                log(f"  {p}")
        if WINDOWS and prontos:
            try:
                os.startfile(str(prontos[-1].parent))
            except OSError:
                pass
        return
    if not args.tema:
        ap.print_help()
        sys.exit(1)

    nome = slug(args.tema)
    base = Path(cfg["pasta_dados"]) if cfg.get("pasta_dados") else RAIZ
    proj = base / "projetos" / nome
    if args.novo and proj.exists():
        proj = base / "projetos" / f"{nome}-{time.strftime('%Y%m%d-%H%M%S')}"
        nome = proj.name
    (proj / "public").mkdir(parents=True, exist_ok=True)
    (base / "saidas").mkdir(parents=True, exist_ok=True)
    saida = base / "saidas" / f"{nome}.mp4"

    log(f"Tema:    {args.tema}")
    log(f"Projeto: {proj}")

    usa_fatos = False
    if args.fatos:
        shutil.copyfile(args.fatos, proj / "fatos.txt")
        usa_fatos = True
    elif (proj / "fatos.txt").exists():
        usa_fatos = True

    py = sys.executable
    TOTAL = 6

    # 1 e 2 -- roteiro e prompts de imagem (precisam do Ollama)
    titulo_etapa(1, TOTAL, "Roteiro e descricoes das imagens (Ollama)")
    precisa_roteiro = not (proj / "roteiro.json").exists()
    precisa_prompts = not roteiro_completo(proj)
    if precisa_roteiro or precisa_prompts:
        proc = iniciar_ollama(cfg)
        try:
            if precisa_roteiro:
                log("Escrevendo o roteiro... (alguns minutos)")
                cmd = [py, str(RAIZ / "script.py"), args.tema] + (["fatos"] if usa_fatos else [])
                rodar(cmd, proj, env, "roteiro")
            if not roteiro_completo(proj):
                log("Criando as descricoes das imagens... (alguns minutos)")
                rodar([py, str(RAIZ / "prompts.py")], proj, env, "prompts das imagens")
        finally:
            parar_ollama(cfg, proc)
    else:
        log("Ja existe, pulando.")

    # 3 -- imagens
    titulo_etapa(2, TOTAL, "Imagens (Cloudflare)")
    rodar([py, str(RAIZ / "imagens.py")], proj, env, "imagens")

    # 4 -- narracao
    motor = args.voz or cfg["motor_voz"]
    if args.refazer_voz:
        for arq in ("narracao.wav", "tempos_cenas.json", "palavras.json"):
            (proj / arq).unlink(missing_ok=True)
    titulo_etapa(3, TOTAL, f"Narracao ({motor})")
    if (proj / "narracao.wav").exists() and (proj / "tempos_cenas.json").exists():
        log("Ja existe, pulando. (use --refazer-voz para trocar a voz)")
    elif motor == "chatterbox":
        py_voz = cfg["python_voz"] or py
        if not Path(py_voz).exists() and py_voz != py:
            log(f"ERRO: python_voz nao encontrado: {py_voz}")
            log("Veja o LEIAME da voz ou use motor_voz = kokoro no config.json.")
            sys.exit(1)
        env_voz = dict(env)
        ref = Path(cfg["voz_referencia"])
        ref = ref if ref.is_absolute() else RAIZ / ref
        if ref.exists():
            env_voz["VOZ_REFERENCIA"] = str(ref)
        rodar([py_voz, str(RAIZ / "tts_chatterbox.py")], proj, env_voz, "narracao (chatterbox)")
    else:
        rodar([py, str(RAIZ / "tts_kokoro.py")], proj, env, "narracao")

    # 5 -- legendas
    titulo_etapa(4, TOTAL, "Legendas palavra por palavra (Whisper)")
    if (proj / "palavras.json").exists():
        log("Ja existe, pulando.")
    else:
        rodar([py, str(RAIZ / "align.py")], proj, env, "legendas")

    # 6 -- reunir arquivos e renderizar
    titulo_etapa(5, TOTAL, "Montando os arquivos do video")
    for arq in ("narracao.wav", "tempos_cenas.json", "palavras.json"):
        shutil.copyfile(proj / arq, proj / "public" / arq)
    preparar_audio(proj, cfg, env, py, nome, args.sem_musica)
    log("Arquivos prontos.")

    titulo_etapa(6, TOTAL, "Edicao e renderizacao (Remotion) - esta etapa demora")
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        log("ERRO: o 'npx' nao foi encontrado. Instale o Node.js.")
        sys.exit(1)
    if saida.exists() and not args.rerender:
        log("O video ja existe. Use --rerender para renderizar de novo.")
        log(f"Video: {saida}")
        return
    if saida.exists():
        saida.unlink()
    rodar(
        [
            npx, "remotion", "render", "src/index.ts", "Documentario", str(saida),
            f"--public-dir={proj / 'public'}",
            f"--concurrency={cfg['concorrencia']}",
        ],
        RAIZ,
        env,
        "renderizacao",
    )

    if cfg.get("normalizar_volume", True):
        normalizar_volume(saida, cfg.get("lufs", -14))

    minutos = (time.time() - inicio) / 60
    log("")
    log("=" * 60)
    log(f" PRONTO em {minutos:.1f} minutos")
    log(f" Video: {saida}")
    log("=" * 60)
    if WINDOWS:
        try:
            os.startfile(str(saida.parent))
        except OSError:
            pass


if __name__ == "__main__":
    main()
