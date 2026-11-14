"""Fotos REAIS sem problema de direito autoral.

Fontes (o programa busca sozinho, em ordem):
  1) A pasta  projetos\\<tema>\\fotos\\  (suas fotos, fotos que voce tem autorizacao de usar, dominio publico).
     Nome da foto = cena que ela ilustra:  cena3.jpg  (ou qualquer nome: vao para as cenas de foto em ordem).
     Opcional: creditos.txt na mesma pasta, uma linha por foto:   cena3.jpg | Autor | Licenca | Link
  2) Wikimedia Commons (busca automatica): so entram fotos CC0, dominio publico ou CC BY (e CC BY-SA se
     voce permitir). Nunca NC (uso nao comercial) nem ND. O credito do autor aparece na tela e na legenda_post.txt.

Cada foto usada e registrada em creditos_fotos.txt (titulo, autor, licenca, link) para voce conferir.
"""
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "doc-tiktok/1.0 (video educativo; contato: o proprio autor)"}
EXT = {".jpg", ".jpeg", ".png", ".webp"}
RUIM_TITULO = re.compile(r"logo|flag|bandeira|map\b|mapa|diagram|chart|icon|coat of arms|brasao|signature|screenshot|poster|cartaz|\.svg|\.pdf|\.tif", re.I)


def _limpa(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(t or "")))).strip()


def licenca_ok(nome, permitir_sa=False):
    n = (nome or "").lower().replace("-", " ").replace("_", " ")
    if re.search(r"\bnc\b|\bnd\b|noncommercial|no derivs|fair use|copyrighted|all rights", n):
        return False
    if re.search(r"\bcc0\b|public domain|\bpd\b|dominio publico|domínio público|\bpdm\b", n):
        return True
    if re.match(r"cc by( |$)", n) and "sa" not in n.split():
        return True
    if re.match(r"cc by sa", n):
        return permitir_sa
    return False


def palavras_chave(consulta):
    return [w for w in re.findall(r"[a-zà-ÿ0-9]{4,}", consulta.lower()) if w not in {"with", "from", "that", "this", "para", "from"}]


