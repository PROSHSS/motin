"""Gera dados sinteticos, SEM AUDIO, para renderizar as 3 novas composicoes."""
import json
from pathlib import Path
import motion_editor

root = Path(__file__).resolve().parents[1]
pasta = root / "public"
pasta.mkdir(parents=True, exist_ok=True)
frases = [
    "Você sabia que uma ideia pode mudar tudo?",
    "Primeiro, clique na tela do aplicativo para começar.",
    "Depois, organize as etapas e veja o resultado.",
]
cenas = [
    {"tipo": "citacao", "narracao": texto, "duracao": 2, "manchete": [],
     "citacao": {"texto": texto}}
    for texto in frases
]
tempos = [{"inicio": i * 2, "fim": i * 2 + 2} for i in range(len(cenas))]
dados = {"titulo": "Teste Motion Pro", "edicao": "motion", "narrado": False,
         "fps": 30, "cenas": cenas, "mostrar_fontes": False}
ctx = {"semente": 2026, "historico": [], "dominio": "tecnologia",
       "id": "test-motion-pro", "versao": "direcao-contextual-v8.1"}
motion_editor.dirigir(dados, tempos, [], contexto=ctx)
for cena, tipo in zip(dados["cenas"], ["palavra", "dividida", "profundidade"]):
    cena["motion"]["layout"] = tipo
    cena["motion"]["variante"] = 1
dados["narrado"] = False
for nome, obj in {
    "showcase.json": dados,
    "tempos_cenas.json": tempos,
    "palavras.json": [],
    "audio.json": {"musica": False, "sfx": False, "narracao": False,
                   "documentario": False},
}.items():
    (pasta / nome).write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                               encoding="utf-8")
print("Fixtures Motion Pro: 3 composicoes, 6 segundos, audio desligado")
