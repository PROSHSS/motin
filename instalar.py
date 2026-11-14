# -*- coding: utf-8 -*-
"""Instalador OFFLINE e reversivel do pacote Motion Pro para Windows.

Nao acessa GitHub, nao baixa dependencias, nao modifica dados privados.
Uma copia de seguranca de todos os arquivos substituidos e criada antes.
"""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ_PACOTE = Path(__file__).resolve().parent
NOVOS = ["motion_inteligencia.py", "src/showcase/CenasPro.tsx",
         "tests/test_motion_pro_inteligencia.py", "tests/test_motion_pro_integracao.py"]
ALTERADOS = [
    "motion_editor.py",
    "motion_variacao.py",
    "criar.py",
    "painel.py",
    "src/showcase/Motion.tsx",
    "src/showcase/Base.tsx",
]


def aplicar(t, old: str, new: str, label: str) -> str:
    """Aplica substituicao sem duplicar mudancas em instalacoes ja atualizadas."""
    if old == new:
        raise ValueError("Substituicao sem alteracao: " + label)
    if new in t:
        return t
    ocorrencias = t.count(old)
    if ocorrencias != 1:
        raise RuntimeError(f"Editor diferente do esperado em {label} ({ocorrencias} ocorrencias). Nenhum arquivo foi alterado.")
    return t.replace(old, new, 1)


def patch_motion_editor(t: str) -> str:
    repl = [
        ("from motion_variacao import planejar_variedade, detalhes_visual, numero_aleatorio, acao",
         "from motion_variacao import planejar_variedade, detalhes_visual, numero_aleatorio, acao\nfrom motion_inteligencia import analisar_roteiro, adequacao, escolher_cenas_midia"),
        ("LAYOUTS=('impacto','morph','interface','colagem','orbita','recorte','tipografia','comparativo','sequencia','editorial','dados','demonstracao')",
         "LAYOUTS=('impacto','morph','interface','colagem','orbita','recorte','tipografia','comparativo','sequencia','editorial','dados','demonstracao','palavra','dividida','profundidade')"),
        ("def escolher(c,i,n,uso,recentes,plano=None):",
         "def escolher(c,i,n,uso,recentes,plano=None,analise=None):"),
        ("elif c.get('video'):op=['editorial','colagem']",
         "elif c.get('video'):op=['editorial','colagem','dividida','profundidade']"),
        ("elif i==0:op=['impacto','tipografia']+(['demonstracao'] if act!='observar' else [])",
         "elif i==0:op=['impacto','tipografia','palavra']+(['demonstracao'] if act!='observar' else [])"),
        ("elif act=='etapas':op=['sequencia','demonstracao','morph']",
         "elif act=='etapas':op=['sequencia','demonstracao','morph','profundidade']"),
        ("elif act in ('proteger','buscar','produzir','percorrer','comunicar'):op=['demonstracao','morph','interface'] if plano.get('dominio')=='tecnologia' else ['demonstracao','morph','tipografia']",
         "elif act in ('proteger','buscar','produzir','percorrer','comunicar'):op=['demonstracao','morph','interface','profundidade'] if plano.get('dominio')=='tecnologia' else ['demonstracao','morph','tipografia','profundidade']"),
        ("elif act=='transformar':op=['morph','demonstracao','comparativo','tipografia']",
         "elif act=='transformar':op=['morph','demonstracao','comparativo','tipografia','palavra']"),
        ("elif act=='conectar':op=['orbita','demonstracao','morph']",
         "elif act=='conectar':op=['orbita','demonstracao','morph','profundidade']"),
        ("elif c.get('foto'):op=['colagem','editorial','tipografia']",
         "elif c.get('foto'):op=['colagem','editorial','tipografia','dividida','profundidade']"),
        ("elif i==n-1:op=['tipografia','impacto','morph']",
         "elif i==n-1:op=['tipografia','impacto','morph','palavra']"),
        ("else:op=['morph','tipografia','impacto','orbita','demonstracao']",
         "else:op=['morph','tipografia','impacto','orbita','demonstracao','palavra','profundidade']"),
        ("('orbita','tipografia','impacto','demonstracao','morph') if x not in op and not uso[x]][:2]",
         "('orbita','tipografia','impacto','demonstracao','morph','palavra','profundidade') if x not in op and not uso[x]][:2]"),
        ("return uso[x]*3+passado*.55+aberturas*2+op.index(x)*.06+numero_aleatorio(plano['semente'],'layout',i,x)*1.2",
         "return uso[x]*{'consistente':2,'criativa':3,'maxima':4}.get(plano.get('variedade_motion','criativa'),3)+passado*.55+aberturas*2+op.index(x)*.06+numero_aleatorio(plano['semente'],'layout',i,x)*1.2-adequacao(x,analise,c,i,n)*.48"),
        ("fps=int(dados.get('fps') or 30);uso=Counter();recentes=[];cursores={};visuais=[]",
         "fps=int(dados.get('fps') or 30);uso=Counter();recentes=[];cursores={};visuais=[]\n    analises=analisar_roteiro(dados['cenas'])"),
        ("layout=escolher(c,i,len(dados['cenas']),uso,recentes,plano);uso[layout]+=1;recentes.append(layout)",
         "layout=escolher(c,i,len(dados['cenas']),uso,recentes,plano,analises[i]);uso[layout]+=1;recentes.append(layout)"),
        ("'legendas':bool(palavras),'versao':VERSAO_MOTION}",
         "'legendas':bool(palavras),'versao':VERSAO_MOTION,'intencao':analises[i]['intencao'],'intensidade':analises[i]['intensidade']}"),
        ("    j=0\n    for i,c in enumerate(dados['cenas']):\n        m=fixos.get(i+1)\n        if m is None and livres and (i%2==1 or len(dados['cenas'])==1):m=livres[j%len(livres)];j+=1",
         "    # Metadados textuais associam clipes ao roteiro; sem metadados, manter comportamento legado.\n"
         "    mapa=escolher_cenas_midia(dados['cenas'],livres) if livres else {}\n"
         "    por_cena={indice:livres[j] for j,indice in mapa.items()}\n"
         "    sem_rotulo=not mapa and not any(m.get('descricao') or m.get('etiquetas') for m in livres)\n"
         "    j=0\n    for i,c in enumerate(dados['cenas']):\n"
         "        m=fixos.get(i+1) or por_cena.get(i)\n"
         "        if m is None and livres and sem_rotulo and (i%2==1 or len(dados['cenas'])==1):\n"
         "            m=livres[j%len(livres)]\n            j+=1"),
    ]
    for i, (o, n) in enumerate(repl):
        t = aplicar(t, o, n, f"motion_editor.py, alteracao {i+1}")
    return t


