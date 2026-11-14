import json, asyncio, edge_tts

VOZ = "pt-BR-ThalitaMultilingualNeural"   # mais natural que Antonio/Francisca

async def main():
    roteiro = json.load(open("roteiro.json", encoding="utf-8"))
    texto = " ".join(c["narracao"] for c in roteiro["cenas"])
    await edge_tts.Communicate(texto, VOZ, rate="-8%", pitch="-2Hz").save("narracao.mp3")
    print("OK: narracao.mp3 criado")

asyncio.run(main())
