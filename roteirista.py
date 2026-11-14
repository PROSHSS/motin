"""
Roteirista em etapas, a prova de invencao:
  1) PONTOS: a IA transforma os FATOS (com fonte e data) em 8-10 pontos distintos. Cada ponto traz a
     evidencia (trecho copiado do fato). Ponto sem evidencia valida e descartado.
  2) PLANO: um programa (nao a IA) escolhe o tipo de cena de cada ponto, sem repetir e com muitas fotos.
  3) CENAS: a IA preenche cada cena (textos curtos). Um verificador confere palavras e numeros na tela.
  4) JUIZ (temas serios): a IA confere se cada frase esta 100% apoiada pela evidencia.
O que nao passa e trocado por uma cena segura feita so com as palavras da propria narracao.
"""
import json
import random
import re
import unicodedata

import requests

import showcase_gen as G

OLLAMA_URL = "http://localhost:11434"

SERIO_RE = re.compile(
    r"eleic|eleit|candidat|president|governo|governador|prefeit|partido|politic|congresso|senad|deputad|\bstf\b|\btse\b|"
    r"\blula\b|bolsonaro|justica|justiça|crime|assassin|morte|morreu|guerra|terror|ataque|doenca|doença|cancer|câncer|"
    r"vacina|remedio|remédio|saude|saúde|suicid|depress|religi|racis|policia|polícia|preso|prisao|prisão|investiment|"
    r"\bacoes\b|ações|bolsa de valores|bitcoin|cripto|aposta|\bbets?\b|imposto|aposentad|\binss\b|previd|tragedia|tragédia|"
    r"acidente|epidemia|pandemia|covid|dengue|abuso|violencia|violência|armas?\b", re.I)
PRECO_RE = re.compile(r"pre[cç]o|desconto|oferta|promo[cç]|black friday|compra|loja|cupom|frete|parcel", re.I)
SAUDE_RE = re.compile(r"saude|saúde|doenca|doença|remedio|remédio|vacina|cancer|câncer|dieta|sintoma|tratamento", re.I)
FINANCA_RE = re.compile(r"invest|acoes|ações|bolsa|bitcoin|cripto|aposta|\bbets?\b|renda fixa|tesouro|dolar|dólar|selic", re.I)

STOP = set("""para como mais isso esse essa esta este mesmo muito sobre pelo pela entre quando onde tambem também ainda
porque qual quais seus suas nossa nosso voce você voces vocês sera será foram sendo desde depois antes apenas todo toda
todos todas cada outro outra outros outras algo alguem alguém nada tudo assim entao então pode podem deve devem fazer feito
faz tem tinha tinham ser estar esta estao estão vai vao vão hoje agora aqui ali sempre nunca ja já bem melhor maior menor
seguir siga mais conteudo conteúdo veja saiba confira descubra entenda passo dica dicas sinais sinal exemplo ilustrativo
fonte antes durante depois cuidado atencao atenção importante""".split())


def norm(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def palavras(t, minimo=4):
    return [w for w in norm(t).split() if len(w) >= minimo and not w.isdigit()]


def numeros(t):
    out = set()
    for m in re.findall(r"\d+(?:[.,]\d+)*", t or ""):
        out.add(re.sub(r"[.,]", "", m))
    return out


def similares(a, b):
    A, B = set(palavras(a)), set(palavras(b))
    return bool(A and B) and len(A & B) / len(A | B) > 0.5


# ---------------------------------------------------------------------
# chamada a IA
# ---------------------------------------------------------------------
def llm(prompt, schema, modelo, temperatura=0.5, ctx=6144, predict=900, tentativas=2):
    ultimo = None
    for i in range(tentativas):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json={
                "model": modelo, "stream": False, "think": False,
                "options": {"num_ctx": ctx, "temperature": temperatura + 0.15 * i, "num_predict": predict},
                "format": schema, "messages": [{"role": "user", "content": prompt}]}, timeout=1800)
            r.raise_for_status()
            return json.loads(r.json()["message"]["content"])
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            ultimo = e
    raise RuntimeError(f"Ollama nao respondeu direito: {ultimo}")


# ---------------------------------------------------------------------
# etapa 1: pontos
# ---------------------------------------------------------------------
SCHEMA_PONTOS = {
    "type": "object",
    "properties": {
        "titulo": {"type": "string"},
        "pontos": {"type": "array", "items": {"type": "object", "properties": {
            "narracao": {"type": "string"},
            "fatos": {"type": "array", "items": {"type": "string"}},
            "evidencia": {"type": "string"},
        }, "required": ["narracao", "fatos", "evidencia"]}},
    },
    "required": ["titulo", "pontos"],
}


