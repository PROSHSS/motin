"""
VERDADE: pesquisa com fontes + verificacao de cada frase.

Fluxo (tudo automatico, sem pressa):
  1. pesquisar(tema)   -> busca noticias recentes, Wikipedia e dados oficiais (Banco Central) na internet
  2. extrair fatos     -> o Ollama le cada fonte e extrai fatos curtos; fatos com numero/nome que NAO estao
                          no texto original sao descartados (checagem automatica, sem IA)
  3. o roteiro so pode usar esses fatos (cada cena cita os ids [F1], [F2]...)
  4. verificar_cenas   -> cada frase e conferida: numeros, nomes, opiniao, e um "juiz" (Ollama) que reescreve
                          o que nao tem apoio nos fatos
Se o tema e sensivel (politica, saude, crime...) e NAO ha fontes, o video NAO e criado.
"""
import html
import json
import re
import time
import unicodedata
import urllib.parse
from datetime import datetime
from html.parser import HTMLParser

import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept-Language": "pt-BR,pt;q=0.9"}
OLLAMA_URL = "http://localhost:11434"

SENSIVEL = [
    "eleic", "elei", "candidat", "president", "governador", "prefeit", "senado", "deputad", "congresso", "stf", "tse",
    "partido", "lula", "bolsonaro", "politic", "voto", "urna", "golpe de estado", "impeachment", "ministro",
    "crime", "assassin", "morte", "morreu", "mortes", "preso", "prisao", "policia", "homicid", "estupro", "violencia",
    "feminicid", "acidente", "tragedia", "guerra", "ataque", "terror", "israel", "gaza", "ucrania", "russia",
    "vacina", "cancer", "doenca", "virus", "pandemia", "remedio", "medicamento", "tratamento", "suicid", "depress",
    "religi", "igreja", "aborto", "racis", "preconceito", "lgbt", "drog", "tráfico", "trafico",
    "investiment", "bolsa de valores", "acoes", "cripto", "bitcoin", "emprestimo", "financiamento", "aposentad", "inss",
    "governo", "transicao", "posse", "eleito", "dolar", "cambio", "selic", "inflac", "juros", "imposto", "tribut", "reforma", "salario minimo", "pix", "golpe",
]
OPINIAO = ["absurdo", "vergonha", "vergonhoso", "corrupto", "criminoso", "culpado", "inacreditavel", "chocante", "escandalo",
           "obviamente", "claramente", "com certeza", "todo mundo sabe", "ninguem", "sempre", "nunca", "pior", "melhor do mundo",
           "inaceitavel", "covarde", "mentiroso", "genial", "horrivel", "terrivel", "desastre", "milagre", "garantido", "garantia"]
SERIES_BCB = {  # codigo SGS -> (nome, unidade, palavras-chave do tema)
    432: ("Meta da taxa Selic definida pelo Copom", "% ao ano", ["selic", "juros", "copom", "taxa basica"]),
    433: ("IPCA, variacao mensal", "%", ["ipca", "inflacao", "precos", "custo de vida"]),
    13522: ("IPCA acumulado em 12 meses", "%", ["ipca", "inflacao", "precos", "custo de vida"]),
    1: ("Dolar comercial (venda), cotacao do dia", "R$", ["dolar", "cambio", "moeda", "real"]),
    21619: ("Euro (venda), cotacao do dia", "R$", ["euro", "cambio"]),
}


