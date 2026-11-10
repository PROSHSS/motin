"""
Gerador de roteiros do Showcase.
Entrada: um tema (e, se quiser, fatos reais). Saida: dict pronto para o Remotion.
Cada execucao sorteia estilo, paleta, ordem das cenas e animacoes, entao nao sai igual.
"""
import json
import random
import re
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent
OLLAMA_URL = "http://localhost:11434"

CLASSES = ["imagem", "cinetica", "silhuetas", "documento", "versus", "explicativa", "grafico_barras", "grafico_linha",
           "rosca", "numero_gigante", "frase", "lista_caixas", "painel"]
CLASSES_DADOS = {"grafico_barras", "grafico_linha", "rosca", "numero_gigante", "painel", "versus"}   # so com fatos reais
OPC = {"imagens": True, "fatos": False}   # preenchido por chamar_llm
FOTOS = ["foto_hero", "foto_celular", "foto_lupa", "foto_polaroid", "foto_recorte", "foto_persianas", "foto_card3d"]
TIPOS = FOTOS + ["classica", "gancho", "celular", "lupa", "processo", "grafico", "rajada", "checklist", "fecho",
         "comparacao", "contador", "ranking", "linha_tempo", "alerta", "citacao"]
ICONES = ["Tag", "Clock", "Flame", "Bell", "Search", "LineChart", "Scale", "ShieldCheck", "BadgeCheck", "Lock", "Key",
          "Smartphone", "Mail", "MessageCircle", "CreditCard", "Banknote", "Coins", "Wallet", "TrendingUp", "TrendingDown",
          "Percent", "Calendar", "MapPin", "Globe", "Heart", "Star", "Zap", "Lightbulb", "Target", "Eye", "Brain",
          "TriangleAlert", "Siren", "Users", "House", "Car", "Plane", "ShoppingCart", "Gift", "Handshake"]

DUR = {"gancho": 2.4, "celular": 2.7, "lupa": 2.4, "processo": 4.0, "grafico": 2.8, "rajada": 2.7, "checklist": 2.7,
       "fecho": 2.9, "classica": 3.2, "foto_hero": 3.0, "foto_celular": 3.2, "foto_lupa": 3.2, "foto_polaroid": 3.2,
       "foto_recorte": 3.0, "foto_persianas": 3.0, "foto_card3d": 3.0, "fato_real": 6.3, "fato_documento": 5.0, "comparacao": 3.3, "contador": 3.0, "ranking": 3.4, "linha_tempo": 3.4, "alerta": 2.7, "citacao": 3.0,
       "cartaz": 3.2, "foto_moldura": 3.2, "busca": 3.4, "pilula": 3.0, "glitch": 2.6, "pasta": 3.4}
VARIEDADE = ["cartaz", "foto_moldura", "busca", "pilula", "glitch", "pasta"]   # montadas por programa, so com texto da narracao

SCHEMA = {
    "type": "object",
    "properties": {
        "titulo": {"type": "string"},
        "cenas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": TIPOS},
                    "narracao": {"type": "string"},
                    "manchete": {"type": "array", "items": {"type": "string"}},
                    "fatos": {"type": "array", "items": {"type": "string"}},
                    "chips": {"type": "array", "items": {"type": "object", "properties": {"texto": {"type": "string"}, "valor": {"type": "string"}}}},
                    "rotulo": {"type": "string"},
                    "classe": {"type": "string", "enum": CLASSES},
                    "destaque": {"type": "string"},
                    "elementos": {"type": "array", "items": {"type": "object", "properties": {
                        "tipo": {"type": "string", "enum": ["icone", "numero", "lista"]},
                        "texto": {"type": "string"}, "icone": {"type": "string", "enum": ICONES}}}},
                    "fantasma": {"type": "string"},
                    "etiqueta": {"type": "object", "properties": {"texto": {"type": "string"}, "sub": {"type": "string"}}},
                    "notificacoes": {"type": "array", "items": {"type": "object", "properties": {
                        "icone": {"type": "string", "enum": ICONES}, "titulo": {"type": "string"}, "texto": {"type": "string"}}}},
                    "lupa": {"type": "object", "properties": {"preco": {"type": "string"}, "rotulo": {"type": "string"}}},
                    "processo": {"type": "object", "properties": {k: {"type": "string"} for k in
                                 ["rotulo", "campo", "de", "para", "badge", "final", "botao"]}},
                    "grafico": {"type": "object", "properties": {
                        "rotulo": {"type": "string"}, "valores": {"type": "array", "items": {"type": "number"}},
                        "marcadores": {"type": "array", "items": {"type": "object", "properties": {
                            "i": {"type": "integer"}, "texto": {"type": "string"}}}},
                        "botao": {"type": "string"}}},
                    "rajada": {"type": "array", "items": {"type": "object", "properties": {
                        "icone": {"type": "string", "enum": ICONES}, "texto": {"type": "string"}}}},
                    "checklist": {"type": "array", "items": {"type": "string"}},
                    "comparacao": {"type": "object", "properties": {
                        "a": {"type": "object", "properties": {"titulo": {"type": "string"}, "valor": {"type": "string"},
                                                               "itens": {"type": "array", "items": {"type": "string"}}}},
                        "b": {"type": "object", "properties": {"titulo": {"type": "string"}, "valor": {"type": "string"},
                                                               "itens": {"type": "array", "items": {"type": "string"}}}},
                        "vencedor": {"type": "string", "enum": ["a", "b"]}}},
                    "contador": {"type": "object", "properties": {
                        "rotulo": {"type": "string"}, "de": {"type": "number"}, "para": {"type": "number"},
                        "prefixo": {"type": "string"}, "sufixo": {"type": "string"}, "legenda": {"type": "string"}}},
                    "ranking": {"type": "object", "properties": {"titulo": {"type": "string"}, "itens": {
                        "type": "array", "items": {"type": "object", "properties": {
                            "nome": {"type": "string"}, "valor": {"type": "number"}, "texto": {"type": "string"}}}}}},
                    "linha_tempo": {"type": "array", "items": {"type": "object", "properties": {
                        "ano": {"type": "string"}, "texto": {"type": "string"}}}},
                    "alerta": {"type": "object", "properties": {"titulo": {"type": "string"}, "texto": {"type": "string"},
                                                                "selo": {"type": "string"}}},
                    "citacao": {"type": "object", "properties": {"texto": {"type": "string"}, "autor": {"type": "string"}}},
                    "fecho": {"type": "object", "properties": {"pergunta": {"type": "string"}, "cta": {"type": "string"}}},
                },
                "required": ["tipo", "narracao", "manchete"],
            },
        },
    },
    "required": ["titulo", "cenas"],
}