def prompt_pontos(tema, fatos_txt, serio, tem_fatos, n):
    base = f"""Voce e roteirista de videos curtos (TikTok/Reels) em portugues do Brasil: claro, humano, bem contado e RESPEITOSO.
Tema: {tema}
{"FATOS VERIFICADOS (cada um com numero, fonte e data). Use SOMENTE eles:" if tem_fatos else "Nao ha fatos pesquisados: escreva apenas explicacoes gerais, verdadeiras e conhecidas, sem numeros, datas, nomes proprios, estatisticas ou pesquisas."}
{fatos_txt if tem_fatos else ""}

Escreva {n} PONTOS, em ordem, como uma pequena historia com comeco, meio e fim:
1. GANCHO: uma pergunta ou frase curta e intrigante (ate 12 palavras) que faz a pessoa querer ouvir ate o fim. Nao afirme nada que nao esteja nos fatos.
2. CONTEXTO: situe o assunto em uma frase simples (o que e, por que importa agora).
3 a {n - 3}. DESENVOLVIMENTO: cada ponto traz UMA ideia nova e concreta, na ordem logica (o que aconteceu -> como funciona -> o que muda na pratica -> o que ainda nao se sabe ou o que fica de fora). Nunca repita assunto, palavra-chave ou frase.
{n - 2}. O QUE ISSO SIGNIFICA: resuma o principal para a vida da pessoa, com cuidado para nao prometer nada.
{n}. FECHO: pergunta final ou convite a seguir (ate 12 palavras).
ESTILO DA NARRACAO: linguagem falada e natural, como uma pessoa explicando a um amigo; frases de 10 a 22 palavras, no maximo 2 frases por ponto; use conectores ("mas", "por isso", "ou seja", "na pratica", "e o mais importante"); verbos ativos; sem jargao, sem emojis, sem lista telegrafica, sem repetir o inicio das frases. Escreva numeros por extenso como se fala.
{"Cada ponto do meio: fatos = lista dos ids usados (ex [\"F2\"]); evidencia = copie EXATAMENTE (letra por letra) um trecho do fato que sustenta a narracao. A narracao so pode conter numeros, nomes e datas que aparecem nesse trecho; explicar com palavras simples e permitido, acrescentar dado novo nao. No gancho e no fecho deixe fatos=[] e evidencia=\"\"." if tem_fatos else "fatos=[] e evidencia=\"\" em todos os pontos."}
{"TEMA SERIO: neutro e factual, sem opiniao, sem adjetivos de julgamento, sem previsao, sem tomar partido, sem culpar ninguem. Atribua a informacao a fonte quando fizer sentido (\"segundo ...\"). Nao cite nada que nao esteja nos fatos." if serio else "Nunca invente numeros, pesquisas, nomes ou datas."}
Tambem devolva titulo (ate 8 palavras, chamativo e honesto)."""
    return base