def _candidato(p, kws, permitir_sa, exigir_relevancia=True, min_larg=900):
    ii = (p.get("imageinfo") or [{}])[0]
    titulo = p.get("title", "")
    if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < min_larg or RUIM_TITULO.search(titulo):
        return None
    meta = ii.get("extmetadata") or {}
    val = lambda k: _limpa((meta.get(k) or {}).get("value"))  # noqa: E731
    lic = val("LicenseShortName") or val("UsageTerms")
    if not licenca_ok(lic, permitir_sa) or val("Restrictions"):
        return None
    autor = val("Artist") or val("Credit")
    if len(autor) > 60:
        autor = autor[:57].rsplit(" ", 1)[0] + "..."
    if not autor and "public domain" not in lic.lower() and "cc0" not in lic.lower():
        return None   # CC BY exige autor
    texto = (titulo + " " + val("ImageDescription") + " " + val("ObjectName") + " " + val("Categories")).lower()
    pontos = sum(1 for k in kws if k in texto)
    if exigir_relevancia and kws and pontos < max(1, min(2, (len(kws) + 1) // 2)):
        return None
    cred = f"Foto: {autor + ' / ' if autor else ''}Wikimedia Commons / {lic}"
    return {"titulo": titulo, "url": ii.get("thumburl") or ii.get("url"), "pagina": ii.get("descriptionurl", ""),
            "autor": autor, "licenca": lic, "credito": cred[:90], "pontos": pontos, "area": ii.get("width", 0) * ii.get("height", 0)}


def buscar_commons(consulta, permitir_sa=False, min_larg=900, limite=15, usados=()):
    """Devolve candidatos {titulo, url, pagina, autor, licenca, credito, pontos}, melhores primeiro."""
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
              "gsrsearch": f"{consulta} filetype:bitmap", "gsrlimit": limite, "prop": "imageinfo",
              "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600}
    r = requests.get(API, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    paginas = (r.json().get("query") or {}).get("pages") or {}
    kws = palavras_chave(consulta)
    out = []
    for p in paginas.values():
        c = _candidato(p, kws, permitir_sa, True, min_larg)
        if c and c["titulo"] not in usados:
            out.append(c)
    out.sort(key=lambda c: (-c["pontos"], -min(c["area"], 2_000_000)))
    return out


def _sem_acento(t):
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(ch) != "Mn")


def buscar_entidade(nome, permitir_sa=False, usados=()):
    """Foto PRINCIPAL da pagina da Wikipedia (pt e en) da pessoa/instituicao/lugar com esse nome.
    A identidade e garantida pelo titulo da pagina: todas as palavras do nome precisam estar nele.
    So vale se o arquivo estiver no Commons com licenca livre."""
    toks = [t for t in re.findall(r"[a-z0-9]{3,}", _sem_acento(nome)) if t not in {"the", "dos", "das", "del", "van", "von"}]
    if not toks:
        return []
    out = []
    for lang in ("pt", "en"):
        try:
            r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", params={
                "action": "query", "format": "json", "generator": "search", "gsrsearch": nome, "gsrlimit": 3,
                "prop": "pageimages", "piprop": "name", "redirects": 1}, headers=UA, timeout=30)
            r.raise_for_status()
        except requests.RequestException:
            continue
        paginas = (r.json().get("query") or {}).get("pages") or {}
        for p in sorted(paginas.values(), key=lambda x: x.get("index", 9)):
            tit = _sem_acento(p.get("title", ""))
            arq = p.get("pageimage")
            if not arq or not all(t in tit for t in toks):
                continue
            try:
                r2 = requests.get(API, params={"action": "query", "format": "json", "titles": "File:" + arq, "prop": "imageinfo",
                                               "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600}, headers=UA, timeout=30)
                r2.raise_for_status()
            except requests.RequestException:
                continue
            for pg in ((r2.json().get("query") or {}).get("pages") or {}).values():
                c = _candidato(pg, [], permitir_sa, False, 500)
                if c and c["titulo"] not in usados:
                    c["pontos"] = 99
                    c["origem"] = f"Wikipedia ({lang}): {p.get('title')}"
                    out.append(c)
        if out:
            break
    return out


def buscar_openverse(consulta, permitir_sa=False, usados=(), limite=12):
    """Openverse: busca em varios bancos livres (Flickr, Wikimedia, museus...). So CC0, dominio publico e CC BY."""
    lic = "cc0,by,pdm" + (",by-sa" if permitir_sa else "")
    r = requests.get("https://api.openverse.org/v1/images/", params={"q": consulta, "license": lic, "page_size": limite, "mature": "false"},
                     headers=UA, timeout=30)
    r.raise_for_status()
    kws = palavras_chave(consulta)
    out = []
    for it in r.json().get("results", []):
        titulo = _limpa(it.get("title"))
        tags = " ".join(t.get("name", "") for t in (it.get("tags") or []))
        if (it.get("width") or 0) < 900 or RUIM_TITULO.search(titulo + " " + (it.get("url") or "")):
            continue
        texto = (titulo + " " + tags).lower()
        pontos = sum(1 for k in kws if k in texto)
        if kws and pontos < max(1, min(2, (len(kws) + 1) // 2)):
            continue
        if re.search(r"\b(person|people|man|woman|girl|boy|child|children|face|portrait|selfie)\b", texto):
            continue   # foto de gente comum: sem autorizacao de imagem, nao usa
        lic_nome = f"CC {it.get('license', '').upper()}" + (f" {it.get('license_version')}" if it.get("license_version") else "")
        if it.get("license") in ("cc0", "pdm"):
            lic_nome = "CC0" if it.get("license") == "cc0" else "Dominio publico"
        autor = _limpa(it.get("creator"))[:50]
        if not autor and it.get("license") == "by":
            continue
        out.append({"titulo": titulo or it.get("id", ""), "url": it.get("url"), "pagina": it.get("foreign_landing_url", ""),
                    "autor": autor, "licenca": lic_nome, "credito": f"Foto: {autor + ' / ' if autor else ''}{it.get('source', 'Openverse')} / {lic_nome}"[:90],
                    "pontos": pontos, "area": (it.get("width") or 0) * (it.get("height") or 0)})
    out = [c for c in out if c["titulo"] not in usados]
    out.sort(key=lambda c: (-c["pontos"], -min(c["area"], 2_000_000)))
    return out


def baixar_como_jpg(url, destino):
    ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    destino = Path(destino)
    bruto = destino.with_suffix(".baixado")
    r = requests.get(url, headers=UA, timeout=90)
    r.raise_for_status()
    bruto.write_bytes(r.content)
    if ff:
        p = subprocess.run([ff, "-y", "-v", "error", "-i", str(bruto), "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", str(destino)])
        bruto.unlink(missing_ok=True)
        return p.returncode == 0 and destino.exists()
    bruto.replace(destino)
    return True


def ler_creditos_pasta(pasta):
    """creditos.txt:  arquivo | autor | licenca | link"""
    f = Path(pasta) / "creditos.txt"
    out = {}
    if f.exists():
        for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            partes = [x.strip() for x in ln.split("|")]
            if len(partes) >= 2 and partes[0] and not ln.strip().startswith("#"):
                out[partes[0].lower()] = partes
    return out


def fotos_da_pasta(pasta):
    """{numero_da_cena: arquivo} para nomes cenaN.ext, e lista de arquivos sem numero (em ordem)."""
    pasta = Path(pasta)
    numeradas, livres = {}, []
    if not pasta.exists():
        return numeradas, livres
    for f in sorted(pasta.iterdir()):
        if f.suffix.lower() not in EXT:
            continue
        if re.match(r"cena\s*0*\d+[_ -]*(objeto|recorte)", f.stem, re.I):
            continue
        m = re.match(r"cena\s*0*(\d+)", f.stem, re.I)
        if m:
            numeradas[int(m.group(1))] = f
        else:
            livres.append(f)
    return numeradas, livres


def credito_da_pasta(arq, creditos):
    p = creditos.get(arq.name.lower())
    if not p:
        return "", "SEM CREDITO registrado em creditos.txt"
    autor, lic = p[1], (p[2] if len(p) > 2 else "")
    if autor.lower() in ("proprio", "própria", "propria", "próprio", "eu"):
        return "Foto: acervo próprio", ""
    return f"Foto: {autor}" + (f" ({lic})" if lic else ""), ""


def arquivo_extra(pasta, n, tipo):
    """cena3_objeto.jpg / cena3_recorte.png (se existir)"""
    for f in Path(pasta).glob("*"):
        if f.suffix.lower() in EXT and re.match(rf"cena\s*0*{n}[_ -]*{tipo}$", f.stem, re.I):
            return f
    return None


_SESSAO = {}


def remover_fundo(origem, destino):
    """Recorta a pessoa da foto (PNG com transparencia). Precisa do rembg (opcional): pip install rembg onnxruntime"""
    try:
        from rembg import new_session, remove
    except ImportError:
        return False
    try:
        if "s" not in _SESSAO:
            _SESSAO["s"] = new_session("u2net_human_seg")
        saida = remove(Path(origem).read_bytes(), session=_SESSAO["s"])
        Path(destino).write_bytes(saida)
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------
# Conferencia opcional da foto por um modelo de VISAO do Ollama (config "modelo_visao")
# ---------------------------------------------------------------------
def foto_combina(caminho, descricao, modelo, nome_proprio=""):
    """Pergunta ao modelo de visao se a imagem mostra o que a cena precisa. Em duvida (erro/indisponivel) devolve True
    para nao travar. Devolve False quando o modelo diz claramente que NAO combina."""
    import base64
    try:
        img = base64.b64encode(Path(caminho).read_bytes()).decode()
        pergunta = (f"Esta imagem mostra: {descricao}? " + (f"Deve ser relacionada a: {nome_proprio}. " if nome_proprio else "") +
                    "Responda so no JSON: combina (true se a imagem e uma foto real, nitida, SEM texto grande e que combina com isso; false se nao tem relacao, "
                    "e um logo, mapa, grafico, capa, print de tela, meme ou desenho).")
        r = requests.post("http://localhost:11434/api/chat", json={
            "model": modelo, "stream": False, "think": False, "options": {"num_ctx": 4096, "temperature": 0},
            "format": {"type": "object", "properties": {"combina": {"type": "boolean"}}, "required": ["combina"]},
            "messages": [{"role": "user", "content": pergunta, "images": [img]}]}, timeout=600)
        r.raise_for_status()
        return bool(json.loads(r.json()["message"]["content"]).get("combina", True))
    except Exception:  # noqa: BLE001
        return True