def patch_variacao(t: str) -> str:
    repl = [
        ("from pathlib import Path", "from pathlib import Path\nfrom motion_inteligencia import assinatura_visual"),
        ("'corte':c.get('motion',{}).get('corte',0)}",
         "'corte':c.get('motion',{}).get('corte',0),'assinatura':assinatura_visual(c.get('motion',{})),'foco':c.get('motion',{}).get('foco'),'densidade':c.get('motion',{}).get('densidade'),'movimento':c.get('motion',{}).get('movimento')}"),
        ("return {'semente':seed,'historico':hist,'dominio':dom,'cor':cor}",
         "return {'semente':seed,'historico':hist,'dominio':dom,'cor':cor,'intensidade_motion':(ctx or {}).get('intensidade_motion','equilibrado'),'variedade_motion':(ctx or {}).get('variedade_motion','criativa')}"),
        ("m=c['motion'];m.update({'dominio':dom,'acao':act,'variante':variante,'acento':plano['cor'],'corte':corte,'camera':int(numero_aleatorio(seed,'camera',i)*4)%4,'velocidade':.88+numero_aleatorio(seed,'ritmo',i)*.24})",
         "m=c['motion']\n"
         " foco=int(numero_aleatorio(seed,'foco',i,layout)*3)%3\n"
         " densidade=int(numero_aleatorio(seed,'densidade',i,layout)*3)%3\n"
         " movimento=int(numero_aleatorio(seed,'movimento',i,layout)*4)%4\n"
         " assinatura=f'{layout}|{variante}|{corte}|{foco}|{densidade}|{movimento}'\n"
         " assinaturas_recentes=[s.get('assinatura') for h in plano['historico'][:5] for s in h.get('cenas',[])]\n"
         " if assinatura in assinaturas_recentes:\n  foco=(foco+1)%3\n"
         " if layouts and layouts[-1].get('layout')==layout and layouts[-1].get('variante')==variante:\n  variante=(variante+1)%3\n"
         " m.update({'dominio':dom,'acao':act,'variante':variante,'acento':plano['cor'],'corte':corte,'camera':int(numero_aleatorio(seed,'camera',i)*4)%4,'velocidade':.88+numero_aleatorio(seed,'ritmo',i)*.24,'foco':foco,'densidade':densidade,'movimento':movimento,'movimento_intensidade':plano.get('intensidade_motion','equilibrado')})"),
    ]
    for i, (o, n) in enumerate(repl):
        t = aplicar(t, o, n, f"motion_variacao.py, alteracao {i+1}")
    return t