REGRAS = """Voce e roteirista e diretor de motion design de videos curtos de TikTok (formato vertical) com NARRACAO falada.
Escreva em portugues do Brasil, tom natural, claro e envolvente. O video tem de 8 a 10 cenas, e cada cena tem:
- narracao: 1 frase curta (ate 16 palavras), ou 2 frases bem curtas, que serao FALADAS (sem emojis, sem hashtags, numeros e "R$" escritos como se fala; nada de siglas confusas). A narracao e o roteiro de verdade: conta a historia do tema em sequencia, com comeco, meio e fim.
- o visual da cena (tipo e dados), que ilustra o que a narracao diz naquele momento.
A primeira cena (gancho) abre com uma pergunta ou afirmacao forte que prende nos 3 primeiros segundos. A ultima (fecho) termina com uma pergunta ou chamada para seguir.
Textos NA TELA sao ainda mais curtos que a narracao (poucas palavras).
A primeira cena e SEMPRE do tipo "gancho" e a ultima e SEMPRE do tipo "fecho".
Escolha as cenas do meio entre os tipos que combinam com o que a narracao diz, sem repetir o mesmo tipo duas vezes seguidas. Estilo pedido: {estilo}. Prefira estes tipos: {preferir}. Evite: {evitar}.

COMO PREENCHER CADA TIPO (preencha SOMENTE o campo do tipo da cena, alem de manchete):
- manchete: 1 ou 2 linhas curtas (ate 28 letras cada). Marque **PALAVRA** (em negrito, vira letra grossa) em 1 palavra e *palavra* (em italico, vira serifada) em outra. Ex: ["**BLACK FRIDAY**", "e *engano*?"].
- gancho: fantasma (1 palavra em MAIUSCULAS ate 8 letras, ex FALSO), etiqueta {{texto: numero ou palavra curta como "-70%" ou "GOLPE", sub: ate 3 palavras}}.
- celular: notificacoes (3 a 4): icone, titulo (MAIUSCULAS ate 20 letras), texto (ate 28 letras). fantasma opcional.
- lupa: lupa {{preco: ex "R$ 1.299", rotulo: ex "PRECO ANTES"}}. Use para algo que precisa ser olhado de perto (valor, numero, detalhe).
- processo: processo {{rotulo: nome do campo, campo: valor digitado (ex "R$ 999"), de: valor que aparece (ex "R$ 1.299"), para: resultado final (ex "R$ 909"), badge: ex "30% OFF", final: frase curta de conclusao, botao: ex "Aplicar"}}.
- grafico: grafico {{rotulo, valores: 10 a 13 numeros, marcadores: 1 a 2 itens {{i: indice do valor, texto curto}}, botao: ex "Ver historico"}}.
- rajada: rajada = 4 a 5 itens {{icone, texto em MAIUSCULAS de 1 palavra}} (passos ou ideias rapidas).
- checklist: checklist = 3 itens de 1 palavra (ate 10 letras).
- comparacao: comparacao {{a: {{titulo, valor, itens: 3 itens curtos}}, b: {{...}}, vencedor: "a" ou "b"}}.
- contador: contador {{rotulo, de: 0, para: numero, prefixo: ex "R$ ", sufixo: ex "%", legenda: frase curta}}.
- ranking: ranking {{titulo, itens: 4 a 5 {{nome, valor (numero), texto (valor escrito)}}, do maior para o menor}}.
- linha_tempo: linha_tempo = 3 a 4 itens {{ano (ou data/etapa curta), texto ate 28 letras}}.
- alerta: alerta {{titulo (ate 18 letras, MAIUSCULAS), texto (ate 80 letras), selo (ate 8 letras)}}.
- citacao: citacao {{texto (frase marcante ate 80 letras), autor opcional}}.
- fecho: fecho {{pergunta (ate 70 letras, termina com ...?), cta: ex "Siga para mais"}}.

CENAS CLASSICAS (tipo "classica"; preencha classe, destaque e elementos; use {n_cl} cenas assim no video, entre as do meio, para dar variedade; classes preferidas: {cl_pref}):
- classe "imagem": foto de fundo gerada por IA com frase grande. destaque = frase de ate 5 palavras. elementos = []. {linha_img}
- classe "cinetica": texto gigante de impacto. destaque = 1 palavra ou expressao curta (ate 12 letras). elementos[0].texto = frase curta ANTES do destaque; elementos[1..2] = linhas DEPOIS (curtas). Comece com "~" para negar.
- classe "silhuetas": sobre pessoas/populacao. destaque = 2 a 3 palavras. elementos[0].texto = frase curta antes (opcional).
- classe "documento": regra, lei ou definicao. destaque = carimbo de ate 9 letras. elementos[0].texto = origem; elementos[1].texto = a regra completa; elementos[2].texto = trecho COPIADO exato de elementos[1].
- classe "explicativa": conceito com icones. destaque = titulo curto. elementos = 2 a 4 itens com tipo "icone" (texto ate 4 palavras) e icone da lista.
- classe "frase": ideia forte. destaque = frase de 3 a 8 palavras sem ponto. elementos[0].texto = uma palavra que esta no destaque; elementos[1].texto = "caixa", "circulo", "sublinhado" ou "x".
- classe "lista_caixas": destaque = titulo curto; elementos = 2 a 4 itens de 1 a 3 palavras.
- classes de DADOS (so com fatos reais, senao NAO use): "numero_gigante" (destaque = numero com unidade, ex "87%"; elementos[0].texto = o que mede), "grafico_barras" (elementos "Nome|valor", 2 a 5), "grafico_linha" (elementos "ano|valor", 3 a 6), "rosca" (elementos "Nome|45%", soma 100), "painel" (3 a 4 elementos "Rotulo|valor"), "versus" (2 elementos "Nome 47,03%").

REGRA DE VERDADE (a mais importante): a lista FATOS VERIFICADOS abaixo e a UNICA fonte de informacao. Cada cena deve trazer em "fatos" os ids ([F1], [F2]...) que sua narracao usa, e a narracao so pode afirmar o que esta nesses fatos (copie numeros, nomes e datas exatamente). Nunca invente numero, nome, data, citacao nem relacao de causa. Narracao do gancho e do fecho nao tem numeros novos. Se um fato for "fonte unica", escreva "segundo <fonte>". Datas relativas ("hoje", "ontem") so se o fato trouxer a data. Se NAO houver fatos, escreva apenas dicas gerais e atemporais, sem numeros, sem nomes proprios e sem datas.
{aviso_ilustrativo}{aviso_sensivel}{aviso_memoria}
"""


