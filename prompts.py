import json, os, random, requests
from estilo_imagem import estilo

ESTILO_IMG = estilo()

MODELO = os.environ.get("MODELO_OLLAMA", "qwen3.5:9b")
# todas as cenas ganham foto; nas cenas animadas ela fica como fundo escurecido
TIPOS_FOTO_PRINCIPAL = {"imagem"}
# cenas so de texto/graficos: nao precisam de foto (economiza cota de imagens)
SEM_IMAGEM = {"frase", "lista_caixas", "painel"}

SCHEMA = {
    "type": "object",
    "properties": {"prompt": {"type": "string"}},
    "required": ["prompt"],
}


# ---------------------------------------------------------------------
# Variedade: cada cena recebe categoria + enquadramento + luz + paleta DIFERENTES
# ---------------------------------------------------------------------
CATEGORIAS = [
    "an everyday person doing a relevant action (face not visible or seen from behind)",
    "a close-up of a single meaningful object on a clean surface",
    "a modern building, street or city scene",
    "a natural landscape or sky that fits the mood",
    "hands interacting with a phone, tablet, document or tool",
    "a workplace, shop, market, office or kitchen interior",
    "a symbolic still-life made of simple objects (coins, keys, clocks, paper, glass)",
    "a crowd or group of anonymous people in a public place, seen from a distance",
    "a vehicle, road, bridge, train or infrastructure",
    "a home interior with warm daily-life details",
]
ENQUADRAMENTOS = [
    "aerial drone view looking straight down",
    "extreme macro close-up",
    "low-angle wide shot",
    "over-the-shoulder shot",
    "wide establishing shot",
    "overhead flat lay on a table",
    "eye-level medium shot",
    "shot through a window or doorway frame",
    "symmetrical one-point perspective",
    "medium close-up with shallow depth of field",
    "high-angle shot from a balcony",
    "reflection in glass or water",
]
LUZES = [
    "soft natural daylight", "warm golden hour sunlight", "overcast diffused daylight",
    "early morning light with long shadows", "harsh midday sun with real shadows", "warm window light indoors",
    "dim practical lights at night", "blue hour with glowing city lights",
]
PALETAS = [
    "natural muted colors", "warm earthy tones", "teal and warm orange tones", "neutral grays with one warm accent",
    "cool daylight tones", "faded vintage tones", "rich natural greens and browns", "urban concrete grays and yellows",
]
EXEMPLOS = (
    "Examples of GOOD prompts (realistic, natural and varied; do NOT copy them):\n"
    "- Money: Overhead shot of worn Brazilian banknotes and coins on a scratched wooden kitchen table, a hand holding a pen over a notebook, soft window light, shallow depth of field.\n"
    "- Sleep: Eye-level shot of a lived-in bedroom at dawn, rumpled sheets, gray morning light through a curtain, realistic clutter on the nightstand.\n"
    "- Cities: Aerial view of a dense Brazilian neighborhood with uneven rooftops, water tanks and hills in hazy afternoon light, documentary style.\n"
    "- Technology: Close-up of hands holding a cracked smartphone in a busy bus, reflections on the window, natural light, slight motion blur.\n"
    "- Scam alert: Medium close-up of a person's hands holding a phone at a cluttered desk at night, blue screen glow on the fingers, realistic and tense.\n"
    "- Work: Wide shot of a crowded street market stall at midday, real fruit crates, sweat and sunlight, candid documentary feel.\n"
    "- Health: Overhead shot of a pharmacy counter with medicine boxes, a glass of water and a prescription paper, cold clinical light.\n"
    "- Politics: Wide shot of a modern government building behind a plaza under an overcast sky, a few anonymous people walking, no readable text.\n"
    "- Economy: Low-angle shot of office towers at dusk with lit windows, wet street reflections, natural city light.\n"
    "- Education: Eye-level shot of students from behind in a worn classroom, sunlight on scratched desks, candid.\n\n"
)


def pedir_prompt(titulo, roteiro_completo, cena, indice=0, anteriores=None):
    rnd = random.Random(f"{titulo}-{indice}")
    cat = CATEGORIAS[(indice * 3 + rnd.randrange(len(CATEGORIAS))) % len(CATEGORIAS)]
    enq = ENQUADRAMENTOS[(indice * 5 + rnd.randrange(len(ENQUADRAMENTOS))) % len(ENQUADRAMENTOS)]
    luz = rnd.choice(LUZES)
    paleta = rnd.choice(PALETAS)
    evitar = ""
    if anteriores:
        evitar = ("Previous scenes already used these images; this one must be clearly DIFFERENT in subject, "
                  "setting, composition and colors: " + " | ".join(a[:90] for a in anteriores[-4:]) + "\n")
    fundo = cena.get("tipo") not in TIPOS_FOTO_PRINCIPAL
    extra = (
        "This image sits behind animated graphics: keep the main subject slightly off-center with some clean "
        "open space, but the image must still be bright, sharp and colorful. "
        if fundo
        else "This image is the main visual of the scene: strong, clear subject and composition. "
    )
    instrucao = (
        "You are the visual director of a modern, clean documentary for a Brazilian audience.\n"
        f"Video title: {titulo}\n"
        f"Full narration: {roteiro_completo}\n\n"
        f"Current scene narration: {cena['narracao']}\n"
        f"Key phrase on screen: {cena.get('destaque', '')}\n\n"
        + EXEMPLOS + evitar +
        f"For THIS scene use: subject type = {cat}; camera = {enq}; lighting = {luz}; color palette = {paleta}.\n"
        "Write ONE image prompt in English (25 to 45 words) for a text-to-image model. "
        "It must show a concrete, literal, photographable scene that illustrates the idea of the "
        "narration (adapt the subject type so it makes sense for the topic). Name the subject, the place, "
        "the camera angle and the light. " + extra +
        ESTILO_IMG["look"] + " "
        "Compose for a VERTICAL 9:16 video: keep the main subject centered so a square image can be cropped to portrait. "
        "Use Brazilian settings when the topic is about Brazil. "
        "Do not include any written text, numbers, logos, flags with text, or recognizable real people "
        "or politicians; use anonymous people, people seen from behind, hands, objects and buildings instead."
    )
    r = requests.post("http://localhost:11434/api/chat", json={
        "model": MODELO,
        "stream": False,
        "think": False,
        "options": {"num_ctx": 4096, "temperature": 0.9},
        "format": SCHEMA,
        "messages": [{"role": "user", "content": instrucao}],
    }, timeout=900)
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])["prompt"].strip()


def main():
    roteiro = json.load(open("roteiro.json", encoding="utf-8"))
    completo = " ".join(c["narracao"] for c in roteiro["cenas"])
    for i, cena in enumerate(roteiro["cenas"], start=1):
        print(f"Cena {i}: criando prompt visual...")
        if cena.get("tipo") in SEM_IMAGEM:
            print(f"Cena {i}: so texto, sem foto.")
            continue
        anteriores = [c["prompt_imagem"] for c in roteiro["cenas"][: i - 1] if c.get("prompt_imagem")]
        cena["prompt_imagem"] = pedir_prompt(roteiro["titulo"], completo, cena, i, anteriores)
        print("   ->", cena["prompt_imagem"])
    json.dump(roteiro, open("roteiro.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("OK: roteiro.json atualizado com prompt_imagem")


main()
