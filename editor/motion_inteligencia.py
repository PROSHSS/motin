"""Direcao semantica, factual e deterministica para as cenas Motion.

O planejamento nao inventa dados nem interpreta videos por conta propria.
Nao depende de rede, GPU ou do modelo de linguagem para funcionar.
"""
import re
import unicodedata
from collections import Counter

STOP = frozenset("""a as ao aos o os um uma e de da das do dos em na nas no nos
para por com que se eu voce ele ela esse essa isso estes estas quando como
tambem mais muito pouco cada sua seu seus suas nosso nossa ser ter fazer
foi sera esta estao tem sao ja ainda sobre entre sem""".split())

PADROES = {
    "pergunta": r"\?|(?:\bpor que\b|\bcomo\b|\bsera que\b|\bvoce sabia\b)",
    "revelacao": r"\b(surpresa|descoberta|incrivel|segredo|revel\w*|imagina|ninguem sabia|mas olha)\b",
    "contraste": r"\b(porem|mas|enquanto|diferente|compar\w*|antes|depois|melhor|pior|versus|contra)\b",
    "processo": r"\b(primeiro|segundo|terceiro|passo|etapa|etapas|processo|funciona|faça|faca|comece|configure|ativar)\b",
    "demonstracao": r"\b(toque|clique|arraste|mostr\w*|tela|aplicativo|celular|botao|menu|tutorial|digite|acesse)\b",
    "prova": r"\b(pesquisa|estudo|dados|numero|porcentagem|estatistica|documento|segundo|fonte)\b",
    "alerta": r"\b(cuidado|perigo|atenção|atencao|risco|alerta|golpe|evite|nunca)\b",
    "trajeto": r"\b(trajeto|rota|caminho|viajar|transito|estrada|percurso|cidade)\b",
    "conclusao": r"\b(portanto|conclusao|resumindo|resultado|em resumo|por fim|finalmente)\b",
}
# Sem acentos para processar facilmente portugues brasileiro.
ATRIBUTOS = {
    "palavra": {"pergunta": 6, "revelacao": 7, "conclusao": 5, "alerta": 4, "contraste": 2},
    "dividida": {"contraste": 7, "demonstracao": 4, "processo": 2, "prova": 2},
    "profundidade": {"processo": 5, "trajeto": 5, "revelacao": 3, "demonstracao": 3},
    "tipografia": {"pergunta": 4, "revelacao": 4, "conclusao": 4},
    "morph": {"contraste": 3, "processo": 3, "revelacao": 2},
    "demonstracao": {"demonstracao": 6, "processo": 4},
    "interface": {"demonstracao": 7, "processo": 2},
    "comparativo": {"contraste": 6, "prova": 2},
    "sequencia": {"processo": 6},
    "editorial": {"prova": 2, "revelacao": 3},
    "impacto": {"revelacao": 4, "pergunta": 3, "alerta": 4},
    "colagem": {"contraste": 3, "prova": 3},
    "orbita": {"trajeto": 4, "processo": 2},
    "recorte": {"prova": 2},
    "dados": {"prova": 5},
}


def normal(texto):
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(texto).lower())
        if not unicodedata.combining(c)
    )


def termos(texto):
    return {p for p in re.findall(r"[a-z0-9]+", normal(texto)) if len(p) > 2 and p not in STOP}


def analisar_roteiro(cenas):
    """Classifica o sentido da frase e do seu contexto; nao cria fatos."""
    resultado = []
    for i, cena in enumerate(cenas):
        fala = str(cena.get("narracao") or "")
        norm = normal(fala)
        pontos = {nome: bool(re.search(padrao, norm)) for nome, padrao in PADROES.items()}
        ordem = sorted((nome for nome, ligado in pontos.items() if ligado),
                       key=lambda nome: (-int(nome in ("contraste", "demonstracao", "processo")), nome))
        intencao = ordem[0] if ordem else "contexto"
        anterior = cenas[i - 1].get("narracao", "") if i else ""
        seguinte = cenas[i + 1].get("narracao", "") if i < len(cenas) - 1 else ""
        compartilhados = len(termos(fala) & termos(anterior))
        segue = len(termos(fala) & termos(seguinte))
        intensidade = ("alta" if pontos["revelacao"] or pontos["alerta"]
                       else "media" if pontos["pergunta"] or pontos["contraste"]
                       else "baixa")
        resultado.append({
            "intencao": intencao, "intencoes": ordem,
            "intensidade": intensidade,
            "conexao_anterior": compartilhados > 0,
            "conexao_proxima": segue > 0,
            "termos": sorted(termos(fala)),
        })
    return resultado