# ---------------------------------------------------------------------
# estilos
# ---------------------------------------------------------------------
def carregar_estilos():
    est = {}
    pasta = RAIZ / "estilos"
    if pasta.exists():
        for f in sorted(pasta.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                est[d.get("nome", f.stem)] = d
            except json.JSONDecodeError:
                print(f"AVISO: estilo com erro de formato ignorado: {f.name}")
    if not est:
        est["padrao"] = {"nome": "padrao", "paleta": ["ouro"], "gancho": ["etiqueta"], "preferir": [], "evitar": [], "ritmo": 1.0}
    return est


def escolher_estilo(nome, rnd, evitar=()):
    est = carregar_estilos()
    if nome and nome != "auto":
        if nome not in est:
            print("Estilos disponiveis:", ", ".join(est))
            sys.exit(f"Estilo '{nome}' nao existe.")
        return est[nome]
    livres = [n for n in sorted(est) if n not in set(evitar)] or sorted(est)
    return est[rnd.choice(livres)]


# ---------------------------------------------------------------------
# chamada ao Ollama
# ---------------------------------------------------------------------
def chamar_llm(tema, fatos, estilo, modelo, tentativas=2, mistura=None, usar_imagens=True, base=None, memoria_txt=""):
    OPC["imagens"] = bool(usar_imagens)
    OPC["fatos"] = bool((fatos or "").strip())
    mistura = estilo.get("mistura", 0.3) if mistura is None else mistura
    n_cl = round(max(0.0, min(1.0, mistura)) * 8)
    cl_pref = [c for c in (estilo.get("classicas") or CLASSES) if usar_imagens or c != "imagem"]
    if not OPC["fatos"]:
        cl_pref = [c for c in cl_pref if c not in CLASSES_DADOS] or ["cinetica", "frase", "lista_caixas"]
    tem_base = bool(base and base.get("fatos"))
    sens = bool(base and base.get("sensivel"))
    aviso_il = ("Os tipos lupa, processo e celular mostram EXEMPLOS ILUSTRATIVOS (valores de exemplo, com aviso na tela): use so se o tema for "
                "dica/explicacao de compra ou golpe, nunca para noticia. O tipo grafico so e permitido quando ha dado oficial de serie temporal nos fatos.\n"
                if tem_base else "")
    aviso_sen = ("TEMA SENSIVEL: tom neutro e factual, sem adjetivos, sem opiniao, sem previsao, sem acusar ninguem; atribua cada afirmacao a fonte; "
                 "NAO use lupa, processo, celular nem grafico.\n" if sens else "")
    aviso_mem = (f"VARIEDADE: nos ultimos videos foram muito usados estes tipos de cena/abertura: {memoria_txt}. Evite repetir; use tipos DIFERENTES.\n"
                 if memoria_txt else "")
    regras = REGRAS.format(
        aviso_ilustrativo=aviso_il, aviso_sensivel=aviso_sen, aviso_memoria=aviso_mem,
        n_cl=n_cl if n_cl else "0 (nenhuma)",
        cl_pref=", ".join(cl_pref),
        linha_img="Use no maximo 2 cenas imagem." if usar_imagens else "NAO use a classe imagem.",
        estilo=estilo.get("descricao", estilo["nome"]),
        preferir=", ".join(estilo.get("preferir", [])) or "qualquer",
        evitar=", ".join(estilo.get("evitar", [])) or "nenhum",
    )
    if tem_base:
        import verdade as V
        fatos_txt = V.texto_fatos(base, fatos)
    else:
        fatos_txt = fatos or "(nenhum fato: escreva somente dicas gerais e atemporais, sem numeros, nomes proprios ou datas)"
    from datetime import datetime as _dt
    prompt = f"{regras}\nData de hoje: {_dt.now().strftime('%d/%m/%Y')}\nTema: {tema}\nFATOS VERIFICADOS:\n{fatos_txt}\n"
    ultimo = None
    for i in range(tentativas):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json={
                "model": modelo, "stream": False, "think": False,
                "options": {"num_ctx": 6144, "temperature": 0.7 + 0.1 * i},
                "format": SCHEMA,
                "messages": [{"role": "user", "content": prompt}],
            }, timeout=1800)
            r.raise_for_status()
            return json.loads(r.json()["message"]["content"])
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            ultimo = e
            print(f"  tentativa {i + 1} falhou ({e}); tentando de novo...")
    raise RuntimeError(f"Ollama nao respondeu direito: {ultimo}")


# ---------------------------------------------------------------------
# limpeza / validacao
# ---------------------------------------------------------------------
_PENDENTES = {"de", "da", "do", "das", "dos", "e", "o", "a", "os", "as", "em", "no", "na", "nos", "nas", "para", "por", "com",
              "que", "um", "uma", "ao", "aos", "à", "às", "ou", "se", "mas", "como", "pelo", "pela", "sem", "sobre", "entre", "até"}


def s(v, n=60):
    """Limpa espacos e corta no tamanho SEM quebrar palavra e sem terminar em 'de', 'da', 'e'... (texto cortado parece erro)."""
    t = re.sub(r"\s+", " ", str(v or "")).strip()
    if len(t) <= n:
        return t
    if " " not in t[: n + 1] and " " not in t and len(t) <= int(n * 1.7) + 2:
        return t   # palavra unica: nunca corta no meio (o texto encolhe sozinho para caber)
    corte = t[:n]
    if t[n] != " " and " " in corte:
        corte = corte[: corte.rfind(" ")]
    pal = corte.split(" ")
    while len(pal) > 1 and (pal[-1].lower().strip(",;:.-") in _PENDENTES):
        pal.pop()
    return " ".join(pal).rstrip(" ,;:-")


def _sem_acentos(t):
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(ch) != "Mn")


