import json, sys, requests

MODELO = "qwen3.5:9b"

ICONES = ['Vote', 'Landmark', 'Scale', 'Users', 'User', 'Flag', 'FileText', 'Gavel', 'Building2', 'Banknote', 'TrendingUp', 'TrendingDown', 'ChartColumn', 'ChartPie', 'Clock', 'Calendar', 'MapPin', 'Globe', 'Shield', 'Lock', 'Key', 'Heart', 'Star', 'Check', 'X', 'TriangleAlert', 'Megaphone', 'Newspaper', 'ScrollText', 'Handshake', 'Search', 'Lightbulb', 'Target', 'Zap', 'Coins', 'Percent', 'Hourglass', 'BookOpen', 'Mic', 'Tv', 'Smartphone', 'Brain', 'Eye', 'Briefcase', 'GraduationCap', 'Hospital', 'House', 'Car', 'Plane', 'Wheat', 'Factory', 'Fuel', 'Siren', 'Swords', 'Sprout']

TIPOS = ["imagem", "cinetica", "silhuetas", "documento", "versus", "linha_tempo", "explicativa",
         "grafico_barras", "grafico_linha", "rosca", "numero_gigante", "ranking",
         "citacao", "checklist", "alerta", "frase", "lista_caixas", "painel"]

SCHEMA = {
  "type": "object",
  "properties": {
    "titulo": {"type": "string"},
    "cenas": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "narracao": {"type": "string"},
          "tipo": {"type": "string", "enum": TIPOS},
          "destaque": {"type": "string"},
          "elementos": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "tipo": {"type": "string", "enum": ["icone", "numero", "lista"]},
                "texto": {"type": "string"},
                "icone": {"type": "string", "enum": ICONES},
                "gatilho": {"type": "string"}
              },
              "required": ["tipo", "texto", "icone", "gatilho"]
            }
          }
        },
        "required": ["narracao", "tipo", "destaque", "elementos"]
      }
    }
  },
  "required": ["titulo", "cenas"]
}

