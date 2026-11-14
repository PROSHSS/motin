"""
SHOWCASE: video de animacao vertical (9:16), sem narracao, a partir de um tema.

Exemplos:
  python criar_showcase.py "5 sinais de golpe no Pix"
  python criar_showcase.py "Black Friday" --estilo varejo_ouro
  python criar_showcase.py "Dicas de sono" --fatos fatos.txt
  python criar_showcase.py --lote temas.txt          (um tema por linha, faz todos)
  python criar_showcase.py --json meu_roteiro.json   (roteiro escrito a mao)
  python criar_showcase.py --estilos                 (lista os estilos)
Opcoes: --sem-ia (nao usa o Ollama) --sem-musica --semente 123 --novo
"""
import argparse
import json
import random
import shutil
import sys
import time
from pathlib import Path

from criar import (RAIZ, carregar_config, env_base, iniciar_ollama, log, normalizar_volume, parar_ollama,
                   preparar_audio, rodar, slug)
import showcase_gen as G


def renderizar(dados, nome, cfg, env, args):
    base = Path(cfg["pasta_dados"]) if cfg.get("pasta_dados") else RAIZ
    proj = base / "projetos" / ("showcase_" + nome)
    (proj / "public").mkdir(parents=True, exist_ok=True)
    (base / "saidas").mkdir(parents=True, exist_ok=True)
    (proj / "public" / "showcase.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    (proj / "roteiro_showcase.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    cfg = dict(cfg)
    if dados.get("marca"):
        cfg["marca"] = dados["marca"]
    preparar_audio(proj, cfg, env, sys.executable, nome, sem_musica=args.sem_musica, lufs_musica=-24)

    npx = shutil.which("npx") or shutil.which("npx.cmd")
    saida = proj / "showcase.mp4"
    if saida.exists():
        saida.unlink()
    log("Renderizando (alguns minutos)...")
    rodar([npx, "remotion", "render", "src/index.ts", "Showcase", str(saida),
           f"--public-dir={proj / 'public'}", f"--concurrency={cfg['concorrencia']}"], RAIZ, env, "renderizacao")
    if cfg.get("normalizar_volume", True):
        normalizar_volume(saida, cfg.get("lufs", -14))
    final = base / "saidas" / f"showcase_{nome}.mp4"
    shutil.copyfile(saida, final)
    return final


def roteiro_para(tema, args, cfg, estilo_nome, rnd, fatos):
    estilo = G.escolher_estilo(estilo_nome, rnd)
    log(f"Estilo sorteado: {estilo['nome']} ({estilo.get('descricao', '')})")
    if args.sem_ia:
        bruto = G.sem_ia(tema, estilo, rnd)
    else:
        log("Escrevendo o roteiro das cenas (Ollama, alguns minutos)...")
        try:
            bruto = G.chamar_llm(tema, fatos, estilo, cfg["modelo_ollama"])
        except RuntimeError as e:
            log(f"AVISO: {e}\nUsando o modo simples sem IA para nao parar.")
            bruto = G.sem_ia(tema, estilo, rnd)
    dados = G.montar(bruto, tema, estilo, rnd, marca=cfg.get("marca", ""))
    if len(dados["cenas"]) < 4:
        log("A IA devolveu poucas cenas validas; completando com o modo simples.")
        extra = G.montar(G.sem_ia(tema, estilo, rnd), tema, estilo, rnd, marca=cfg.get("marca", ""))
        dados["cenas"] = extra["cenas"]
    log("Cenas: " + " > ".join(c["tipo"] for c in dados["cenas"]))
    log(f"Paleta: {dados['paleta']}   Semente visual: {dados['semente']}")
    return dados


def main():
    ap = argparse.ArgumentParser(description="Showcase: video de animacao a partir de um tema.")
    ap.add_argument("tema", nargs="?", help="tema do video (entre aspas)")
    ap.add_argument("--fatos", help="arquivo .txt com fatos reais para usar")
    ap.add_argument("--estilo", default="auto", help="nome de um estilo da pasta estilos (padrao: sorteia)")
    ap.add_argument("--semente", type=int, help="repete exatamente o mesmo sorteio")
    ap.add_argument("--lote", help="arquivo .txt com um tema por linha")
    ap.add_argument("--json", help="usa um roteiro showcase pronto (escrito a mao)")
    ap.add_argument("--sem-ia", action="store_true", help="nao usa o Ollama")
    ap.add_argument("--sem-musica", action="store_true")
    ap.add_argument("--estilos", action="store_true", help="lista os estilos disponiveis")
    ap.add_argument("--novo", action="store_true", help="(compatibilidade) sempre cria arquivo novo")
    args = ap.parse_args()

    if args.estilos:
        for n, e in G.carregar_estilos().items():
            print(f"  {n:18} {e.get('descricao', '')}")
        return

    cfg = carregar_config()
    env = env_base(cfg)
    inicio = time.time()

    # roteiro escrito a mao
    if args.json:
        dados = json.loads(Path(args.json).read_text(encoding="utf-8"))
        nome = slug(dados.get("titulo", Path(args.json).stem)) + "-" + time.strftime("%H%M%S")
        final = renderizar(dados, nome, cfg, env, args)
        log(f"\nPRONTO em {(time.time() - inicio) / 60:.1f} min -> {final}")
        return

    temas = []
    if args.lote:
        temas = [l.strip() for l in Path(args.lote).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    elif args.tema:
        temas = [args.tema]
    else:
        ap.print_help()
        sys.exit(1)
    fatos = Path(args.fatos).read_text(encoding="utf-8") if args.fatos else ""

    proc = None
    if not args.sem_ia:
        proc = iniciar_ollama(cfg)
    roteiros = []
    try:
        for tema in temas:
            semente = args.semente if args.semente is not None else random.randrange(10**6)
            rnd = random.Random(semente)
            log(f"\n=== Tema: {tema} ===")
            roteiros.append((tema, roteiro_para(tema, args, cfg, args.estilo, rnd, fatos)))
    finally:
        if proc is not None or not args.sem_ia:
            parar_ollama(cfg, proc)

    prontos = []
    for tema, dados in roteiros:
        nome = slug(tema) + "-" + time.strftime("%H%M%S")
        log(f"\n=== Renderizando: {tema} ===")
        prontos.append(renderizar(dados, nome, cfg, env, args))
    log("\n" + "=" * 60)
    log(f" PRONTO em {(time.time() - inicio) / 60:.1f} minutos")
    for p in prontos:
        log(f" Video: {p}")
    log("=" * 60)


if __name__ == "__main__":
    main()