def patch_criar(t: str) -> str:
    repl = [
        ('    "edicao": "motion",',
         '    "edicao": "motion",\n    "intensidade_motion": "equilibrado",\n    "variedade_motion": "criativa",'),
        ('        if k == "edicao" and v in ("motion", "anterior"):',
         '        if k == "intensidade_motion" and v in ("suave", "equilibrado", "dinamico"):\n'
         '            cfg[k] = v\n            continue\n'
         '        if k == "variedade_motion" and v in ("consistente", "criativa", "maxima"):\n'
         '            cfg[k] = v\n            continue\n'
         '        if k == "edicao" and v in ("motion", "anterior"):') ,
        ("    contexto_direcao=preparar_direcao(dados,proj,base,cfg.get('motion_pedido','')) if modo_edicao=='motion' else None",
         "    contexto_direcao=preparar_direcao(dados,proj,base,cfg.get('motion_pedido','')) if modo_edicao=='motion' else None\n"
         "    if contexto_direcao:\n"
         "        contexto_direcao={**contexto_direcao,\n"
         "                          'intensidade_motion':cfg.get('intensidade_motion','equilibrado'),\n"
         "                          'variedade_motion':cfg.get('variedade_motion','criativa')}"),
    ]
    for i, (o, n) in enumerate(repl):
        t = aplicar(t, o, n, f"criar.py, alteracao {i+1}")
    return t


def patch_painel(t: str) -> str:
    repl = [
        ('<div><label>Estilo das imagens de IA</label><select name="estilo" id="estilo"><option value="realista">Realista (foto documental)</option><option value="cinematografico">Cinematográfico</option><option value="editorial">Editorial (revista)</option></select></div>',
         '<div><label>Estilo das imagens de IA</label><select name="estilo" id="estilo"><option value="realista">Realista (foto documental)</option><option value="cinematografico">Cinematográfico</option><option value="editorial">Editorial (revista)</option></select></div>\n'
         '<div><label>Movimento do Motion</label><select name="intensidade_motion" id="intensidade_motion"><option value="suave">Suave</option><option value="equilibrado" selected>Equilibrado</option><option value="dinamico">Dinâmico</option></select></div>\n'
         '<div><label>Variedade de composição</label><select name="variedade_motion" id="variedade_motion"><option value="consistente">Consistente</option><option value="criativa" selected>Criativa</option><option value="maxima">Máxima</option></select></div>'),
        ('const CAMPOS=["tema","lote","descricao","narrativa","serio","duracao","pesquisar","estilo","edicao"];',
         'const CAMPOS=["tema","lote","descricao","narrativa","serio","duracao","pesquisar","estilo","edicao","intensidade_motion","variedade_motion"];'),
        ('$("#estilo").value="realista";$("#edicao").value="motion";arqs=[];',
         '$("#estilo").value="realista";$("#edicao").value="motion";$("#intensidade_motion").value="equilibrado";$("#variedade_motion").value="criativa";arqs=[];'),
        ("ajustes={'edicao':campos.get('edicao') if campos.get('edicao') in ('motion','anterior') else 'motion'}",
         "ajustes={'edicao':campos.get('edicao') if campos.get('edicao') in ('motion','anterior') else 'motion'}\n"
         "    if campos.get('intensidade_motion') in ('suave','equilibrado','dinamico'):\n"
         "        ajustes['intensidade_motion']=campos['intensidade_motion']\n"
         "    if campos.get('variedade_motion') in ('consistente','criativa','maxima'):\n"
         "        ajustes['variedade_motion']=campos['variedade_motion']"),
    ]
    for i, (o, n) in enumerate(repl):
        t = aplicar(t, o, n, f"painel.py, alteracao {i+1}")
    return t