def validar_pontos(brutos, fatos, serio, tem_fatos, tema):
    """Descarta o que nao tem evidencia real; confere numeros e nomes."""
    idx = {f["id"]: f for f in fatos}
    todos_txt = " ".join(f["texto"] for f in fatos) + " " + tema
    permit_num = numeros(todos_txt)
    permit_norm = norm(todos_txt)
    permit_pal = set(norm(todos_txt).split())
    out = []
    ocupados = []
    motivos = []
    n = len(brutos)
    for i, p in enumerate(brutos):
        nar = G.s(p.get("narracao"), 300)
        if not nar:
            continue
        extremo = i == 0 or i == n - 1
        if re.search(r"[Ѐ-ӿ぀-ヿ一-鿿؀-ۿ]", nar):
            motivos.append(f"ponto {i+1}: caracteres estranhos")
            continue
        ids = [x for x in (p.get("fatos") or []) if x in idx]
        evid = G.s(p.get("evidencia"), 300)
        if tem_fatos and not extremo:
            if not ids or not evid:
                motivos.append(f"ponto {i+1}: sem evidencia")
                continue
            fonte_txt = norm(" ".join(idx[x]["texto"] for x in ids))
            if norm(evid).strip() not in fonte_txt:
                motivos.append(f"ponto {i+1}: evidencia nao confere com o fato")
                continue
            base_nums = numeros(evid)
        else:
            base_nums = set()
        # numeros da narracao precisam estar na evidencia (ou nos fatos, no gancho/fecho)
        for nm in numeros(nar):
            if extremo:
                ok = nm in permit_num
            elif tem_fatos:
                ok = nm in base_nums
            else:
                ok = (not serio) and len(nm) <= 2 and int(nm) <= 12
            if not ok:
                motivos.append(f"ponto {i+1}: numero {nm} fora dos fatos")
                break
        else:
            # nomes proprios / siglas
            sentenca_ini = True
            ruim = None
            for tok in re.findall(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9'-]*|[.!?]", nar):
                if tok in ".!?":
                    sentenca_ini = True
                    continue
                if tok.isdigit():
                    sentenca_ini = False
                    continue
                cap = tok[0].isupper() and len(tok) >= 3
                sigla = tok.isupper() and len(tok) >= 2
                if (cap and not sentenca_ini) or sigla:
                    if norm(tok).strip() not in permit_pal:
                        ruim = tok
                        break
                sentenca_ini = False
            if ruim and (tem_fatos or serio):
                motivos.append(f"ponto {i+1}: nome '{ruim}' nao esta nos fatos")
                continue
            if any(similares(nar, o) for o in ocupados):
                motivos.append(f"ponto {i+1}: repete outro ponto")
                continue
            ocupados.append(nar)
            out.append({"narracao": nar, "fatos": ids, "evidencia": evid, "extremo": extremo})
    return out, motivos


def etapa_pontos(tema, fatos, serio, modelo, n=9, log=print):
    tem_fatos = bool(fatos)
    fatos_txt = "\n".join(f"[{f['id']}] ({f['fonte']}, {f['data']}) {f['texto']}" for f in fatos)
    melhor = None
    for tentativa in range(3):
        bruto = llm(prompt_pontos(tema, fatos_txt, serio, tem_fatos, n), SCHEMA_PONTOS, modelo,
                    temperatura=0.35 + 0.15 * tentativa, predict=2200)
        pontos, motivos = validar_pontos(bruto.get("pontos", []), fatos, serio, tem_fatos, tema)
        for m in motivos:
            log(f"   descartado - {m}")
        if melhor is None or len(pontos) > len(melhor[1]):
            melhor = (bruto, pontos)
        meio = [p for p in pontos if not p["extremo"]]
        if len(pontos) >= 6 and len(meio) >= 4:
            break
    bruto, pontos = melhor
    if len(pontos) < 5:
        raise RuntimeError("poucos pontos com evidencia valida (os fatos pesquisados nao bastam para um video completo)")
    # gancho e fecho garantidos
    if not pontos[0]["extremo"]:
        pontos.insert(0, {"narracao": G.s(f"Vamos entender: {tema}?", 120),
                          "fatos": [], "evidencia": "", "extremo": True})
    if not pontos[-1]["extremo"]:
        pontos.append({"narracao": "Quer entender mais sobre isso? Siga para ver os próximos vídeos.", "fatos": [], "evidencia": "", "extremo": True})
    return G.s(bruto.get("titulo") or tema, 80), pontos


# ---------------------------------------------------------------------
# etapa 2: plano (tipos de cena) -- decidido por programa, sem repetir
# ---------------------------------------------------------------------
UI_TIPOS = ["rajada", "checklist", "comparacao", "alerta", "linha_tempo", "citacao", "contador", "ranking", "grafico",
            "processo", "lupa", "celular"]
CLASSICAS_SEGURAS = ["documento", "numero_gigante"]  # as classicas "vazias" (texto sobre creme/verde) foram retiradas: pouco conteudo, cara de ar


def planejar(pontos, estilo, rnd, max_fotos, serio, tema, tem_fatos):
    n = len(pontos)
    usados = {}
    plano = []
    fotos = 0
    pref = set(estilo.get("preferir", []))
    evita = set(estilo.get("evitar", []))
    classicas_pref = estilo.get("classicas") or CLASSICAS_SEGURAS
    preco = bool(PRECO_RE.search(tema))
    for i, p in enumerate(pontos):
        if i == n - 1:
            plano.append(("fecho", None))
            continue
        tem_num = bool(numeros(p["evidencia"]))
        cand = {}
        # fotos (sempre validas)
        if fotos < max_fotos:
            for t in G.FOTOS:
                cand[t] = 3.0
        # perfil documental (nome/numero real + foto): no maximo 2 por video, nunca grudadas
        if fotos < max_fotos and i > 0 and usados.get("fato_real", 0) < (2 if n >= 9 else 1) and "fato_real" not in [x[0] for x in plano[-3:]]:
            nome_, num_ = candidato_fato_real(p)
            peso_ = (2.5 if nome_ else 0) + (2.5 if num_ else 0)
            if peso_:
                cand["fato_real"] = 1.5 + peso_
        # documento (o que diz a fonte): so quando ha fato com fonte, 1 por video, longe do perfil
        if tem_fatos and i > 0 and p["fatos"] and p["evidencia"] and len(p["evidencia"]) <= 220 and usados.get("fato_documento", 0) < 1 \
                and not any(x[0] in ("fato_real", "fato_documento") for x in plano[-2:]):
            cand["fato_documento"] = 3.5 if serio else 2.5
        # cenas de variedade (motion): programa monta so com a narracao; entram quando o texto do ponto permite
        for t in G.VARIEDADE:
            if t == "foto_moldura" and fotos >= max_fotos:
                continue
            if i == 0 and t not in ("glitch", "cartaz"):
                continue
            if pode_variedade(t, p, tema):
                cand[t] = 0.3 if t in evita else (4.2 if t in pref else 2.6)
        # cenas Showcase de interface
        for t in UI_TIPOS:
            w = 2.2 if t in pref else 1.0
            if t in evita:
                w = 0.15
            if t in ("contador",) and not tem_num:
                continue
            if t in ("ranking", "grafico") and len(numeros(p["evidencia"])) < 3:
                continue
            if t in ("processo", "lupa") and not preco:
                continue
            if t == "celular" and serio:
                continue
            if t == "alerta" and serio:
                continue
            cand[t] = w
        # cenas classicas (no mesmo plano)
        for c in CLASSICAS_SEGURAS:
            if c == "numero_gigante" and not tem_num:
                continue
            w = 2.0 if c in classicas_pref else 0.8
            cand["c_" + c] = w
        if i == 0:
            cand = {k: v for k, v in cand.items() if k in ("foto_persianas", "foto_recorte", "foto_hero", "citacao", "glitch", "cartaz")}
            cand["gancho"] = 3.5
        # regras de variedade
        ult = [x[0] for x in plano[-3:]]
        for k in list(cand):
            if k in ult:
                cand.pop(k)
            elif usados.get(k, 0) >= (1 if k.startswith("foto_") or k.startswith("c_") else 1):
                cand.pop(k)
        # no maximo 2 fotos seguidas e 2 nao-fotos seguidas
        if len(plano) >= 2:
            a, b = plano[-1][0], plano[-2][0]
            if a.startswith("foto_") and b.startswith("foto_"):
                cand = {k: v for k, v in cand.items() if not k.startswith("foto_")} or cand
            if not a.startswith("foto_") and not b.startswith("foto_") and fotos < max_fotos:
                cand = {k: v for k, v in cand.items() if k.startswith("foto_")} or cand
        if not cand:
            cand = {"foto_hero": 1} if fotos < max_fotos else {"citacao": 1}
        chaves = list(cand)
        escolhido = rnd.choices(chaves, weights=[cand[k] for k in chaves])[0]
        usados[escolhido] = usados.get(escolhido, 0) + 1
        if escolhido.startswith("foto_") or escolhido == "fato_real":
            fotos += 1
        if escolhido.startswith("c_"):
            plano.append(("classica", escolhido[2:]))
        else:
            plano.append((escolhido, None))
    # garante pelo menos UMA cena de perfil documental quando algum ponto tem nome/numero real
    if max_fotos > 0 and n >= 6 and not any(t == "fato_real" for t, _ in plano):
        melhores = []
        for i, p in enumerate(pontos):
            if i == 0 or i >= n - 1:
                continue
            nome_, num_ = candidato_fato_real(p)
            if nome_ or num_:
                melhores.append(((2 if nome_ else 0) + (2 if num_ else 0) + (1 if 2 <= i <= n - 3 else 0), i))
        if melhores:
            melhores.sort(reverse=True)
            i = melhores[0][1]
            plano[i] = ("fato_real", None)
    # e pelo menos UM documento (o que diz a fonte) quando ha fatos com fonte
    if tem_fatos and n >= 6 and not any(t == "fato_documento" for t, _ in plano):
        opcoes = []
        for i, p in enumerate(pontos):
            if i == 0 or i >= n - 1 or not p["fatos"] or not p["evidencia"] or len(p["evidencia"]) > 220:
                continue
            viz = [plano[j][0] for j in (i - 1, i + 1) if 0 <= j < n]
            if "fato_real" in viz or plano[i][0] == "fato_real":
                continue
            nome_, num_ = candidato_fato_real(p)
            opcoes.append(((2 if num_ else 0) + (1 if nome_ else 0) + (1 if serio else 0), i))
        if opcoes:
            opcoes.sort(reverse=True)
            plano[opcoes[0][1]] = ("fato_documento", None)
    return plano


# ---------------------------------------------------------------------
# etapa 3: preencher cada cena + verificar
# ---------------------------------------------------------------------
TIPO_CHAVES = {
    "gancho": ["fantasma", "etiqueta"], "celular": ["notificacoes", "fantasma"], "lupa": ["lupa"], "processo": ["processo"],
    "grafico": ["grafico"], "rajada": ["rajada"], "checklist": ["checklist"], "comparacao": ["comparacao"],
    "contador": ["contador"], "ranking": ["ranking"], "linha_tempo": ["linha_tempo"], "alerta": ["alerta"],
    "citacao": ["citacao"], "fecho": ["fecho"], "classica": ["classe", "destaque", "elementos"],
}
for _f in G.FOTOS:
    TIPO_CHAVES[_f] = ["chips", "rotulo", "fantasma"]

FOTO_REGRA = ('- manchete: 1 ou 2 linhas curtas (ate 24 letras cada) com palavras DA NARRACAO. Marque **PALAVRA** (letra grossa) em 1 palavra e *palavra* (serifada) em outra.\n'
              '- chips: 0 a 3 etiquetas {texto: ate 3 palavras tiradas da evidencia, valor: SO se for um numero que esta na evidencia}.\n'
              '- rotulo: frase curta (ate 6 palavras) da narracao.\n'
              '- fantasma: UMA palavra MAIUSCULA (ate 8 letras) que esta na narracao.')


def regra_do_tipo(tipo, classe):
    txt = G.REGRAS.replace("{{", "{").replace("}}", "}")
    if tipo in G.FOTOS:
        return FOTO_REGRA
    linhas = []
    for ln in txt.splitlines():
        if ln.startswith("- manchete") or ln.startswith(f"- {tipo}:") or (classe and ln.startswith(f'- classe "{classe}"')):
            linhas.append(ln)
    if tipo == "classica" and not any(l.startswith("- classe") for l in linhas):
        linhas.append(f'- classe "{classe}": destaque (frase/palavra curta) e elementos conforme o tipo.')
    return "\n".join(linhas)


def schema_cena(tipo):
    props = G.SCHEMA["properties"]["cenas"]["items"]["properties"]
    keys = ["manchete"] + TIPO_CHAVES.get(tipo, [])
    return {"type": "object", "properties": {k: props[k] for k in keys if k in props}, "required": ["manchete"]}


def prompt_cena(tipo, classe, ponto, fatos_ids_txt, serio):
    return f"""Voce e diretor de motion design de um video de TikTok em portugues do Brasil.
Monte o visual de UMA cena do tipo "{tipo}"{(' (classe "' + classe + '")') if classe else ''}.
Narracao da cena (falada): {ponto['narracao']}
Evidencia (trecho dos fatos): {ponto['evidencia'] or '(nenhuma)'}
{fatos_ids_txt}
REGRAS ABSOLUTAS:
- Todo texto na tela usa APENAS palavras e numeros que aparecem na narracao ou na evidencia. Nao invente nada.
- Textos MUITO curtos (poucas palavras, sem frases longas), sem emojis, em portugues correto.
{"- Tema serio: nada de humor, opiniao, exagero ou julgamento." if serio else ""}
COMO PREENCHER:
{regra_do_tipo(tipo, classe)}
Devolva somente os campos pedidos."""


def textos_da_cena(c):
    """Todos os textos exibidos na tela (para conferir)."""
    out = []

    def ach(v):
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            for x in v:
                ach(x)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k not in ("icone", "tipo", "vencedor", "gatilho", "imagem"):
                    ach(x)
    for k, v in c.items():
        if k in ("tipo", "duracao", "narracao", "foto", "acento", "fonte", "variante", "fatos", "evidencia", "video", "credito_video", "motion"):
            continue
        if k == "manchete":
            for linha in v:
                for parte in linha:
                    out.append(parte["t"])
        elif k == "cena":
            ach({kk: vv for kk, vv in v.items() if kk not in ("narracao", "tipo", "imagem")})
        else:
            ach(v)
    return out


def linta(c, ponto, tema, serio, tem_fatos, ilustrativo):
    """Devolve (ok, motivo). Todas as palavras/numeros da tela devem vir da narracao, evidencia ou tema."""
    base_txt = f"{ponto['narracao']} {ponto['evidencia']} {tema}"
    base = set(norm(base_txt).split())
    pref = {w[:5] for w in base if len(w) >= 4}
    nums_ok = numeros(base_txt)
    desconhecidas, total = [], 0
    for t in textos_da_cena(c):
        if re.search(r"[Ѐ-ӿ぀-ヿ一-鿿؀-ۿ]", t):
            return False, "caracteres estranhos"
        for nm in numeros(t):
            if nm not in nums_ok and not ilustrativo and not (not serio and not tem_fatos and nm.isdigit() and int(nm) <= 12):
                return False, f"numero {nm} nao esta na evidencia"
        for w in norm(t).split():
            if len(w) < 4 or w.isdigit() or w in STOP:
                continue
            total += 1
            if w not in base and w[:5] not in pref:
                desconhecidas.append(w)
            if len(w) > 5 and not re.search(r"[aeiou]", w):
                return False, f"palavra sem sentido: {w}"
    limite = 0 if serio else (0.25 if tem_fatos else 0.4)
    if c.get("tipo") in ("fecho", "gancho"):
        limite = 0.5
    if total and len(desconhecidas) / total > limite:
        return False, "palavras fora da narracao: " + ", ".join(desconhecidas[:4])
    return True, ""


def manchete_da_narracao(nar, rnd):
    pal = re.findall(r"[A-Za-zÀ-ÿ0-9%$,.-]+", re.sub(r"[?!.]+$", "", nar))
    _p = G._PENDENTES
    fortes = [w for w in pal if len(w) > 3]
    n1 = pal[: min(3, len(pal))]
    resto = pal[len(n1): len(n1) + 4]
    while n1 and len(n1) > 1 and n1[-1].lower().strip(",.") in _p:
        resto.insert(0, n1.pop())
    while resto and resto[-1].lower().strip(",.") in _p:
        resto.pop()
    l1 = " ".join(n1)
    if len(l1) > 22:
        l1 = " ".join(n1[:2])
        resto = pal[2: 6]
    linhas = [f"**{l1.upper()}**"] if l1 else []
    if resto:
        r = " ".join(resto)
        ult = resto[-1]
        linhas.append(r[: len(r) - len(ult)] + f"*{ult}*" if len(resto) > 1 else f"*{ult}*")
    return linhas or [f"**{(fortes[:1] or ['AGORA'])[0].upper()}**"]


def cena_segura(ponto, rnd, usar_foto, i, evitar=()):
    """Cena sem risco: so usa a narracao. Foto (se houver) ou texto cinetico."""
    nar = ponto["narracao"]
    man = manchete_da_narracao(nar, rnd)
    if usar_foto:
        opcoes = [t for t in G.FOTOS if t not in evitar] or list(G.FOTOS)
        tipo = rnd.choice(opcoes)
        return {"tipo": tipo, "manchete": man, "chips": [], "rotulo": "", "narracao": nar}
    # sem foto: cena de citacao com a propria narracao (tema escuro, texto grande). Nunca uma cena de foto sem foto.
    partes = [p.strip() for p in re.split(r"[;:.?!]\s*", nar) if p.strip()]
    frase = next((p for p in partes if 3 <= len(p.split()) and len(p) <= 90), "")
    if not frase:
        pal_ = (partes[0] if partes else nar).split()[:12]
        while len(pal_) > 2 and pal_[-1].lower().strip(",") in G._PENDENTES:
            pal_.pop()
        frase = " ".join(pal_)
    return {"tipo": "citacao", "manchete": man, "citacao": {"texto": G.s(frase.rstrip(","), 90), "autor": ""}, "narracao": nar}


# ---------------------------------------------------------------------
# FATO REAL (perfil documental): montada por programa, sem IA, direto da narracao e da evidencia
# ---------------------------------------------------------------------
_CONECT = {"de", "da", "do", "das", "dos", "e"}


def nome_proprio(texto):
    """Maior sequencia de palavras com inicial maiuscula (ex.: 'Congresso Nacional', 'Banco Central do Brasil')."""
    toks = re.findall(r"[A-Za-zÀ-ÿ0-9'-]+|[.!?]", texto or "")
    melhor, atual, ini = "", [], True
    pend = []

    def fecha():
        nonlocal melhor, atual, pend
        seq = atual[:]
        if seq and (len(seq) >= 2 or not seq_inicio[0]):
            txt = " ".join(seq)
            if len(txt) > len(melhor):
                melhor = txt
        atual, pend = [], []
    seq_inicio = [True]
    for t in toks:
        if t in ".!?":
            fecha()
            ini = True
            continue
        cap = t[0].isupper() and len(t) >= 3 and norm(t) not in STOP
        if cap:
            if not atual:
                seq_inicio[0] = ini
            if pend:
                atual.extend(pend)
                pend = []
            atual.append(t)
        elif t.lower() in _CONECT and atual:
            pend.append(t)
        else:
            fecha()
        ini = False
    fecha()
    return melhor[:34]


_NUM_RE = re.compile(r"(R\$|US\$|\$)?\s*(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?\s*(%|por cento|mil(?:h[õo]es|h[ãa]o)|bilh[õo]es|bilh[ãa]o|trilh[õo]es|trilh[ãa]o|mil)?", re.I)


def numero_destaque(evidencia, narracao):
    """Escolhe UM numero da evidencia que tambem aparece na narracao (dinheiro, porcentagem, quantidade)."""
    melhor = None
    nar_nums = numeros(narracao)
    for m in _NUM_RE.finditer(evidencia or ""):
        pre, inteiro, dec, suf = m.group(1), m.group(2), m.group(3), m.group(4)
        bruto = re.sub(r"[.,]", "", inteiro + (dec or ""))
        if bruto not in nar_nums:
            continue
        ano = len(inteiro) == 4 and 1900 <= int(inteiro) <= 2100 and not pre and not suf
        if ano:
            continue
        if not (pre or suf or len(inteiro.replace('.', '')) >= 3):
            continue
        peso = (2 if pre else 0) + (2 if suf else 0) + (1 if len(inteiro) > 2 else 0)
        if melhor is None or peso > melhor[0]:
            valor = float(inteiro.replace(".", "") + ("." + dec if dec else ""))
            sufixo = ""
            if suf:
                sufixo = "%" if suf.lower() in ("%", "por cento") else " " + suf.lower()
            prefixo = {"r$": "R$ ", "us$": "US$ ", "$": "$ "}.get((pre or "").lower(), "")
            melhor = (peso, {"prefixo": prefixo, "valor": valor, "decimais": len(dec or ""), "sufixo": sufixo, "rotulo": ""})
    return melhor[1] if melhor else None


def quebrar_linhas(texto, largura=34, maximo=5):
    sentencas = re.split(r"(?<=[.!?])\s+", texto.strip())
    def envolver(t):
        out, atual = [], ""
        for w in t.split():
            if len(atual) + len(w) + 1 > largura and atual:
                out.append(atual)
                atual = w
            else:
                atual = (atual + " " + w).strip()
        if atual:
            out.append(atual)
        return out
    acumulado = []
    for sent in sentencas:
        cand = envolver(" ".join(acumulado + [sent]) if False else (" ".join(x for x in [" ".join(acumulado)] if x) + " " + sent).strip())
        if len(cand) <= maximo:
            acumulado.append(sent)
        else:
            break
    if acumulado:
        return envolver(" ".join(acumulado))
    linhas = envolver(sentencas[0])[:maximo]
    # cortou no meio da frase: termina na ultima linha completa sem palavra solta
    return linhas


def candidato_fato_real(ponto):
    nome = nome_proprio(ponto["narracao"]) or nome_proprio(ponto["evidencia"])
    num = numero_destaque(ponto["evidencia"], ponto["narracao"])
    return nome, num


def montar_fato_real(ponto, tema, rnd):
    nome, num = candidato_fato_real(ponto)
    titulo = nome or G.s(tema, 30)
    c = {"tipo": "fato_real", "titulo": titulo, "linhas": quebrar_linhas(ponto["narracao"]), "narracao": ponto["narracao"]}
    if num:
        c["numero"] = num
    return G.sanear_cena(c, rnd, {})


def montar_documento(ponto, fatos_idx):
    """Folha com o texto do fato (da fonte), marca-texto nos numeros e nomes. Sem IA."""
    ids = [x for x in ponto["fatos"] if x in fatos_idx]
    if not ids:
        return None
    fato = fatos_idx[ids[0]]
    texto = fato["texto"] if len(fato["texto"]) <= 230 else ponto["evidencia"]
    texto = re.sub(r"\s+", " ", texto).strip()
    if not texto or len(texto) > 230:
        return None
    dest = []
    for m in _NUM_RE.finditer(texto):
        t = m.group(0).strip()
        if re.search(r"\d", t) and (m.group(1) or m.group(4) or len(re.sub(r"\D", "", t)) >= 3) and t not in dest:
            dest.append(t)
    nome = nome_proprio(texto)
    if nome and nome in texto and nome not in dest:
        dest.append(nome)
    manual = fato.get("tipo") in ("manual", "usuario")
    nome_fonte = G.s(re.sub(r"\s*\(.*$", "", fato["fonte"]), 50) or "Fonte"
    data = fato.get("data", "")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", data or ""):
        data = f"{data[8:10]}/{data[5:7]}/{data[:4]}"
    c = {"tipo": "fato_documento", "narracao": ponto["narracao"], "fatos": ids,
         "documento": {"fonte": nome_fonte, "data": data, "trecho": texto, "destaques": dest[:4], "selo": "INFORMADO" if manual else "CONFERIDO"}}
    return G.sanear_cena(c, random.Random(1), {})


# ---------------------------------------------------------------------
# CENAS DE VARIEDADE (motion): tudo montado por programa a partir da narracao/evidencia
# ---------------------------------------------------------------------
def _frases(texto):
    return [x.strip() for x in re.split(r"(?<=[.!?;])\s+", re.sub(r"\s+", " ", texto or "").strip()) if x.strip()]


def _orac(texto):
    """Pedacos de frase inteiros (separados por virgula, ponto e virgula ou ' e ') com 2 a 5 palavras."""
    out = []
    for fr in _frases(texto):
        for pe in re.split(r"\s*[,;:]\s*|\s+e\s+|\s+mas\s+|\s+porque\s+", fr):
            pe = pe.strip(" .!?")
            n = len(pe.split())
            if 2 <= n <= 6 and len(pe) <= 34 and pe.split()[-1].lower() not in G._PENDENTES and pe.split()[0].lower() not in _CONECT | {"que", "se", "o", "a", "os", "as"}:
                out.append(pe[0].upper() + pe[1:])
    return out


_FRACAS = {"quem", "paga", "pagar", "cento", "segundo", "informou", "disse", "fica", "ficar", "muita", "muito", "gente", "ainda", "quer", "alem", "além"}


def _inteiro(texto, largura, maximo):
    """Quebra em linhas SO se a(s) frase(s) cabem inteiras (nunca termina no meio de uma frase)."""
    lin = quebrar_linhas(texto, largura, maximo)
    if not lin or not " ".join(lin).rstrip()[-1:] in ".!?":
        return None
    return lin


def _palavras_chave(texto, n=5, maxlen=14):
    vistas, out = set(), []
    for w in re.findall(r"\d+(?:[.,]\d+)*%?|[A-Za-zÀ-ÿ$]+", texto or ""):
        k = norm(w).strip()
        if k in _FRACAS:
            continue
        if (len(k) >= 4 or any(ch.isdigit() for ch in w)) and k not in STOP and k not in vistas and len(w) <= maxlen:
            vistas.add(k)
            out.append(w)
    return out[:n]


def montar_cartaz(ponto, tema, rnd):
    pal = _palavras_chave(ponto["narracao"], 5)
    if len(pal) < 3:
        return None
    pal = [w.upper() for w in pal]
    idx = next((i for i, w in enumerate(pal) if any(ch.isdigit() for ch in w)), None)
    if idx is None:
        idx = max(range(len(pal)), key=lambda i: len(pal[i]))
    return G.sanear_cena({"tipo": "cartaz", "palavras": pal, "realce": [idx], "narracao": ponto["narracao"], "fatos": ponto.get("fatos")}, rnd, {})


def montar_foto_moldura(ponto, tema, rnd):
    tags = [w.upper() for w in _palavras_chave(ponto["narracao"], 2, 14)]
    lin = _inteiro(ponto["narracao"], 28, 4)
    if len(tags) < 1 or not lin:
        return None
    return G.sanear_cena({"tipo": "foto_moldura", "tags": tags, "linhas": lin, "narracao": ponto["narracao"], "fatos": ponto.get("fatos")}, rnd, {})


def montar_busca(ponto, tema, rnd):
    nome = nome_proprio(ponto["narracao"]) or nome_proprio(ponto["evidencia"]) or G.s(tema, 40)
    base = [x for x in _frases(ponto["evidencia"]) if 12 <= len(x) <= 74]
    if len(base) < 2:
        base += [x for x in _frases(ponto["narracao"]) if 12 <= len(x) <= 74 and x not in base]
    base = [x.rstrip(".") for x in base][:3]
    if len(base) < 2 or not nome:
        return None
    return G.sanear_cena({"tipo": "busca", "consulta": nome, "resultados": base, "narracao": ponto["narracao"], "fatos": ponto.get("fatos")}, rnd, {})


def _destaque(ponto):
    num = re.search(r"(R\$\s?)?\d[\d.,]*\s?(%|mil|milh[õo]es|bilh[õo]es)?", ponto["narracao"])
    if num and len(num.group(0).strip()) >= 2:
        return num.group(0).strip()
    nome = nome_proprio(ponto["narracao"])
    if nome and len(nome) <= 22:
        return nome
    pal = _palavras_chave(ponto["narracao"], 8, 16)
    return max(pal, key=len) if pal else ""


def montar_pilula(ponto, tema, rnd):
    lin = _inteiro(ponto["narracao"], 24, 4)
    dest = _destaque(ponto)
    if len(lin) < 2 or not dest or dest.lower() not in " ".join(lin).lower():
        return None
    return G.sanear_cena({"tipo": "pilula", "linhas": lin, "destaque": dest, "narracao": ponto["narracao"], "fatos": ponto.get("fatos")}, rnd, {})


def montar_glitch(ponto, tema, rnd):
    dest = _destaque(ponto)
    lin = _inteiro(ponto["narracao"], 34, 3)
    if not dest or len(dest) > 14 or not lin:
        return None
    return G.sanear_cena({"tipo": "glitch", "palavra": dest, "linhas": lin, "narracao": ponto["narracao"], "fatos": ponto.get("fatos")}, rnd, {})


def montar_pasta(ponto, tema, rnd):
    car = _orac(ponto["narracao"])
    vistos, uni = set(), []
    for x in car:
        if norm(x) not in vistos:
            vistos.add(norm(x))
            uni.append(x)
    if len(uni) < 3:
        return None
    tit = nome_proprio(ponto["narracao"]) or G.s(tema, 28)
    return G.sanear_cena({"tipo": "pasta", "titulo": tit, "cartoes": uni[:3], "narracao": ponto["narracao"], "fatos": ponto.get("fatos")}, rnd, {})


MONTADORES_VAR = {"cartaz": montar_cartaz, "foto_moldura": montar_foto_moldura, "busca": montar_busca,
                  "pilula": montar_pilula, "glitch": montar_glitch, "pasta": montar_pasta}


def pode_variedade(tipo, ponto, tema):
    """Esta cena de variedade consegue ser montada com o texto deste ponto? (teste sem efeitos)"""
    try:
        return MONTADORES_VAR[tipo](ponto, tema, random.Random(1)) is not None
    except Exception:
        return False


def montar_cena(tipo, classe, ponto, i, tema, serio, tem_fatos, modelo, rnd, estilo, fatos_idx, log):
    if tipo == "fato_real":
        return montar_fato_real(ponto, tema, rnd)
    if tipo == "fato_documento":
        return montar_documento(ponto, fatos_idx)
    if tipo in MONTADORES_VAR:
        return MONTADORES_VAR[tipo](ponto, tema, rnd)
    ilustrativo = tipo in ("processo", "lupa", "celular") and not serio
    ids = ", ".join(f"[{x}] {fatos_idx[x]['texto']}" for x in ponto["fatos"] if x in fatos_idx)
    for tentativa in range(2):
        try:
            bruto = llm(prompt_cena(tipo, classe, ponto, ("Fatos: " + ids) if ids else "", serio), schema_cena(tipo), modelo,
                        temperatura=0.4 + 0.2 * tentativa, ctx=4096, predict=500)
        except RuntimeError:
            continue
        bruto["tipo"] = tipo
        bruto["narracao"] = ponto["narracao"]
        if classe:
            bruto["classe"] = classe
        c = G.sanear_cena(bruto, rnd, estilo)
        if not c:
            continue
        ok, motivo = linta(c, ponto, tema, serio, tem_fatos, ilustrativo)
        if ok:
            c["narracao"] = ponto["narracao"]
            if ilustrativo:
                c["fonte"] = "Exemplo ilustrativo"
            return c
        log(f"   cena {i+1} ({tipo}) recusada: {motivo}")
    return None


def fonte_do_ponto(ponto, fatos_idx):
    ids = [x for x in ponto["fatos"] if x in fatos_idx]
    if not ids:
        return ""
    f = fatos_idx[ids[0]]
    if f["tipo"] in ("manual", "usuario") or "Informado pelo autor" in f.get("fonte", ""):
        return ""
    nome = f["fonte"].split("(")[0].strip()
    return G.s(f"Fonte: {nome}" + (f" · {f['data']}" if f.get("data") else ""), 60)


# ---------------------------------------------------------------------
# etapa 4: juiz (temas serios)
# ---------------------------------------------------------------------
SCHEMA_JUIZ = {"type": "object", "properties": {"apoiada": {"type": "boolean"}, "motivo": {"type": "string"}}, "required": ["apoiada"]}


def juiz(ponto, fatos_idx, modelo):
    ids = [x for x in ponto["fatos"] if x in fatos_idx]
    if not ids:
        return True
    ev = " ".join(fatos_idx[x]["texto"] for x in ids)
    prompt = (f"Voce e um checador de fatos rigoroso.\nTRECHO FONTE: {ev}\nFRASE A CONFERIR: {ponto['narracao']}\n"
              "A frase esta TOTALMENTE apoiada pelo trecho, sem acrescentar nenhuma informacao, numero, nome, causa, "
              "consequencia, opiniao ou generalizacao que nao esteja no trecho? Responda apoiada=true somente se sim.")
    try:
        r = llm(prompt, SCHEMA_JUIZ, modelo, temperatura=0.0, ctx=2048, predict=120, tentativas=1)
    except RuntimeError:
        return False   # na duvida, nao usa
    return bool(r.get("apoiada"))


# ---------------------------------------------------------------------
# principal
# ---------------------------------------------------------------------
def classificar(tema):
    serio = bool(SERIO_RE.search(tema))
    aviso = ""
    if SAUDE_RE.search(tema):
        aviso = "Conteúdo informativo. Não substitui orientação de um profissional de saúde."
    elif FINANCA_RE.search(tema):
        aviso = "Conteúdo informativo. Não é recomendação de investimento."
    elif serio:
        aviso = "Informações de fontes públicas, conferidas na data indicada."
    return serio, aviso


def gerar(tema, fatos, estilo, modelo, rnd, max_fotos=6, serio=None, marca="", fps=30, log=print, n_pontos=11, modelo_juiz=None, max_imagens=0):
    serio_auto, aviso = classificar(tema)
    serio = serio_auto if serio is None else serio
    tem_fatos = bool(fatos)
    G.OPC["fatos"] = tem_fatos
    log(f"Modo: {'SERIO (verificacao maxima)' if serio else 'normal'} | fatos pesquisados: {len(fatos)}")
    titulo, pontos = etapa_pontos(tema, fatos, serio, modelo, n=n_pontos, log=log)
    fatos_idx = {f["id"]: f for f in fatos}
    if serio:
        log("Conferindo cada frase com o juiz de fatos...")
        mantidos = []
        for p in pontos:
            if p["extremo"] or juiz(p, fatos_idx, modelo_juiz or modelo):
                mantidos.append(p)
            else:
                log(f"   frase removida (nao apoiada): {p['narracao']}")
        if len(mantidos) >= 5:
            pontos = mantidos
    plano = planejar(pontos, estilo, rnd, max_fotos, serio, tema, tem_fatos)
    log("Plano de cenas: " + " > ".join((c or t) if t == "classica" else t for t, c in plano))
    fotos_usadas = sum(1 for t, _ in plano if t.startswith("foto_"))
    cenas = []
    for i, (p, (tipo, classe)) in enumerate(zip(pontos, plano)):
        c = montar_cena(tipo, classe, p, i, tema, serio, tem_fatos, modelo, rnd, estilo, fatos_idx, log)
        if c is None and tipo == "fecho":
            c = {"tipo": "fecho", "duracao": G.DUR["fecho"], "narracao": p["narracao"],
                 "fecho": {"pergunta": G.s(p["narracao"], 80), "cta": "Siga para mais"}}
        if c is None:
            usar_foto = fotos_usadas < max_fotos
            usados_tipos = [x["tipo"] for x in cenas] + [t for t, _ in plano[i:i + 2]]
            seg = cena_segura(p, rnd, usar_foto, i, usados_tipos)
            if seg.get("tipo") == "foto_recorte":
                seg["fantasma"] = G.fantasma_ok("", p["narracao"])
            c = G.sanear_cena(seg, rnd, estilo)
            if c is None:
                continue
            c["narracao"] = p["narracao"]
            if usar_foto and c["tipo"].startswith("foto_"):
                fotos_usadas += 1
        f = fonte_do_ponto(p, fatos_idx)
        if f and not c.get("fonte"):
            c["fonte"] = f
        c["evidencia"] = p["evidencia"]
        c["fatos"] = p["fatos"]
        cenas.append(c)
    # imagens de IA tambem como FUNDO das cenas animadas (como no modo classico): Showcase + cara de foto real
    n_img = sum(1 for c in cenas if c["tipo"].startswith("foto_") or c["tipo"] == "fato_real")
    orcamento = max(0, int(max_imagens) - n_img)
    if orcamento:
        FUNDO_OK = {"gancho", "rajada", "checklist", "citacao", "alerta", "linha_tempo", "comparacao", "contador", "ranking", "grafico",
                    "processo", "lupa", "celular", "classica"}
        tem_img = lambda k: 0 <= k < len(cenas) and (cenas[k]["tipo"].startswith("foto_") or cenas[k]["tipo"] == "fato_real" or cenas[k].get("fundo_foto"))  # noqa: E731
        for passo in (1, 2):
            for k, c in enumerate(cenas):
                if orcamento <= 0:
                    break
                if k == len(cenas) - 1 or c["tipo"] not in FUNDO_OK or tem_img(k):
                    continue
                if c["tipo"] == "classica" and (c.get("cena") or {}).get("tipo") not in ("cinetica", "explicativa", "numero_gigante", "silhuetas", "documento", "imagem"):
                    continue
                if passo == 1 and (tem_img(k - 1) or tem_img(k + 1)):
                    continue
                c["fundo_foto"] = True
                orcamento -= 1
    # a primeira cena e gancho/foto de abertura, a ultima e o fecho
    paleta = rnd.choice(estilo.get("paleta") or ["ouro"])
    dados = {"titulo": titulo, "fps": fps, "paleta": paleta, "semente": rnd.randrange(1, 9999), "estilo": estilo["nome"],
             "marca": marca, "narrado": True, "modo": "serio" if serio else "normal", "aviso": aviso, "cenas": cenas,
             "fatos_usados": [f for f in fatos if any(f["id"] in c.get("fatos", []) for c in cenas)]}
    return dados
