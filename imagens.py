import os, sys, json, base64, time, random
import urllib.parse
import requests

# ---------------- CONFIGURAÇÃO ----------------
CONTA = os.environ.get("CF_ACCOUNT_ID", "")
TOKEN = os.environ.get("CF_API_TOKEN", "")
MODELO = "@cf/black-forest-labs/flux-1-schnell"
URL = os.environ.get(
    "CF_URL",
    f"https://api.cloudflare.com/client/v4/accounts/{CONTA}/ai/run/{MODELO}",
)
PASSOS = 8   # 4 = mais rápido/barato, 8 = mais qualidade (limite grátis: ~10.000 neurons/dia, ~95 imagens)

# Cenas que recebem imagem de fundo (barras e hemiciclo ficam como gráfico)
TIPOS_COM_IMAGEM = None   # None = todas as cenas ganham foto

# Estilo leve: so mantem a "cara de documentario"; enquadramento e luz vem do prompts.py (varia por cena)
from estilo_imagem import estilo  # noqa: E402
ESTILO = estilo()["sufixo"]

PASTA_SAIDA = "public"
SEM_IMAGEM = {"frase", "lista_caixas", "painel"}   # cenas so de texto: nao gastam imagem
# ----------------------------------------------


def gerar(prompt):
    cab = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    corpo = {"prompt": prompt, "steps": PASSOS}
    for tentativa in range(5):
        r = requests.post(URL, headers=cab, json=corpo, timeout=180)
        if r.status_code in (429, 500, 502, 503):
            espera = 15 * (tentativa + 1)
            print(f"   limite/instabilidade ({r.status_code}), aguardando {espera}s...")
            time.sleep(espera)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Erro {r.status_code}: {r.text[:500]}")
        dados = r.json()
        img = (dados.get("result") or {}).get("image")
        if not img:
            raise RuntimeError("A resposta não trouxe imagem: " + json.dumps(dados)[:500])
        return base64.b64decode(img), "jpg"
    # limite diario da Cloudflare atingido: tenta o servico gratuito de reserva (Pollinations)
    if os.environ.get("IMG_RESERVA", "1") != "0":
        print("   Cloudflare sem cota agora. Tentando o servico gratuito de reserva (Pollinations)...")
        try:
            u = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt[:900])
                 + f"?width=832&height=1216&model=flux&nologo=true&seed={random.randint(1, 999999)}")
            r = requests.get(u, timeout=240)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image") and len(r.content) > 5000:
                return r.content, "jpg"
            print(f"   reserva falhou ({r.status_code}).")
        except requests.RequestException as e:
            print("   reserva falhou:", e)
    raise RuntimeError("Muitas tentativas falharam (limite diário de 10.000 neurons atingido?).")


def main():
    if not CONTA or not TOKEN:
        print("ERRO: defina as duas variáveis antes. No Prompt de Comando:")
        print("   set CF_ACCOUNT_ID=SEU_ACCOUNT_ID")
        print("   set CF_API_TOKEN=SEU_TOKEN")
        sys.exit(1)

    roteiro = json.load(open("roteiro.json", encoding="utf-8"))
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    for i, cena in enumerate(roteiro["cenas"], start=1):
        if cena.get("tipo") in SEM_IMAGEM:
            print(f"Cena {i}: so texto, sem imagem.")
            continue
        if TIPOS_COM_IMAGEM and cena.get("tipo") not in TIPOS_COM_IMAGEM:
            continue
        nome = f"img_{i}.jpg"
        caminho = os.path.join(PASTA_SAIDA, nome)
        if os.path.exists(caminho):
            cena["imagem"] = nome
            print(f"Cena {i}: já existe, pulando ({nome})")
            continue

        if cena.get("prompt_imagem"):
            prompt = f"{cena['prompt_imagem']} {ESTILO}"
        else:
            prompt = (
                f"{ESTILO}"
                f"Scene illustrating this idea: {cena['narracao']} "
                f"Main concept: {cena.get('destaque', '')}."
            )
        print("   prompt:", prompt[:160])
        print(f"Cena {i}: gerando imagem...")
        dados, _ = gerar(prompt)
        with open(caminho, "wb") as f:
            f.write(dados)
        cena["imagem"] = nome
        time.sleep(2)

    with open(os.path.join(PASTA_SAIDA, "roteiro.json"), "w", encoding="utf-8") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)
    print("OK: imagens salvas em public\\ e public\\roteiro.json atualizado")


main()