def fantasma_ok(valor, narracao="", n=9):
    """Palavra-fantasma sempre INTEIRA: nunca corta no meio (ex. PRESIDEN). Se a palavra for longa demais,
    usa a maior palavra inteira da narracao que caiba."""
    v = re.sub(r"[^A-Za-zÀ-ÿ0-9%$-]", "", str(valor or "").split(" ")[0] if str(valor or "").strip() else "")
    palavras_nar = {_sem_acentos(w) for w in re.findall(r"[A-Za-zÀ-ÿ0-9%$-]+", narracao or "")}
    if v and len(v) <= n and (not narracao or _sem_acentos(v) in palavras_nar or v.isdigit()):
        return v.upper()   # so vale palavra INTEIRA que existe na narracao (nada cortado nem inventado)
    cand = [w for w in re.findall(r"[A-Za-zÀ-ÿ]+", narracao or "") if 4 <= len(w) <= n and w.lower() not in _PENDENTES]
    if cand:
        return max(cand, key=len).upper()
    return v.upper() if v and len(v) <= n and not narracao else ""


def manchete(linhas, rnd):
    """'**FORTE** e *serifa* texto' -> partes. Sem marcacao, sorteia o estilo."""
    out = []
    for ln in (linhas or [])[:2]:
        ln = s(ln, 40)
        if not ln:
            continue
        # "faz a *dezembro*": artigo/preposicao solto antes da palavra em destaque soa como erro
        ln = re.sub(r"\b(?:de|da|do|das|dos|e|o|a|os|as|em|no|na|para|por|com|que|um|uma|ao)\s+(?=\*[^*]+\*\s*$)", "", ln, flags=re.I)
        partes = []
        for tok in re.split(r"(\*\*.+?\*\*|\*.+?\*)", ln):
            if not tok:
                continue
            if tok.startswith("**"):
                partes.append({"t": tok.strip("*"), "e": "forte"})
            elif tok.startswith("*"):
                partes.append({"t": tok.strip("*"), "e": "serifa"})
            else:
                partes.append({"t": tok, "e": "fina"})
        if not any(p["e"] != "fina" for p in partes):
            pal = ln.split(" ")
            if len(pal) == 1:
                partes = [{"t": ln, "e": "forte"}]
            else:
                k = rnd.randrange(len(pal))
                partes = []
                if k:
                    partes.append({"t": " ".join(pal[:k]) + " ", "e": "fina"})
                partes.append({"t": pal[k], "e": rnd.choice(["serifa", "forte"])})
                if k < len(pal) - 1:
                    partes.append({"t": " " + " ".join(pal[k + 1:]), "e": "fina"})
        out.append(partes)
    return out