def norm(t):
    t = unicodedata.normalize("NFD", str(t).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def log(m=""):
    print(m, flush=True)


# ---------------------------------------------------------------------
# ferramentas de texto
# ---------------------------------------------------------------------
class _Extrator(HTMLParser):
    PULAR = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg", "iframe"}

    def __init__(self):
        super().__init__()
        self.skip = 0
        self.em_p = False
        self.atual = []
        self.paragrafos = []

    def handle_starttag(self, tag, attrs):
        if tag in self.PULAR:
            self.skip += 1
        if tag in ("p", "h1", "h2", "li") and not self.skip:
            self.em_p = True
            self.atual = []

    def handle_endtag(self, tag):
        if tag in self.PULAR and self.skip:
            self.skip -= 1
        if tag in ("p", "h1", "h2", "li") and self.em_p:
            t = " ".join("".join(self.atual).split())
            if len(t) >= 50:
                self.paragrafos.append(t)
            self.em_p = False

    def handle_data(self, d):
        if self.em_p and not self.skip:
            self.atual.append(d)


def extrair_texto_html(codigo, limite=5000):
    p = _Extrator()
    try:
        p.feed(codigo)
    except Exception:
        pass
    vistos, out = set(), []
    for t in p.paragrafos:
        k = t[:60]
        if k in vistos:
            continue
        vistos.add(k)
        out.append(html.unescape(t))
    return " ".join(out)[:limite]


def numeros_de(texto):
    """Todos os numeros do texto, normalizados (47,03 -> 47.03; 1.299 -> 1299; 'R$ 5' -> 5)."""
    achados = re.findall(r"\d[\d.,]*\d|\d", texto)
    out = set()
    for a in achados:
        b = a.replace(".", "").replace(",", ".") if ("," in a or re.search(r"\.\d{3}\b", a)) else a
        try:
            out.add(str(float(b)).rstrip("0").rstrip("."))
        except ValueError:
            pass
    return out


def nomes_proprios(texto):
    """Palavras com inicial maiuscula que nao abrem frase (nomes de pessoas, lugares, instituicoes)."""
    out = set()
    for frase in re.split(r"(?<=[.!?])\s+", texto):
        pal = re.findall(r"[A-Za-zÀ-ÿ][\wÀ-ÿ'-]*", frase)
        for i, w in enumerate(pal):
            if i > 0 and w[0].isupper() and len(w) > 2 and not w.isupper():
                out.add(norm(w))
            elif i > 0 and w.isupper() and len(w) >= 3:
                out.add(norm(w))
    return out


# ---------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------
def pedir_json(prompt, schema, modelo, temperatura=0.0, ctx=6144, timeout=1800):
    r = requests.post(f"{OLLAMA_URL}/api/chat", json={
        "model": modelo, "stream": False, "think": False,
        "options": {"num_ctx": ctx, "temperature": temperatura},
        "format": schema, "messages": [{"role": "user", "content": prompt}],
    }, timeout=timeout)
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


# ---------------------------------------------------------------------
# 1) busca de fontes
# ---------------------------------------------------------------------
def _get(url, timeout=20):
    try:
        r = requests.get(url, headers=UA, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r
    except requests.RequestException:
        pass
    return None


def _itens_rss(xml):
    itens = []
    for bloco in re.findall(r"<item>(.*?)</item>", xml, flags=re.S):
        def tag(n):
            m = re.search(rf"<{n}[^>]*>(.*?)</{n}>", bloco, flags=re.S)
            return html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1))).strip() if m else ""
        itens.append({"titulo": tag("title"), "link": tag("link"), "data": tag("pubDate"), "fonte": tag("source") or tag("News:Source")})
    return itens


def _data_iso(s):
    for f in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
        try:
            return datetime.strptime(s.strip(), f).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def _link_direto(link):
    if "bing.com/news/apiclick" in link:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
        if q.get("url"):
            return q["url"][0]
    return link