def patch_motion_ts(t: str) -> str:
    repl = [
        ("import {CenaVariacao} from './Variacoes';",
         "import {CenaVariacao} from './Variacoes';\nimport {CenaPro} from './CenasPro';"),
        ("{c.motion?.layout==='demonstracao'||(c.motion?.variante||0)>0?<CenaVariacao c={c} dur={dur}/>:<Component c={c} dur={dur}/>}" ,
         "{['palavra','dividida','profundidade'].includes(c.motion?.layout||'')?<CenaPro c={c} dur={dur}/>:c.motion?.layout==='demonstracao'||(c.motion?.variante||0)>0?<CenaVariacao c={c} dur={dur}/>:<Component c={c} dur={dur}/>}"),
        ("camera=c.motion?.camera||0,dx=camera===1?(q-.5)*16:camera===3?Math.sin(q*Math.PI)*8:0,dy=camera===2?(q-.5)*14:0;",
         "camera=c.motion?.camera||0,forca=({'suave':.6,'equilibrado':1,'dinamico':1.45} as Record<string,number>)[c.motion?.movimento_intensidade||'equilibrado']||1,dx=(camera===1?(q-.5)*16:camera===3?Math.sin(q*Math.PI)*8:0)*forca,dy=(camera===2?(q-.5)*14:0)*forca;"),
        ("scale(${1+q*.018})", "scale(${1+q*.018*forca})"),
    ]
    for i, (o, n) in enumerate(repl):
        t = aplicar(t, o, n, f"Motion.tsx, alteracao {i+1}")
    return t


def patch_base_ts(t: str) -> str:
    return aplicar(t, "export type PlanoMotion={variante?:number;",
                   "export type PlanoMotion={intencao?:string;intensidade?:string;movimento_intensidade?:string;foco?:number;densidade?:number;movimento?:number;variante?:number;",
                   "Base.tsx, tipos do plano")


PATCHERS = {
    "motion_editor.py": patch_motion_editor,
    "motion_variacao.py": patch_variacao,
    "criar.py": patch_criar,
    "painel.py": patch_painel,
    "src/showcase/Motion.tsx": patch_motion_ts,
    "src/showcase/Base.tsx": patch_base_ts,
}


def localizar_editor() -> Path:
    base = RAIZ_PACOTE
    candidatos = [base.parent, base.parent / "editor", base, Path.cwd(), Path.cwd() / "editor"]
    for c in candidatos:
        if (c / "motion_editor.py").is_file() and (c / "painel.py").is_file():
            return c.resolve()
    print("\nSelecione a pasta de instalacao do editor (que contem painel.py).")
    pasta = None
    try:
        import tkinter as tk
        from tkinter import filedialog
        raiz = tk.Tk()
        raiz.withdraw()
        pasta = filedialog.askdirectory(title="Selecione a pasta onde fica painel.py")
        raiz.destroy()
    except Exception:
        pass
    if not pasta:
        pasta = input("Cole o caminho da pasta do editor aqui: ").strip().strip('"')
    if not pasta:
        raise RuntimeError("Nenhuma pasta foi escolhida.")
    p = Path(pasta).expanduser().resolve()
    if (p / "editor" / "motion_editor.py").is_file():
        p /= "editor"
    if not (p / "motion_editor.py").is_file() or not (p / "painel.py").is_file():
        raise RuntimeError("Pasta invalida: nao achei motion_editor.py e painel.py.")
    return p