REGRAS = """
Escreva o roteiro de um video curto de TikTok (60 a 80 segundos) em portugues do Brasil, tom serio de documentario.
Use SOMENTE os fatos e numeros fornecidos, sem inventar nada.
Divida em 10 a 12 cenas curtas (ritmo rapido: uma ideia por cena, narracao de 1 frase curta ou 2 muito curtas). Cada cena tem: narracao (1 a 2 frases curtas), tipo, destaque e elementos.

ESCOLHA O TIPO DE CADA CENA (varie, nao repita o mesmo tipo em cenas seguidas, use cada tipo no maximo 3 vezes; use alerta, checklist ou citacao quando combinarem com o assunto; inclua de 2 a 3 cenas de dados quando houver numeros nos fatos):
- primeira e ultima cena: tipo "imagem", elementos = [].
- "cinetica": frase de impacto. destaque = UMA palavra ou expressao curta (ate 12 letras) que vira texto gigante.
  elementos[0].texto = frase curta que vem ANTES do destaque. elementos[1] e seguintes = linhas que vem DEPOIS (2 a 3 linhas curtas). Para negar uma ideia, comece o texto com "~".
- "documento": uma regra, lei ou definicao. destaque = carimbo curto (ate 9 letras, ex: "50% + 1").
  elementos[0].texto = origem (ex: "TSE regra eleitoral"). elementos[1].texto = a frase da regra completa.
  elementos[2].texto = um trecho copiado EXATAMENTE de elementos[1].texto, que sera marcado de amarelo.
- "versus": comparacao de DOIS numeros reais. destaque = titulo curto. elementos tem exatamente 2 itens: texto = "Nome 47,03%" (nome e numero).
- "silhuetas": fala sobre pessoas, eleitores, populacao. destaque = frase curta (2 a 3 palavras). elementos[0].texto = frase curta antes (opcional).
- "linha_tempo": sequencia de etapas ou datas. destaque = titulo. elementos = 3 ou 4 itens, texto = "04 OUT|1o turno" (data, barra vertical, nome).
- "explicativa": explicar conceito com icones. destaque = titulo curto. elementos = 2 a 4 itens: tipo "icone" (texto ate 4 palavras), "numero" (texto = numero real, ex: "47,03%", maximo 1) ou "lista".

TIPOS DE RITMO (so texto, sem foto; use varios deles para o video ter dinamica; nao precisam de numeros):
- "frase": uma ideia forte em poucas palavras com uma palavra-chave desenhada. destaque = a frase (3 a 8 palavras, sem ponto final). elementos[0].texto = a palavra-chave (uma palavra que esta no destaque); elementos[0].gatilho = palavra da narracao em que o desenho aparece. elementos[1].texto = estilo do desenho: "caixa", "circulo", "sublinhado" ou "x" (use "x" para negar).
- "lista_caixas": 2 a 4 palavras empilhadas em tarjas coloridas (exemplos, categorias, itens). destaque = titulo curto. elementos = 2 a 4 itens de 1 a 3 palavras, cada um com gatilho (palavra da narracao).
- "painel": 3 ou 4 indicadores em cartoes. destaque = titulo curto. elementos = 3 ou 4 itens, texto = "Rotulo|valor" (ex: "Retencao|87%", "Visualizacoes|100 mil"), usando SOMENTE numeros dos fatos; o 1o item vira numero grande, o 2o e o 3o recebem barra e anel (use porcentagem neles).

TIPOS DE IMPACTO (nao precisam de numeros):
- "alerta": aviso importante ou perigo (golpe, risco, erro comum). destaque = ate 3 palavras em maiusculas-sentido (ex: "Golpe do Pix"). elementos[0].texto = frase curta de aviso. elementos[1] a [3] = ate 3 linhas curtas (cada uma ate 6 palavras).
- "checklist": passos ou dicas praticas. destaque = titulo curto. elementos = 3 ou 4 itens curtos (ate 7 palavras). Comece o texto com "! " quando o item for algo que NAO se deve fazer (aparece com X vermelho); sem "!" aparece com visto verde.
- "citacao": frase marcante de uma fonte (lei, instituicao, especialista citado nos fatos; nunca invente citacao). destaque = a frase (ate 14 palavras). elementos[0].texto = a fonte (ex: "Banco Central").

TIPOS DE DADOS (use SOMENTE quando os fatos trazem os numeros; nunca invente numeros; se nao houver numeros, nao use estes tipos):
- "numero_gigante": UM numero de impacto. destaque = o numero com unidade (ex: "42,3 bi", "87%", "R$ 4,2 mil"). elementos[0].texto = o que o numero mede (ate 6 palavras). elementos[1].texto = comparacao ou contexto curto (opcional).
- "grafico_barras": compara 2 a 5 valores. destaque = titulo curto. elementos: 2 a 5 itens, texto = "Nome|valor" (ex: "Sul|38", "Sudeste|52%").
- "grafico_linha": evolucao no tempo. destaque = titulo curto. elementos: 3 a 6 itens em ordem cronologica, texto = "ano|valor" (ex: "2021|9,4", "2022|24").
- "rosca": partes de um total em porcentagem. destaque = titulo curto. elementos: 2 a 5 itens, texto = "Nome|45%" (a soma deve dar 100%).
- "ranking": lista ordenada do maior para o menor. destaque = titulo curto. elementos: 3 a 5 itens, texto = "Nome|valor" do MAIOR para o MENOR.
Em todos os tipos de dados use tipo "lista" nos elementos e preencha "gatilho" com uma palavra da narracao (na ordem em que sao ditas).

GANCHO: a narracao da cena 1 deve comecar com uma frase curta e forte que prende a atencao nos primeiros 3 segundos (pergunta, numero chocante ou afirmacao surpreendente). O destaque da cena 1 deve ter ate 5 palavras.

REGRAS DOS ELEMENTOS:
- "gatilho": UMA palavra em minusculas e sem acento que existe na narracao da cena. Marca o momento em que o elemento aparece. Siga a ordem em que as palavras sao ditas.
- "icone": sempre preencha com um icone adequado da lista (use "Check" se nao importar).
- "tipo" do elemento: use "icone" se nao for numero nem lista.
"""


def gerar_roteiro(tema, fatos=""):
    prompt = f"{REGRAS}\nTema: {tema}\nFatos permitidos:\n{fatos}\n"
    r = requests.post("http://localhost:11434/api/chat", json={
        "model": MODELO,
        "stream": False,
        "think": False,
        "options": {"num_ctx": 4096, "temperature": 0.4},
        "format": SCHEMA,
        "messages": [{"role": "user", "content": prompt}],
    }, timeout=1800)
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


if __name__ == "__main__":
    tema = sys.argv[1]
    fatos = open("fatos.txt", encoding="utf-8").read() if len(sys.argv) > 2 else ""
    roteiro = gerar_roteiro(tema, fatos)
    with open("roteiro.json", "w", encoding="utf-8") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)
    print("OK: roteiro.json criado")