def buscar_noticias(tema, maximo=8):
    q = urllib.parse.quote(tema)
    achados = []
    r = _get(f"https://www.bing.com/news/search?q={q}&format=rss&setmkt=pt-BR&setlang=pt-BR")
    if r:
        for it in _itens_rss(r.text):
            it["link"] = _link_direto(it["link"])
            achados.append(it)
    r = _get(f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419")
    if r:
        for it in _itens_rss(r.text):
            achados.append(it)
    # remove repetidas e mantem uma por dominio
    vistos, dominios, out = set(), set(), []
    for it in achados:
        k = norm(it["titulo"])[:50]
        dom = urllib.parse.urlparse(it["link"]).netloc.replace("www.", "")
        if not it["titulo"] or k in vistos:
            continue
        vistos.add(k)
        if dom in dominios and "news.google" not in dom:
            continue
        dominios.add(dom)
        out.append(it)
    return out[: maximo * 2]


def ler_artigo(it):
    link = it["link"]
    r = _get(link)
    if not r:
        return ""
    if "consent.google" in r.url or "news.google.com" in r.url:
        return ""   # redirecionador do Google que nao abriu: ignora
    return extrair_texto_html(r.text)


def wikipedia(tema):
    r = _get("https://pt.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=1&srsearch=" + urllib.parse.quote(tema))
    if not r:
        return None
    try:
        res = r.json()["query"]["search"]
        if not res:
            return None
        titulo = res[0]["title"]
        r2 = _get("https://pt.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(titulo.replace(" ", "_")))
        if not r2:
            return None
        d = r2.json()
        txt = d.get("extract", "")
        if len(txt) < 80:
            return None
        return {"titulo": titulo, "fonte": "Wikipedia", "link": d.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "data": "", "texto": txt[:2500]}
    except (ValueError, KeyError):
        return None


def dados_oficiais(tema):
    """Cotacoes e indices direto do Banco Central (sem IA, valor exato)."""
    t = norm(tema)
    fatos = []
    for cod, (nome, un, chaves) in SERIES_BCB.items():
        if not any(c in t for c in chaves):
            continue
        r = _get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados/ultimos/6?formato=json")
        if not r:
            continue
        try:
            pts = r.json()
            ult = pts[-1]
            val = float(ult["valor"])
        except (ValueError, KeyError, IndexError):
            continue
        txt_val = f"R$ {val:.2f}".replace(".", ",") if un == "R$" else f"{val:.2f}".replace(".", ",") + (" " + un if un else "")
        fatos.append({"texto": f"{nome}: {txt_val} em {ult['data']}, segundo o Banco Central.", "fonte": "Banco Central do Brasil",
                      "link": f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados/ultimos/6?formato=json",
                      "data": datetime.strptime(ult["data"], "%d/%m/%Y").strftime("%Y-%m-%d"), "tipo": "numero",
                      "oficial": True, "corroborado": True, "serie": [(p["data"], float(p["valor"])) for p in pts]})
    return fatos


# ---------------------------------------------------------------------
# 2) extracao de fatos (com checagem automatica contra o texto original)
# ---------------------------------------------------------------------
SCHEMA_FATOS = {"type": "object", "properties": {"fatos": {"type": "array", "items": {"type": "object", "properties": {
    "texto": {"type": "string"}, "tipo": {"type": "string", "enum": ["numero", "data", "declaracao", "contexto"]}},
    "required": ["texto", "tipo"]}}}, "required": ["fatos"]}


def extrair_fatos(fonte, modelo):
    prompt = (
        "Voce e verificador de fatos. Do TEXTO abaixo, extraia ate 6 fatos ATOMICOS, objetivos e verificaveis.\n"
        "REGRAS: copie numeros, nomes, cargos e datas EXATAMENTE como estao no texto. Cada fato e UMA frase completa em portugues "
        "(ate 25 palavras) que se entende sozinha. Quando for declaracao de alguem, escreva 'Segundo <quem>, ...'. "
        "NAO inclua opiniao, adjetivos, previsoes, rumores nem nada que nao esteja escrito no texto. NAO invente. "
        "Se o texto nao traz fatos concretos, devolva lista vazia.\n"
        f"FONTE: {fonte['fonte']} ({fonte.get('data', '')})\nTITULO: {fonte['titulo']}\nTEXTO:\n{fonte['texto'][:3800]}\n"
    )
    try:
        bruto = pedir_json(prompt, SCHEMA_FATOS, modelo)
    except (requests.RequestException, ValueError, KeyError):
        return []
    base = norm(fonte["texto"] + " " + fonte["titulo"])
    nums_base = numeros_de(fonte["texto"] + " " + fonte["titulo"])
    out = []
    for f in bruto.get("fatos", []):
        t = " ".join(str(f.get("texto", "")).split())
        if len(t) < 25 or len(t) > 260:
            continue
        if not numeros_de(t) <= nums_base:            # numero que nao esta no texto original: descarta
            continue
        nomes = nomes_proprios(t)
        if any(n not in base for n in nomes):          # nome que nao esta no texto original: descarta
            continue
        if any(o in norm(t) for o in OPINIAO):
            continue
        out.append({"texto": t, "tipo": f.get("tipo", "contexto"), "fonte": fonte["fonte"], "link": fonte.get("link", ""),
                    "data": fonte.get("data", ""), "oficial": False, "corroborado": False})
    return out


def _jaccard(a, b):
    A, B = set(norm(a).split()), set(norm(b).split())
    return len(A & B) / max(1, len(A | B))


def eh_sensivel(tema):
    t = norm(tema)
    return any(norm(k) in t for k in SENSIVEL)


def montar_base(tema, modelo, maximo_fontes=6):
    """Pesquisa completa. Devolve {'fatos': [...], 'fontes': [...], 'sensivel': bool, 'data': 'AAAA-MM-DD'}."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    log(f"Pesquisando fontes sobre: {tema}")
    fontes = []
    noticias = buscar_noticias(tema)
    log(f"  {len(noticias)} noticia(s) encontrada(s); lendo as melhores...")
    for it in noticias:
        if len(fontes) >= maximo_fontes:
            break
        txt = ler_artigo(it)
        if len(txt) < 300:
            continue
        fonte_nome = re.sub(r"^.* - ", "", it["titulo"]) if " - " in it["titulo"] and not it["fonte"] else (it["fonte"] or urllib.parse.urlparse(it["link"]).netloc)
        fontes.append({"titulo": re.sub(r" - [^-]+$", "", it["titulo"]), "fonte": fonte_nome, "link": it["link"],
                       "data": _data_iso(it["data"]), "texto": txt})
        log(f"  [leu] {fonte_nome}: {it['titulo'][:70]}")
    w = wikipedia(tema)
    if w:
        fontes.append(w)
        log("  [leu] Wikipedia")
    fatos = dados_oficiais(tema)
    if fatos:
        log(f"  {len(fatos)} dado(s) oficial(is) do Banco Central")
    for i, f in enumerate(fontes, 1):
        log(f"  extraindo fatos da fonte {i}/{len(fontes)}: {f['fonte']}...")
        fatos += extrair_fatos(f, modelo)
    # corroboracao: numero que aparece em 2+ fontes diferentes
    for f in fatos:
        if f.get("oficial"):
            continue
        nums = numeros_de(f["texto"])
        if not nums:
            f["corroborado"] = True
            continue
        n_fontes = sum(1 for s in fontes if nums <= numeros_de(s["texto"]))
        f["corroborado"] = n_fontes >= 2
    # remove duplicados
    unicos = []
    for f in fatos:
        if any(_jaccard(f["texto"], u["texto"]) > 0.7 for u in unicos):
            continue
        unicos.append(f)
    # mais recentes e oficiais primeiro
    unicos.sort(key=lambda f: (not f.get("oficial"), f.get("data", "") == "", [-ord(c) for c in f.get("data", "")]))
    unicos = unicos[:24]
    for i, f in enumerate(unicos, 1):
        f["id"] = f"F{i}"
    return {"tema": tema, "data": hoje, "sensivel": eh_sensivel(tema), "fatos": unicos,
            "fontes": [{"fonte": s["fonte"], "titulo": s["titulo"], "link": s.get("link", ""), "data": s.get("data", "")} for s in fontes]}


def texto_fatos(base, fatos_usuario=""):
    linhas = []
    for f in base["fatos"]:
        sel = "OFICIAL" if f.get("oficial") else ("confirmado por 2+ fontes" if f.get("corroborado") else "fonte unica")
        d = f" em {f['data']}" if f.get("data") else ""
        linhas.append(f"[{f['id']}] {f['texto']} (Fonte: {f['fonte']}{d}; {sel})")
    if fatos_usuario.strip():
        linhas.append("FATOS DO USUARIO (confiaveis):\n" + fatos_usuario.strip())
    return "\n".join(linhas)


def texto_dos_fatos_usados(base, ids, fatos_usuario=""):
    mapa = {f["id"]: f for f in base["fatos"]}
    txt = " ".join(mapa[i]["texto"] for i in ids if i in mapa)
    return (txt + " " + (fatos_usuario or "")).strip()


# ---------------------------------------------------------------------
# 3) verificacao de cada frase
# ---------------------------------------------------------------------
SCHEMA_JUIZ = {"type": "object", "properties": {
    "suportada": {"type": "boolean"}, "problemas": {"type": "array", "items": {"type": "string"}},
    "corrigida": {"type": "string"}}, "required": ["suportada", "problemas", "corrigida"]}


def checar_frase(frase, apoio, tema, sensivel, papel="meio"):
    """Checagem automatica (sem IA). Devolve lista de problemas."""
    problemas = []
    ap = norm(apoio + " " + tema)
    nums_ok = numeros_de(apoio) | numeros_de(tema)
    extra_n = numeros_de(frase) - nums_ok
    if extra_n:
        problemas.append("numero sem apoio nos fatos: " + ", ".join(sorted(extra_n)))
    for n in nomes_proprios(frase):
        if n not in ap and n not in {"brasil", "brasileiro", "brasileira"}:
            problemas.append("nome sem apoio nos fatos: " + n)
    for o in OPINIAO:
        if re.search(rf"\b{re.escape(o)}\b", norm(frase)):
            problemas.append("palavra de opiniao/exagero: " + o)
    if re.search(r"[^\x00-ɏ‐-›€°ºª]", frase):
        problemas.append("caractere estranho")
    if "*" in frase or "#" in frase or "undefined" in frase.lower():
        problemas.append("lixo de formatacao")
    return problemas


def reescrever_frase(frase, apoio, problemas, modelo, sensivel, estilo_cena=""):
    regra = ("Tema SENSIVEL: use tom neutro e factual, atribua afirmacoes a fonte ('segundo ...'), sem adjetivos, sem opiniao, sem previsao. "
             if sensivel else "Tom claro e natural, sem exageros. ")
    prompt = (
        "Voce e editor de checagem de um video de noticias. Reescreva a FRASE usando SOMENTE as informacoes dos FATOS.\n"
        f"{regra}Mantenha o mesmo assunto e tamanho parecido (ate 18 palavras). Nao acrescente numero, nome ou data que nao esteja nos fatos. "
        "Se os fatos nao sustentam a ideia da frase, escreva uma frase fiel ao que os fatos dizem.\n"
        f"FRASE: {frase}\nPROBLEMAS ENCONTRADOS: {'; '.join(problemas) or 'verificar apoio nos fatos'}\nFATOS:\n{apoio}\n"
        "Responda no JSON: suportada (true se a frase ORIGINAL ja estava 100% apoiada), problemas, corrigida (a frase final)."
    )
    try:
        r = pedir_json(prompt, SCHEMA_JUIZ, modelo, temperatura=0.1)
        return " ".join(str(r.get("corrigida", "")).split()), bool(r.get("suportada"))
    except (requests.RequestException, ValueError, KeyError):
        return "", False


def juiz(frase, apoio, modelo):
    prompt = (
        "Voce e juiz de checagem. A FRASE esta 100% apoiada pelos FATOS? So e 'suportada' se TODA informacao da frase "
        "(numeros, nomes, datas, relacoes de causa, quem disse o que) estiver nos fatos. Frase que insinua culpa, causa ou "
        "futuro nao dito nos fatos NAO e suportada.\n"
        f"FRASE: {frase}\nFATOS:\n{apoio}\nResponda no JSON: suportada, problemas, corrigida (deixe vazio se suportada)."
    )
    try:
        r = pedir_json(prompt, SCHEMA_JUIZ, modelo, temperatura=0.0)
        return bool(r.get("suportada")), [str(p) for p in r.get("problemas", [])]
    except (requests.RequestException, ValueError, KeyError):
        return False, ["juiz indisponivel"]


FRASES_SEGURAS = {
    "gancho": "Veja o que se sabe até agora sobre este assunto.",
    "meio": "Acompanhe os próximos passos pelas fontes oficiais.",
    "fecho": "Siga para acompanhar as atualizações.",
}


def verificar_cenas(cenas, base, modelo, tema, fatos_usuario="", tentativas=3):
    """cenas: lista de dicts do LLM (com 'narracao' e 'fatos': ['F1',...]). Corrige ou troca o que nao tem apoio."""
    sens = base["sensivel"]
    total = len(cenas)
    for i, c in enumerate(cenas):
        nar = " ".join(str(c.get("narracao", "")).split())
        ids = [x for x in (c.get("fatos") or []) if re.fullmatch(r"F\d+", str(x))]
        papel = "gancho" if i == 0 else ("fecho" if i == total - 1 else "meio")
        apoio = texto_dos_fatos_usados(base, ids, fatos_usuario)
        if not apoio:   # cena sem fatos: usa todos como apoio, mas so passa se nao tiver numero/nome novo
            apoio = texto_dos_fatos_usados(base, [f["id"] for f in base["fatos"]], fatos_usuario)
        final, ok = nar, False
        for t in range(tentativas):
            prob = checar_frase(final, apoio, tema, sens, papel)
            if not prob:
                sup, prob_j = juiz(final, apoio, modelo)
                if sup:
                    ok = True
                    break
                prob = prob_j or ["sem apoio claro nos fatos"]
            log(f"    cena {i + 1}: ajustando ({'; '.join(prob)[:110]})")
            nova, _ = reescrever_frase(final, apoio, prob, modelo, sens)
            if nova and nova != final:
                final = nova
            else:
                break
        if not ok:
            prob = checar_frase(final, apoio, tema, sens, papel)
            if prob or not final:
                log(f"    cena {i + 1}: sem apoio suficiente; usando frase segura.")
                final = FRASES_SEGURAS[papel]
        c["narracao"] = final
        c["verificada"] = True
    return cenas


# ---------------------------------------------------------------------
# revisao de texto (ortografia/clareza) com guarda de numeros
# ---------------------------------------------------------------------
SCHEMA_REV = {"type": "object", "properties": {"textos": {"type": "array", "items": {"type": "string"}}}, "required": ["textos"]}


def limpar_texto(t):
    t = re.sub(r"[*_#`~^|<>{}\[\]]", "", str(t))
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)                       # espaco antes da pontuacao
    t = re.sub(r"([,;:!?])(?=[A-Za-zÀ-ÿ])", r"\1 ", t)            # falta espaco depois da pontuacao
    t = re.sub(r"\b([A-Za-zÀ-ÿ]{2,})(\s+\1\b)+", r"\1", t, flags=re.I)  # palavra repetida ("de de")
    t = re.sub(r"([.!?])\s+([a-zà-ÿ])", lambda m: m.group(1) + " " + m.group(2).upper(), t)
    if t and t[0].islower():
        t = t[0].upper() + t[1:]
    return t


def revisar_textos(textos, modelo):
    """Corrige ortografia e pontuacao em portugues. Se mudar numero ou tamanho demais, mantem o original."""
    if not textos:
        return textos
    prompt = (
        "Voce e revisor de portugues do Brasil. Corrija SOMENTE ortografia, acentuacao, concordancia e pontuacao de cada texto da lista. "
        "NAO mude o sentido, NAO troque palavras por sinonimos, NAO mude numeros, nomes ou datas. Devolva a lista NA MESMA ORDEM e com o "
        f"MESMO numero de itens ({len(textos)}).\n" + json.dumps(textos, ensure_ascii=False)
    )
    try:
        r = pedir_json(prompt, SCHEMA_REV, modelo, temperatura=0.0)
        novos = r.get("textos", [])
    except (requests.RequestException, ValueError, KeyError):
        return textos
    if len(novos) != len(textos):
        return textos
    out = []
    for a, b in zip(textos, novos):
        b = limpar_texto(b)
        if not b or numeros_de(a) != numeros_de(b) or abs(len(b) - len(a)) > max(6, 0.25 * len(a)):
            out.append(a)
        else:
            out.append(b)
    return out


def juntar_fatos_usuario(base, texto):
    """Fatos escritos pelo usuario no fatos.txt entram como confiaveis (um por linha)."""
    linhas = [l.strip(" -*\t") for l in (texto or "").splitlines() if len(l.strip()) > 15]
    if not linhas:
        return base
    base = dict(base)
    novos = [{"texto": l, "tipo": "usuario", "fonte": "Informado pelo autor", "link": "", "data": "", "oficial": True,
              "corroborado": True} for l in linhas[:20]]
    todos = novos + [f for f in base.get("fatos", [])]
    for i, f in enumerate(todos, 1):
        f["id"] = f"F{i}"
    base["fatos"] = todos[:30]
    return base