def adequacao(layout, analise, cena, indice, total):
    """Pontua adequacao visual; variedade e avaliada separadamente no editor."""
    intencoes = analise.get("intencoes", []) if analise else []
    valor = sum(ATRIBUTOS.get(layout, {}).get(x, 0) for x in intencoes)
    possui_midia = bool(cena.get("foto") or cena.get("video") or cena.get("recorte"))
    if layout == "dividida":
        valor += 4 if possui_midia else -3
    if layout == "profundidade":
        valor += 3 if possui_midia else 0
    if layout == "editorial":
        valor += 4 if possui_midia else -5
    if layout in ("colagem", "recorte"):
        valor += 3 if possui_midia else -4
    if layout == "interface" and "demonstracao" not in intencoes:
        valor -= 3
    if layout == "palavra":
        if indice == 0 or indice == total - 1:
            valor += 4
        if len(str(cena.get("narracao", "")).split()) > 35:
            valor -= 3
    if layout == "impacto" and indice == 0:
        valor += 3
    return valor


def descrever_midia(arquivo, descricao="", etiquetas=None):
    """Usa apenas metadados declarados ou nome do arquivo; sem fingir visao IA."""
    partes = [descricao, " ".join(etiquetas or [])]
    if not any(p.strip() for p in partes):
        # Nomes de cameras (ex. IMG_0023) nao sao descricoes de conteudo.
        nome = str(arquivo).replace("\\", "/").split("/")[-1]
        nome = re.sub(r"\.[^.]+$", "", nome)
        nome = re.sub(r"(?i)\b(?:img|video|clip|dsc|mov)[_-]?\d+\b", "", nome)
        partes.append(re.sub(r"[_-]+", " ", nome))
    return " ".join(partes)


def pontuacao_midia(cena, descricao):
    return len(termos(cena.get("narracao", "")) & termos(descricao))


def escolher_cenas_midia(cenas, arquivos):
    """Uma midia livre e usada apenas onde seu rotulo corresponde a fala.

    Atribuicao fixa prevalece; na ausencia de metadados uteis nao se presume
    o conteudo dos pixels. Retorna indices de cena (0-based) por indice da midia.
    """
    usados = set()
    posicoes = {}
    for j, midia in enumerate(arquivos):
        if midia.get("cena") is not None:
            alvo = int(midia["cena"]) - 1
            if 0 <= alvo < len(cenas) and alvo not in usados:
                posicoes[j] = alvo
                usados.add(alvo)
    for j, midia in enumerate(arquivos):
        if j in posicoes or midia.get("cena") is not None:
            continue
        descricao = descrever_midia(
            midia.get("arquivo", ""),
            midia.get("descricao", ""),
            midia.get("etiquetas", []),
        )
        ranked = sorted(
            ((pontuacao_midia(cena, descricao), -i, i) for i, cena in enumerate(cenas)
             if i not in usados),
            reverse=True,
        )
        if ranked and ranked[0][0] > 0:
            alvo = ranked[0][2]
            posicoes[j] = alvo
            usados.add(alvo)
    return posicoes


def assinatura_visual(motion):
    """Assinatura estrutural para memoria de variedade, nao so cor."""
    campos = ("layout", "variante", "corte", "camera", "foco", "densidade", "movimento")
    return "|".join(str(motion.get(chave, "")) for chave in campos)