def atomic_write(destino: Path, data: bytes) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp: Path | None = None
    try:
        fd, nome = tempfile.mkstemp(prefix=".motion-pro-", suffix=destino.suffix, dir=destino.parent)
        tmp = Path(nome)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, destino)
    finally:
        if tmp and tmp.exists():
            tmp.unlink()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def instalar() -> int:
    print("\n=== MOTION PRO - ATUALIZACAO OFFLINE PARA WINDOWS ===")
    print("O GitHub nao sera acessado nem modificado.")
    print("Feche o painel e termine as renderizacoes antes de instalar.\n")
    editor = localizar_editor()
    print("Editor selecionado:", editor)
    if not (editor / "src" / "showcase" / "Motion.tsx").is_file():
        raise RuntimeError("Estrutura do editor incompleta: falta src/showcase/Motion.tsx.")
    alteracoes: dict[str, bytes] = {}
    backup_files: dict[str, bytes] = {}
    # Analise TODAS as alterações antes de escrever qualquer arquivo.
    for rel, patcher in PATCHERS.items():
        alvo = editor / rel
        anterior = alvo.read_bytes()
        atual = patcher(anterior.decode("utf-8"))
        if rel.endswith(".py"):
            ast.parse(atual, filename=rel)
        if atual.encode("utf-8") != anterior:
            alteracoes[rel] = atual.encode("utf-8")
            backup_files[rel] = anterior
    for rel in NOVOS:
        origem = RAIZ_PACOTE / "editor" / rel
        dados = origem.read_bytes()
        if rel.endswith(".py"):
            ast.parse(dados.decode("utf-8"), filename=rel)
        destino = editor / rel
        if destino.exists():
            anterior = destino.read_bytes()
            if anterior != dados:
                backup_files[rel] = anterior
                alteracoes[rel] = dados
        else:
            alteracoes[rel] = dados
    if not alteracoes:
        print("\nTudo ja esta atualizado. Nada foi substituido.")
        return 0
    rotulo = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_backup = editor / ("_BACKUP_MOTION_PRO_" + rotulo)
    indice = 2
    while base_backup.exists():
        base_backup = editor / (f"_BACKUP_MOTION_PRO_{rotulo}_{indice}")
        indice += 1
    base_backup.mkdir(parents=True)
    manifesto = {"versao": "2.0-local-offline", "editor": str(editor),
                 "data": dt.datetime.now().isoformat(timespec="seconds"),
                 "arquivos": {}, "criados": [], "pacote": "Motion Pro PC"}
    # Backup de todos os originais com verificacao.
    for rel, dados in backup_files.items():
        destino = base_backup / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(dados)
        if destino.read_bytes() != dados:
            raise OSError(f"Falha ao confirmar backup de {rel}")
        manifesto["arquivos"][rel] = {"sha256": sha(dados)}
    manifesto["criados"] = [rel for rel in alteracoes if not (editor / rel).exists()]
    (base_backup / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    instalados = []
    try:
        for rel, dados in alteracoes.items():
            atomic_write(editor / rel, dados)
            instalados.append(rel)
            print("Atualizado:", rel)
    except Exception:
        print("Falha durante a copia. Restaurando arquivos do backup...")
        for rel in reversed(instalados):
            try:
                if rel in backup_files:
                    atomic_write(editor / rel, backup_files[rel])
                else:
                    (editor / rel).unlink(missing_ok=True)
            except OSError as e:
                print("ATENCAO: restauracao manual necessaria:", rel, e)
        raise
    (editor / "_ULTIMO_BACKUP_MOTION_PRO.txt").write_text(str(base_backup), encoding="utf-8")
    print("\nSUCESSO. Arquivos atualizados:", len(alteracoes))
    print("Backup salvo em:", base_backup)
    print("Se necessario, use RESTAURAR_BACKUP.bat deste pacote.")
    print("Suas vozes, config.json, videos, modelos e projetos nao foram alterados.")
    return 0


def restaurar() -> int:
    editor = localizar_editor()
    ponteiro = editor / "_ULTIMO_BACKUP_MOTION_PRO.txt"
    if not ponteiro.is_file():
        raise RuntimeError("Nao encontrei o endereco do backup mais recente.")
    backup = Path(ponteiro.read_text(encoding="utf-8").strip())
    manifesto = json.loads((backup / "manifesto.json").read_text(encoding="utf-8"))
    for rel, inf in manifesto["arquivos"].items():
        conteudo = (backup / rel).read_bytes()
        if sha(conteudo) != inf["sha256"]:
            raise RuntimeError(f"Backup corrompido: {rel}")
    for rel, inf in manifesto["arquivos"].items():
        atomic_write(editor / rel, (backup / rel).read_bytes())
        print("Restaurado:", rel)
    for rel in manifesto["criados"]:
        (editor / rel).unlink(missing_ok=True)
        print("Removido (criado pela atualizacao):", rel)
    print("\nVersao anterior restaurada. Seus dados foram preservados.")
    ponteiro.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    try:
        status = restaurar() if "--restaurar" in sys.argv else instalar()
    except (OSError, UnicodeError, SyntaxError, ValueError, RuntimeError) as e:
        print("\nERRO:", e)
        status = 1
    sys.exit(status)