def num(v, padrao=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return padrao


def icone(v):
    return v if v in ICONES else "Star"



def _gatilhos(elementos, narracao):
    """Associa cada elemento a uma palavra da narracao (para aparecer no momento em que e falado)."""
    def norm(x):
        return re.sub(r"[^a-z0-9]", "", __import__("unicodedata").normalize("NFD", x.lower()).encode("ascii", "ignore").decode())
    palavras = [norm(w) for w in re.findall(r"\w+", narracao)]
    usados = set()
    pos = 0
    for e in elementos:
        cands = [norm(w) for w in re.findall(r"\w+", e["texto"].split("|")[0])]
        cands = [w for w in cands if len(w) > 3]
        achou = None
        for i in range(pos, len(palavras)):
            if palavras[i] in cands and palavras[i] not in usados:
                achou = i
                break
        if achou is not None:
            e["gatilho"] = palavras[achou]
            usados.add(palavras[achou])
            pos = achou
    return elementos


def sanear_classica(c):
    classe = c.get("classe")
    nar = s(c.get("narracao"), 400)
    if classe not in CLASSES or not nar:
        return None
    if classe == "imagem" and not OPC["imagens"]:
        return None
    if classe in CLASSES_DADOS and not OPC["fatos"]:
        return None
    dest = s(c.get("destaque"), 70)
    if not dest:
        return None
    els = []
    for e in (c.get("elementos") or [])[:5]:
        t = s(e.get("texto"), 90)
        if t:
            els.append({"tipo": e.get("tipo") if e.get("tipo") in ("icone", "numero", "lista") else "lista",
                        "texto": t, "icone": icone(e.get("icone"))})
    n = len(els)
    if classe == "imagem":
        els = []
        dest = s(dest, 40)
    elif classe == "documento":
        if n < 2:
            return None
        trecho = els[2]["texto"] if n > 2 else ""
        if not trecho or trecho not in els[1]["texto"]:
            els = els[:2] + [{"tipo": "lista", "texto": " ".join(els[1]["texto"].split()[:4]).rstrip(",.;"), "icone": "Check"}]
        dest = s(dest, 9)
    elif classe == "cinetica":
        if n < 1:
            els = [{"tipo": "lista", "texto": "", "icone": "Check"}]
        dest = s(dest, 14)
    elif classe == "versus":
        if n != 2 or not all(re.search(r"\d", e["texto"]) for e in els):
            return None
    elif classe == "explicativa":
        if n < 2:
            return None
    elif classe in ("grafico_barras", "rosca", "painel"):
        if n < 2 or not all("|" in e["texto"] and re.search(r"\d", e["texto"].split("|")[-1]) for e in els):
            return None
        for e in els:
            e["tipo"] = "lista"
    elif classe == "grafico_linha":
        if n < 3 or not all("|" in e["texto"] and re.search(r"\d", e["texto"].split("|")[-1]) for e in els):
            return None
        for e in els:
            e["tipo"] = "lista"
    elif classe == "numero_gigante":
        if not re.search(r"\d", dest) or n < 1:
            return None
    elif classe == "frase":
        if n < 2 or els[1]["texto"].lower() not in ("caixa", "circulo", "sublinhado", "x"):
            els = [{"tipo": "lista", "texto": (dest.split() or ["ideia"])[-1], "icone": "Check"},
                   {"tipo": "lista", "texto": "sublinhado", "icone": "Check"}]
    elif classe == "lista_caixas":
        if n < 2:
            return None
    if classe not in ("frase", "documento", "cinetica", "imagem"):
        els = _gatilhos(els, nar)
    r = {"tipo": "classica", "duracao": DUR["classica"], "narracao": nar,
         "cena": {"narracao": nar, "tipo": classe, "destaque": dest, "elementos": els}}
    ids = [x for x in (c.get("fatos") or []) if re.fullmatch(r"F\d+", str(x))]
    if ids:
        r["fatos"] = ids
    return r


def sanear_fato_real(c):
    """Cena de perfil documental: tudo ja vem pronto e conferido (nome, linhas da narracao, numero da evidencia)."""
    titulo = s(c.get("titulo"), 34)
    linhas = [s(x, 40) for x in (c.get("linhas") or []) if s(x)][:5]
    if not titulo or not linhas:
        return None
    o = {"tipo": "fato_real", "duracao": DUR["fato_real"], "titulo": titulo, "linhas": linhas}
    if s(c.get("narracao"), 400):
        o["narracao"] = s(c["narracao"], 400)
    n = c.get("numero")
    if isinstance(n, dict):
        try:
            o["numero"] = {"prefixo": s(n.get("prefixo"), 4), "valor": float(n["valor"]), "decimais": int(n.get("decimais") or 0),
                           "sufixo": s(n.get("sufixo"), 14).rstrip() if not str(n.get("sufixo") or "").startswith(" ") else " " + s(n.get("sufixo"), 14),
                           "rotulo": s(n.get("rotulo"), 28)}
        except (KeyError, TypeError, ValueError):
            pass
    ids = [x for x in (c.get("fatos") or []) if re.fullmatch(r"F\d+", str(x))]
    if ids:
        o["fatos"] = ids
    return o


def sanear_fato_documento(c):
    d = c.get("documento") or {}
    trecho = re.sub(r"\s+", " ", str(d.get("trecho") or "")).strip()
    fonte = s(d.get("fonte"), 50)
    if not trecho or not fonte or len(trecho) > 240:
        return None
    o = {"tipo": "fato_documento", "duracao": DUR["fato_documento"],
         "documento": {"fonte": fonte, "data": s(d.get("data"), 12), "trecho": trecho,
                       "destaques": [x for x in (d.get("destaques") or []) if x and x in trecho][:4],
                       "selo": s(d.get("selo"), 12) or "CONFERIDO"}}
    if s(c.get("narracao"), 400):
        o["narracao"] = s(c["narracao"], 400)
    ids = [x for x in (c.get("fatos") or []) if re.fullmatch(r"F\d+", str(x))]
    if ids:
        o["fatos"] = ids
    return o


def _lista(v, n, tam):
    out = []
    for x in (v or [])[:n]:
        t = s(x, tam)
        if t:
            out.append(t)
    return out


def sanear_variedade(c):
    """Cenas de variedade: todo texto ja vem da narracao/evidencia (montado por programa); aqui so confere formato e tamanho."""
    t = c.get("tipo")
    o = {"tipo": t, "duracao": DUR[t]}
    if s(c.get("narracao"), 400):
        o["narracao"] = s(c["narracao"], 400)
    ids = [x for x in (c.get("fatos") or []) if re.fullmatch(r"F\d+", str(x))]
    if ids:
        o["fatos"] = ids
    if t == "cartaz":
        pal = _lista(c.get("palavras"), 5, 16)
        if len(pal) < 3:
            return None
        o["palavras"] = pal
        o["realce"] = [i for i in (c.get("realce") or []) if isinstance(i, int) and 0 <= i < len(pal)][:1]
        o["rotulo"] = s(c.get("rotulo"), 24)
    elif t == "foto_moldura":
        lin = _lista(c.get("linhas"), 4, 40)
        tags = _lista(c.get("tags"), 2, 16)
        if not lin or not tags:
            return None
        o.update({"linhas": lin, "tags": tags})
    elif t == "busca":
        q = s(c.get("consulta"), 44)
        res = _lista(c.get("resultados"), 3, 74)
        if not q or len(res) < 2:
            return None
        o.update({"consulta": q, "resultados": res, "rotulo": s(c.get("rotulo"), 16) or "Resultado"})
    elif t == "pilula":
        lin = _lista(c.get("linhas"), 4, 30)
        dest = s(c.get("destaque"), 24)
        if len(lin) < 2 or not dest or dest.lower() not in " ".join(lin).lower():
            return None
        o.update({"linhas": lin, "destaque": dest})
    elif t == "glitch":
        w = s(c.get("palavra"), 14)
        lin = _lista(c.get("linhas"), 3, 36)
        if not w or not lin:
            return None
        o.update({"palavra": w, "linhas": lin})
    elif t == "pasta":
        car = _lista(c.get("cartoes"), 3, 34)
        tit = s(c.get("titulo"), 30)
        if len(car) < 3 or not tit:
            return None
        o.update({"titulo": tit, "cartoes": car, "rotulo": s(c.get("rotulo"), 14) or "Ponto"})
    return o


def sanear_cena(c, rnd, estilo):
    t = c.get("tipo")
    if t == "fato_real":
        return sanear_fato_real(c)
    if t == "fato_documento":
        return sanear_fato_documento(c)
    if t in VARIEDADE:
        return sanear_variedade(c)
    if t not in TIPOS:
        return None
    if t == "classica":
        return sanear_classica(c)
    if t in FOTOS:
        o = {"tipo": t, "duracao": DUR[t], "manchete": manchete(c.get("manchete"), rnd)}
        if s(c.get("narracao"), 400):
            o["narracao"] = s(c["narracao"], 400)
        o["chips"] = [{"texto": s(x.get("texto"), 24), **({"valor": s(x.get("valor"), 8)} if s(x.get("valor")) else {})}
                      for x in (c.get("chips") or []) if s(x.get("texto"))][:3]
        o["rotulo"] = s(c.get("rotulo"), 48)
        fan = fantasma_ok(c.get("fantasma"), c.get("narracao", ""))
        if fan:
            o["fantasma"] = fan
        elif t == "foto_recorte":
            return None
        if not o["manchete"]:
            return None
        return o
    o = {"tipo": t, "duracao": DUR[t], "manchete": manchete(c.get("manchete"), rnd)}
    if s(c.get("narracao"), 400):
        o["narracao"] = s(c["narracao"], 400)
    ids = [x for x in (c.get("fatos") or []) if re.fullmatch(r"F\d+", str(x))]
    if ids:
        o["fatos"] = ids
    fan = fantasma_ok(c.get("fantasma"), c.get("narracao", "")) if c.get("fantasma") else ""
    if fan:
        o["fantasma"] = fan
    if t == "gancho":
        e = c.get("etiqueta") or {}
        if not s(e.get("texto")):
            return None
        o["etiqueta"] = {"texto": s(e.get("texto"), 38), "sub": s(e.get("sub"), 22)}
        o["variante"] = rnd.choice(estilo.get("gancho") or ["etiqueta"])
        if o["variante"] == "digitando" and len(o["etiqueta"]["texto"]) < 8:
            o["variante"] = "etiqueta"
    elif t == "celular":
        n = [{"icone": icone(x.get("icone")), "titulo": s(x.get("titulo"), 22).upper(), "texto": s(x.get("texto"), 30)}
             for x in (c.get("notificacoes") or []) if s(x.get("titulo"))][:4]
        if len(n) < 2:
            return None
        o["notificacoes"] = n
    elif t == "lupa":
        l = c.get("lupa") or {}
        if not s(l.get("preco")):
            return None
        o["lupa"] = {"preco": s(l["preco"], 14), "rotulo": s(l.get("rotulo"), 20).upper() or "ANTES"}
    elif t == "processo":
        p = c.get("processo") or {}
        if not (s(p.get("campo")) and s(p.get("de")) and s(p.get("para")) and s(p.get("badge"))):
            return None
        o["processo"] = {"rotulo": s(p.get("rotulo"), 28) or "Valor", "campo": s(p["campo"], 10), "de": s(p["de"], 10),
                         "para": s(p["para"], 10), "badge": s(p["badge"], 10), "final": s(p.get("final"), 40),
                         "botao": s(p.get("botao"), 10) or "Aplicar"}
        o["duracao"] = DUR[t]
    elif t == "grafico":
        g = c.get("grafico") or {}
        v = [num(x) for x in (g.get("valores") or [])][:14]
        if len(v) < 6 or max(v) == min(v):
            return None
        m = [{"i": int(x.get("i", 0)), "texto": s(x.get("texto"), 20)} for x in (g.get("marcadores") or [])
             if isinstance(x.get("i"), int) and 0 <= x["i"] < len(v) and s(x.get("texto"))][:2]
        o["grafico"] = {"rotulo": s(g.get("rotulo"), 34) or "Evolução", "valores": v, "marcadores": m,
                        "botao": s(g.get("botao"), 14) or "Ver histórico"}
    elif t == "rajada":
        r = [{"icone": icone(x.get("icone")), "texto": s(x.get("texto"), 12).upper()} for x in (c.get("rajada") or [])
             if s(x.get("texto"))][:5]
        if len(r) < 3:
            return None
        o["rajada"] = r
        o["duracao"] = round(max(2.4, len(r) * 0.5 + 0.3), 2)
    elif t == "checklist":
        k = [s(x, 12) for x in (c.get("checklist") or []) if s(x)][:4]
        if len(k) < 2:
            return None
        o["checklist"] = k
        o["duracao"] = round(1.4 + 0.7 * len(k), 2)
    elif t == "comparacao":
        d = c.get("comparacao") or {}
        a, b = d.get("a") or {}, d.get("b") or {}
        if not (s(a.get("titulo")) and s(b.get("titulo"))):
            return None
        f = lambda x: {"titulo": s(x.get("titulo"), 16), "valor": s(x.get("valor"), 12),
                       "itens": [s(i, 22) for i in (x.get("itens") or []) if s(i)][:3]}
        o["comparacao"] = {"a": f(a), "b": f(b), "vencedor": d.get("vencedor") if d.get("vencedor") in ("a", "b") else "b"}
    elif t == "contador":
        d = c.get("contador") or {}
        if num(d.get("para")) == 0:
            return None
        o["contador"] = {"rotulo": s(d.get("rotulo"), 30), "de": num(d.get("de")), "para": num(d.get("para")),
                         "prefixo": s(d.get("prefixo"), 4), "sufixo": s(d.get("sufixo"), 5), "legenda": s(d.get("legenda"), 50)}
    elif t == "ranking":
        d = c.get("ranking") or {}
        it = [{"nome": s(x.get("nome"), 14), "valor": abs(num(x.get("valor"))), "texto": s(x.get("texto"), 10)}
              for x in (d.get("itens") or []) if s(x.get("nome")) and num(x.get("valor")) != 0][:5]
        if len(it) < 3:
            return None
        it.sort(key=lambda x: -x["valor"])
        o["ranking"] = {"titulo": s(d.get("titulo"), 30), "itens": it}
        o["duracao"] = round(2.2 + 0.25 * len(it), 2)
    elif t == "linha_tempo":
        it = [{"ano": s(x.get("ano"), 8), "texto": s(x.get("texto"), 30)} for x in (c.get("linha_tempo") or [])
              if s(x.get("texto"))][:4]
        if len(it) < 3:
            return None
        o["linha_tempo"] = it
    elif t == "alerta":
        d = c.get("alerta") or {}
        if not s(d.get("titulo")):
            return None
        o["alerta"] = {"titulo": s(d["titulo"], 20).upper(), "texto": s(d.get("texto"), 90), "selo": s(d.get("selo"), 9).upper()}
    elif t == "citacao":
        d = c.get("citacao") or {}
        if not s(d.get("texto")):
            return None
        o["citacao"] = {"texto": s(d["texto"], 90), "autor": s(d.get("autor"), 30)}
    elif t == "fecho":
        d = c.get("fecho") or {}
        o["fecho"] = {"pergunta": s(d.get("pergunta"), 80) or "Gostou? Então não perca o próximo...",
                      "cta": s(d.get("cta"), 24) or "Siga para mais"}
        o.pop("manchete", None)
    return o


def cena_reserva(c, rnd):
    """Cena invalida mas com narracao: vira uma frase de destaque, para a historia nao perder trecho."""
    nar = s(c.get("narracao"), 400)
    if not nar:
        return None
    primeira = re.split(r"(?<=[.!?])\s+", nar)[0]
    r = {"tipo": "citacao", "duracao": DUR["citacao"], "narracao": nar, "manchete": manchete(c.get("manchete"), rnd),
         "citacao": {"texto": s(primeira, 90), "autor": ""}}
    if c.get("fatos"):
        r["fatos"] = c["fatos"]
    return r


ILUSTRATIVOS = {"lupa", "processo", "celular"}
_CHAVES_IGNORAR = {"tipo", "duracao", "narracao", "fatos", "fantasma", "icone", "variante", "i", "vencedor", "classe", "imagem",
                   "estilo", "ilustrativo", "verificada", "botao", "cta", "selo"}


def _textos_tela(o, acc=None):
    acc = [] if acc is None else acc
    if isinstance(o, dict):
        for k, v in o.items():
            if k in _CHAVES_IGNORAR:
                continue
            _textos_tela(v, acc)
    elif isinstance(o, list):
        for v in o:
            _textos_tela(v, acc)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        acc.append(str(o))
    elif isinstance(o, str):
        acc.append(o)
    return acc


def numeros_tela(cena):
    """Numeros que aparecem NA TELA e precisam ter apoio nos fatos (inteiros pequenos de contagem, como '5 dicas', sao livres)."""
    import verdade as V
    out = set()
    for t in _textos_tela({k: v for k, v in cena.items()}):
        for m in re.finditer(r"\d[\d.,]*\d|\d", t):
            tok = m.group(0)
            resto = t[m.end(): m.end() + 2]
            if re.fullmatch(r"\d{1,2}", tok) and int(tok) <= 12 and "%" not in resto:
                continue
            out |= V.numeros_de(tok)
    return out


def _serie_oficial(base):
    for f in base.get("fatos", []):
        if f.get("serie") and len(f["serie"]) >= 5:
            return f
    return None


def aplicar_verdade(cenas, base, fatos_usuario, rnd):
    """Modo factual: so passa na tela o que tem apoio nos fatos citados. O resto vira frase de destaque ou ganha aviso."""
    import verdade as V
    if not base or not base.get("fatos"):
        return cenas
    sens = base.get("sensivel")
    tema_nums = V.numeros_de(base.get("tema", ""))
    trocadas = 0
    for i in range(1, len(cenas) - 1):
        c = cenas[i]
        t = c["tipo"]
        if t == "classica":
            continue
        if t in ILUSTRATIVOS:
            if sens:
                cenas[i] = cena_reserva(c, rnd) or c
                trocadas += 1
                continue
            c["ilustrativo"] = True
        if t == "grafico":
            f = _serie_oficial(base)
            if not f or sens and not f.get("oficial"):
                cenas[i] = cena_reserva(c, rnd) or c
                trocadas += 1
                continue
            pts = f["serie"][-12:]
            c["grafico"]["valores"] = [v for _, v in pts]
            c["grafico"]["rotulo"] = s(f["texto"].split(":")[0], 34)
            c["grafico"]["marcadores"] = [{"i": len(pts) - 1, "texto": s(pts[-1][1], 8).replace(".", ",")}]
            c["fatos"] = [f["id"]]
            continue
        apoio = V.texto_dos_fatos_usados(base, c.get("fatos") or [], fatos_usuario)
        permitido = V.numeros_de(apoio) | tema_nums
        if numeros_tela(c) - permitido:
            r = cena_reserva(c, rnd)
            if r:
                cenas[i] = r
                trocadas += 1
    return cenas


def fontes_do_video(cenas, base):
    if not base or not base.get("fatos"):
        return []
    usados = []
    mapa = {f["id"]: f for f in base["fatos"]}
    for c in cenas:
        for i in c.get("fatos", []):
            f = mapa.get(i)
            if f and f["fonte"] not in usados:
                usados.append(f["fonte"])
    return usados[:3]


# ---------------------------------------------------------------------
# memoria entre videos (para nao repetir estilo, paleta, cenas e aberturas)
# ---------------------------------------------------------------------
PALETAS_TODAS = ["ouro", "oceano", "rubi", "menta", "lavanda", "laranja", "neon", "ambar", "ciano", "grafite"]


def ler_memoria(caminho):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))[-8:]
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def gravar_memoria(caminho, dados):
    mem = ler_memoria(caminho)
    mem.append({
        "titulo": dados.get("titulo", ""), "estilo": dados.get("estilo", ""), "paleta": dados.get("paleta", ""),
        "tipos": [c["tipo"] if c["tipo"] != "classica" else "c_" + c["cena"]["tipo"] for c in dados["cenas"]],
        "gancho": (dados["cenas"][0].get("variante") or "") if dados["cenas"] else "",
        "quando": time.strftime("%Y-%m-%d %H:%M"),
    })
    try:
        Path(caminho).write_text(json.dumps(mem[-8:], ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def resumo_memoria(mem):
    from collections import Counter
    cont = Counter(t for m in mem[-4:] for t in m.get("tipos", []) if t not in ("gancho", "fecho"))
    ganchos = [m.get("gancho") for m in mem[-3:] if m.get("gancho")]
    partes = [f"{t} (x{n})" for t, n in cont.most_common(5)]
    if ganchos:
        partes.append("aberturas " + ", ".join(ganchos))
    return "; ".join(partes)


def revisar_dados(dados, modelo):
    """Revisao ortografica de todo texto do video (narracao e telas), com guarda: numeros e tamanho nao podem mudar."""
    import verdade as V
    ignorar = {"tipo", "icone", "variante", "vencedor", "classe", "imagem", "estilo", "paleta", "gatilho", "fatos", "botao", "fantasma", "linhas", "titulo", "numero", "busca_real", "busca_objeto", "credito", "registro_real", "titulo_real"}
    refs = []

    def varrer(o):
        if isinstance(o, dict):
            for k, v in list(o.items()):
                if k in ignorar:
                    continue
                if isinstance(v, str) and len(v) >= 8 and "|" not in v:
                    refs.append((o, k))
                else:
                    varrer(v)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str) and len(v) >= 8 and "|" not in v:
                    refs.append((o, i))
                else:
                    varrer(v)
    for c in dados["cenas"]:
        if c["tipo"] == "classica":
            if c.get("narracao"):
                refs.append((c, "narracao"))
            continue
        varrer(c)
    textos = [V.limpar_texto(cont[k]) for cont, k in refs]
    novos = []
    for i in range(0, len(textos), 18):
        novos += V.revisar_textos(textos[i:i + 18], modelo)
    for (cont, k), t in zip(refs, novos):
        cont[k] = t
    # espelha a narracao revisada dentro da cena classica
    for c in dados["cenas"]:
        if c["tipo"] == "classica" and c.get("cena") and c.get("narracao"):
            c["cena"]["narracao"] = c["narracao"]
    return dados


def montar(dados_llm, tema, estilo, rnd, marca="", fps=30, narrado=False, base=None, fatos_usuario="", recentes_paleta=()):
    if narrado:
        return montar_narrado(dados_llm, tema, estilo, rnd, marca, fps, base, fatos_usuario, recentes_paleta)
    cenas = [x for x in (sanear_cena(c, rnd, estilo) for c in dados_llm.get("cenas", [])) if x]
    # gancho no inicio, fecho no fim
    gancho = next((c for c in cenas if c["tipo"] == "gancho"), None)
    fecho = next((c for c in cenas if c["tipo"] == "fecho"), None)
    meio = [c for c in cenas if c["tipo"] not in ("gancho", "fecho")]
    # sem repeticao seguida
    meio2 = []
    for c in meio:
        if meio2 and meio2[-1]["tipo"] == c["tipo"]:
            continue
        meio2.append(c)
    meio = meio2[:7]
    if gancho is None:
        gancho = {"tipo": "gancho", "duracao": DUR["gancho"], "fantasma": fantasma_ok(tema.split()[0], tema),
                  "etiqueta": {"texto": s(tema, 30), "sub": ""}, "variante": "digitando",
                  "manchete": manchete(["**" + s(tema, 24).upper() + "**"], rnd)}
    if fecho is None:
        fecho = {"tipo": "fecho", "duracao": DUR["fecho"], "fecho": {"pergunta": "Você já sabia disso...?", "cta": "Siga para mais"}}
    ritmo = estilo.get("ritmo", 1.0)
    todas = [gancho] + meio + [fecho]
    for c in todas:
        c["duracao"] = round(c["duracao"] * ritmo, 2)
    paleta = rnd.choice(estilo.get("paleta") or ["ouro"])
    return {"titulo": s(dados_llm.get("titulo") or tema, 80), "fps": fps, "paleta": paleta, "semente": rnd.randrange(1, 9999),
            "estilo": estilo["nome"], "marca": marca, "cenas": todas}


def montar_narrado(dados_llm, tema, estilo, rnd, marca="", fps=30, base=None, fatos_usuario="", recentes_paleta=()):
    """Versao com voz: nenhuma cena com narracao e descartada (a historia segue inteira)."""
    brutas = [c for c in dados_llm.get("cenas", []) if s(c.get("narracao"))][:11]
    cenas = []
    for c in brutas:
        x = sanear_cena(c, rnd, estilo) or cena_reserva(c, rnd)
        if x:
            cenas.append(x)
    if len(cenas) < 4:
        raise RuntimeError("a IA devolveu poucas cenas com narracao")
    # a primeira e sempre gancho e a ultima sempre fecho
    if cenas[0]["tipo"] != "gancho":
        c0 = cenas[0]
        pal = re.findall(r"\w+", c0["narracao"])
        cenas[0] = {"tipo": "gancho", "duracao": DUR["gancho"], "narracao": c0["narracao"], "variante": "digitando",
                    "fantasma": fantasma_ok(pal[0] if pal else tema, tema),
                    "etiqueta": {"texto": s(c0["narracao"], 60), "sub": ""},
                    "manchete": c0.get("manchete") or manchete(["**" + s(tema, 24).upper() + "**"], rnd)}
    else:
        cenas[0]["variante"] = cenas[0].get("variante") or "etiqueta"
    if cenas[-1]["tipo"] != "fecho":
        u = cenas[-1]
        cenas.append({"tipo": "fecho", "duracao": DUR["fecho"], "narracao": "Siga para ver mais conteúdos como este.",
                      "fecho": {"pergunta": "Quer ver mais como este...?", "cta": "Siga para mais"}})
    # um gancho/fecho no meio vira citacao (so o primeiro e o ultimo sao esses)
    for i in range(1, len(cenas) - 1):
        if cenas[i]["tipo"] in ("gancho", "fecho"):
            r = cena_reserva(cenas[i], rnd)
            if r:
                cenas[i] = r
    # no maximo 2 cenas com foto (economiza a cota gratuita de imagens)
    fotos = 0
    for i in range(1, len(cenas) - 1):
        cl = cenas[i].get("cena") or {}
        if cenas[i]["tipo"] == "classica" and cl.get("tipo") == "imagem":
            fotos += 1
            if fotos > 2:
                r = cena_reserva(cenas[i], rnd)
                if r:
                    cenas[i] = r
    cenas = aplicar_verdade(cenas, base, fatos_usuario, rnd)
    pals = [p for p in (estilo.get("paleta") or ["ouro"]) if p not in recentes_paleta] or \
           [p for p in PALETAS_TODAS if p not in recentes_paleta] or ["ouro"]
    paleta = rnd.choice(pals)
    out = {"titulo": s(dados_llm.get("titulo") or tema, 80), "fps": fps, "paleta": paleta, "semente": rnd.randrange(1, 9999),
           "estilo": estilo["nome"], "marca": marca, "narrado": True, "cenas": cenas}
    if base and base.get("fatos"):
        out["fontes"] = fontes_do_video(cenas, base) or sorted({f["fonte"] for f in base["fatos"]})[:3]
        out["data_dados"] = base.get("data", "")
        out["sensivel"] = bool(base.get("sensivel"))
    return out


def sem_foto_faltando(dados, pasta_public):
    """Cena com foto que nao foi gerada (cota da Cloudflare, erro): vira frase de destaque."""
    import random as _r
    n = 0
    for i, c in enumerate(dados["cenas"]):
        if c.get("video"):
            continue
        cl = c.get("cena") if c["tipo"] == "classica" else None
        if cl and cl.get("tipo") == "imagem" and not (cl.get("imagem") and (Path(pasta_public) / cl["imagem"]).exists()):
            r = cena_reserva(c, _r.Random(i))
            if r:
                dados["cenas"][i] = r
                n += 1
    return n


# ---------------------------------------------------------------------
# modo sem IA: monta um roteiro variado so com o tema (nunca trava)
# ---------------------------------------------------------------------
def sem_ia(tema, estilo, rnd):
    pal = [p for p in re.findall(r"\w+", tema) if len(p) > 3] or [tema]
    base = s(tema, 40)
    c = [
        {"tipo": "gancho", "fantasma": fantasma_ok(pal[0], tema), "etiqueta": {"texto": base.upper()[:24], "sub": "VOCÊ SABIA?"},
         "manchete": ["**" + base.upper()[:22] + "**", "o que *ninguém* conta"]},
        {"tipo": "rajada", "manchete": ["5 coisas *rápidas*"],
         "rajada": [{"icone": i, "texto": t} for i, t in rnd.sample(
             [("Search", "PESQUISE"), ("Scale", "COMPARE"), ("ShieldCheck", "CONFIRA"), ("Clock", "ESPERE"),
              ("Lightbulb", "PENSE"), ("Eye", "OBSERVE"), ("Target", "FOQUE")], 5)]},
        {"tipo": "checklist", "manchete": ["antes de *decidir*"], "checklist": ["Pesquise", "Compare", "Confirme"]},
        {"tipo": "citacao", "manchete": ["lembre-se"], "citacao": {"texto": "Quem entende o assunto não cai em armadilha.", "autor": ""}},
        {"tipo": "fecho", "fecho": {"pergunta": f"Você está pronto... para dominar {base.lower()}?", "cta": "Siga para mais"}},
    ]
    return {"titulo": base, "cenas": c}
