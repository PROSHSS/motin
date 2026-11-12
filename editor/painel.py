"""
painel.py - painel local (site) para criar videos.

Abre uma pagina no SEU navegador (endereco 127.0.0.1, so o seu computador enxerga).
Voce coloca: tema, descricao, narrativa/fatos, fotos e videos. Ao clicar em OK, o painel guarda tudo na
pasta do projeto e abre uma janela preta (CMD) que cria o video com o criar.py.

Seguranca: usa so o Python que ja vem instalado (nenhum programa extra), escuta somente em 127.0.0.1,
exige uma senha aleatoria a cada abertura, so aceita arquivos de foto/video e nao envia nada para a internet.
"""
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
import tempfile
from voz_referencia import python_voz
from mascote import configurar as configurar_mascote, sondar_video, PERFIS, PERFIS_ANTIGOS, normalizar_perfil
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PORTA = int(os.environ.get("PAINEL_PORTA", "8765"))
TOKEN = secrets.token_urlsafe(16)
TRAVA_VOZ = threading.Lock()
LIMITE = 1500 * 1024 * 1024  # 1,5 GB por envio
FOTOS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEOS = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
SEM_EXECUTAR = bool(os.environ.get("PAINEL_SEM_EXECUTAR"))  # so para teste

PAGINA = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painel de Documentários · Personagens</title>
<link rel="stylesheet" href="/assets/painel-mascote.css">
<script src="/assets/painel-mascote.js?v=voz-referencia6" defer></script>
<style>
:root{--bg:#0b0c0f;--card:#14161b;--tx:#f2f2ee;--su:#9a9a94;--ac:#f0a830;--bd:#262932;--ok:#2fbf6b;--er:#e2635a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.5 "Segoe UI",Arial,sans-serif}
main{max-width:860px;margin:0 auto;padding:26px 18px 90px}
header{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:6px;flex-wrap:wrap}
h1{font-size:28px;margin:0}a.nav{color:var(--ac);text-decoration:none;font-weight:700;border:1px solid var(--bd);padding:8px 14px;border-radius:10px;background:var(--card)}
p.s{color:var(--su);margin:2px 0 22px}
.c{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px;margin-bottom:14px}
label{display:block;font-weight:700;margin:0 0 6px}small{color:var(--su);display:block;margin:5px 0 0;font-size:13px}
input[type=text],textarea,select,input[type=number]{width:100%;background:#0b0c0f;color:var(--tx);border:1px solid var(--bd);border-radius:10px;padding:12px;font:inherit}
input:focus,textarea:focus,select:focus{outline:2px solid var(--ac);border-color:transparent}
textarea{min-height:110px;resize:vertical}
.cnt{float:right;color:var(--su);font-weight:400;font-size:12px}
.drop{border:2px dashed var(--bd);border-radius:12px;padding:26px;text-align:center;color:var(--su);cursor:pointer;transition:.15s}
.drop.on,.drop:hover{border-color:var(--ac);color:var(--tx);background:#1a1c22}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:12px}
.it{background:#0b0c0f;border:1px solid var(--bd);border-radius:10px;overflow:hidden;font-size:12px}
.it .th{height:110px;background:#1a1c22 center/cover no-repeat;display:flex;align-items:center;justify-content:center;color:var(--su)}
.it .nm{padding:6px 8px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.it .ct{display:flex;gap:6px;align-items:center;padding:6px 8px 8px;flex-wrap:wrap}
.it input{padding:5px 6px;border-radius:6px;font-size:12px}.it button{background:none;border:0;color:var(--er);cursor:pointer;margin-left:auto}
.row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}@media(max-width:700px){.row{grid-template-columns:1fr}}
.chk{display:flex;gap:10px;align-items:flex-start;font-weight:400}.chk input{margin-top:5px}
button.ok{width:100%;background:var(--ac);color:#1a1200;border:0;border-radius:12px;padding:17px;font-size:20px;font-weight:800;cursor:pointer}
button.ok:disabled{opacity:.5;cursor:wait}
#msg{margin-top:14px;padding:14px;border-radius:10px;display:none}
#msg.ok{display:block;background:#12301f;border:1px solid var(--ok)}#msg.er{display:block;background:#3a1613;border:1px solid var(--er)}
progress{width:100%;height:10px;margin-top:10px;display:none}
.mini{font-size:13px;color:var(--su)}.lnk{background:none;border:0;color:var(--ac);cursor:pointer;font:inherit;padding:0}
</style></head><body><main>
<header><h1>Painel de Documentários</h1><a class="nav" href="/status" target="_blank">Meus vídeos →</a></header>
<p class="s">Preencha, envie suas fotos e vídeos e clique em OK. Pode sair do PC: nada pergunta nada na janela preta.</p>

<div class="c" id="cf" style="display:none"><label>Cloudflare (uma vez só)</label>
<input type="text" id="cfid" placeholder="Account ID" style="margin-bottom:8px"><input type="text" id="cftk" placeholder="API Token">
<small>Gratuito. Fica só no seu computador (config.json). Sem isso as imagens de IA não são geradas.</small>
<button type="button" id="cfok" style="margin-top:10px;padding:10px 16px;border-radius:8px;border:0;background:var(--ac);font-weight:700;cursor:pointer">Salvar</button></div>

<form id="f">
<div class="c"><label>Tema do vídeo * <span class="cnt" id="c1"></span></label>
<input type="text" name="tema" id="tema" maxlength="160" placeholder="Ex.: O avião secreto da China">
<small>Vira o título e o nome da pasta. Seja específico (nome, fato e ano ajudam a achar fontes).</small></div>

<div class="c"><label>Vários vídeos de uma vez (opcional) <span class="cnt" id="c4"></span></label>
<textarea name="lote" id="lote" maxlength="4000" style="min-height:90px" placeholder="Um tema por linha (até 12). Deixe o campo 'Tema' vazio e clique OK: eles entram na fila e são feitos um após o outro, mesmo com você fora."></textarea>
<small>Vale as opções de duração, estilo e pesquisa abaixo. Não leva arquivos: para fotos suas, use um vídeo por vez.</small></div>

<div class="c"><label>Descrição básica <span class="cnt" id="c2"></span></label>
<textarea name="descricao" id="descricao" maxlength="3000" placeholder="Do que se trata, o ângulo e o que não pode faltar."></textarea></div>

<div class="c"><label>Narrativa pronta ou fatos (opcional) <span class="cnt" id="c3"></span></label>
<textarea name="narrativa" id="narrativa" maxlength="12000" style="min-height:160px" placeholder="Uma frase por linha. Ex.:&#10;O avião foi mostrado em 2024.&#10;Segundo a fonte X, o alcance é de 3.000 km."></textarea>
<small>Cada linha é tratada como fato confiável escolhido por você: o roteiro usa só isso (e a pesquisa, se estiver ligada). Escreva só o que você confirmou.</small></div>

<div class="c"><label>Fotos e vídeos do assunto</label>
<div class="drop" id="drop">Arraste aqui ou clique para escolher<br><small>Fotos: JPG, PNG, WEBP · Vídeos: MP4, MOV, WEBM · em movimento na edição principal</small></div>
<input type="file" id="arq" multiple accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm,video/x-matroska,.jpg,.jpeg,.png,.webp,.mp4,.mov,.webm,.mkv,.m4v" hidden>
<div class="grid" id="lista"></div>
<small id="dica" style="display:none">Dica: o campo "cena" é opcional. Escreva o número da cena (1 = abertura) para fixar aquela foto nela; sem número, o programa distribui.</small>
<label class="chk" style="margin-top:12px"><input type="checkbox" id="dir">
<span>Confirmo que as fotos e vídeos são meus ou que tenho autorização/licença para usá-los. (Obrigatório se enviar arquivos.)</span></label></div>

<div class="c row">
<div><label>Tipo de assunto</label><select name="serio" id="serio"><option value="auto">Automático</option><option value="serio">Sério (política, crime, saúde, dinheiro...)</option><option value="normal">Leve</option></select></div>
<div><label>Duração</label><select name="duracao" id="duracao"><option value="curto">Curto (~50 s)</option><option value="medio" selected>Médio (~65 s)</option><option value="longo">Longo (~80 s)</option></select></div>
<div><label>Pesquisar na internet</label><select name="pesquisar" id="pesquisar"><option value="sim">Sim (fontes e datas atuais)</option><option value="nao">Não (usar só o que escrevi)</option></select></div>
<div><label>Edição principal</label><select name="edicao" id="edicao"><option value="motion">Motion fluido · Novo</option><option value="anterior">Documentário anterior</option></select></div>
<div><label>Estilo das imagens de IA</label><select name="estilo" id="estilo"><option value="realista">Realista (foto documental)</option><option value="cinematografico">Cinematográfico</option><option value="editorial">Editorial (revista)</option></select></div>
<div><label>Movimento do Motion</label><select name="intensidade_motion" id="intensidade_motion"><option value="suave">Suave</option><option value="equilibrado" selected>Equilibrado</option><option value="dinamico">Dinâmico</option></select></div>
<div><label>Variedade de composição</label><select name="variedade_motion" id="variedade_motion"><option value="consistente">Consistente</option><option value="criativa" selected>Criativa</option><option value="maxima">Máxima</option></select></div>
</div>

__MASCOTE_PAINEL__

<div class="c"><b>Sem perguntas.</b> Assunto sério gera um arquivo <i>_CONFERIR.txt</i> ao lado do vídeo, com tudo que é falado e a fonte de cada frase, e <i>TEXTO_NA_TELA.txt</i> na pasta do projeto com todo texto que aparece no vídeo. Leia antes de postar.</div>

<button class="ok" id="ok" type="submit">OK — criar o vídeo</button>
<progress id="pg" max="100" value="0"></progress>
<div id="msg"></div>
<p class="mini">Seu rascunho é salvo automaticamente neste navegador. <button type="button" class="lnk" id="limpar">limpar tudo</button></p>
</form></main>
<script>
const TOKEN="__TOKEN__";const FALTA_CF=__FALTA_CF__;
const $=s=>document.querySelector(s);
if(FALTA_CF)$("#cf").style.display="block";
$("#cfok").onclick=async()=>{const fd=new FormData();fd.set("token",TOKEN);fd.set("cfid",$("#cfid").value);fd.set("cftk",$("#cftk").value);
 const r=await fetch("/cloudflare",{method:"POST",body:fd});const j=await r.json();if(j.ok){$("#cf").style.display="none"}else alert(j.erro)};
// rascunho
const CAMPOS=["tema","lote","descricao","narrativa","serio","duracao","pesquisar","estilo","edicao","intensidade_motion","variedade_motion"];
function salvar(){try{const o={};CAMPOS.forEach(k=>o[k]=$("#"+k).value);localStorage.setItem("painel_rascunho",JSON.stringify(o))}catch(_){}}
function carregar(){try{const o=JSON.parse(localStorage.getItem("painel_rascunho")||"{}");CAMPOS.forEach(k=>{if(o[k]!==undefined)$("#"+k).value=o[k]})}catch(_){}}
function contar(){[["tema","c1",160],["descricao","c2",3000],["narrativa","c3",12000],["lote","c4",4000]].forEach(([i,c,m])=>{$("#"+c).textContent=$("#"+i).value.length+"/"+m})}
carregar();contar();CAMPOS.forEach(k=>$("#"+k).addEventListener("input",()=>{salvar();contar()}));
$("#limpar").onclick=()=>{try{localStorage.removeItem("painel_rascunho")}catch(_){};CAMPOS.forEach(k=>{$("#"+k).value=$("#"+k).defaultValue||(k==="duracao"?"medio":"")});$("#serio").value="auto";$("#pesquisar").value="sim";$("#estilo").value="realista";$("#edicao").value="motion";$("#intensidade_motion").value="equilibrado";$("#variedade_motion").value="criativa";arqs=[];draw();contar();window.mascoteEditor?.limpar()};
// arquivos
let arqs=[];const drop=$("#drop"),inp=$("#arq");
const ext=n=>(n.split(".").pop()||"").toLowerCase();
const OKX=["jpg","jpeg","png","webp","mp4","mov","webm","mkv","m4v"];const VID=["mp4","mov","webm","mkv","m4v"];
function add(fs){for(const f of fs){if(OKX.includes(ext(f.name))&&!arqs.some(a=>a.f.name===f.name&&a.f.size===f.size))arqs.push({f,cena:"",inicio:"",fim:""});}draw();}
function draw(){const l=$("#lista");l.innerHTML="";$("#dica").style.display=arqs.length?"block":"none";
 arqs.forEach((a,i)=>{const d=document.createElement("div");d.className="it";
  const th=document.createElement("div");th.className="th";
  if(VID.includes(ext(a.f.name)))th.textContent="🎬 vídeo";else th.style.backgroundImage="url("+URL.createObjectURL(a.f)+")";
  const nm=document.createElement("div");nm.className="nm";nm.textContent=a.f.name;nm.title=a.f.name;
  const ct=document.createElement("div");ct.className="ct";
  const n=document.createElement("input");n.type="number";n.min=1;n.max=30;n.placeholder="cena";n.value=a.cena;n.style.width="64px";n.oninput=()=>{a.cena=n.value;window.dispatchEvent(new Event("midias-atualizadas"))};
  const b=document.createElement("button");b.type="button";b.textContent="remover";b.onclick=()=>{arqs.splice(i,1);draw()};
  ct.append(n,b);
  if(VID.includes(ext(a.f.name))){const range=document.createElement('div');range.style.cssText='display:flex;gap:8px;width:100%;flex-wrap:wrap';[['inicio','Início (s)'],['fim','Fim (s)']].forEach(([key,label])=>{const wrap=document.createElement('label');wrap.style.cssText='font-size:11px;flex:1;min-width:65px';wrap.textContent=label;const v=document.createElement('input');v.type='number';v.min='0';v.step='0.1';v.placeholder=key==='inicio'?'0':'até o fim';v.value=a[key]||'';v.style.cssText='width:100%;box-sizing:border-box';v.oninput=()=>a[key]=v.value;wrap.append(v);range.append(wrap);});ct.append(range);}
  d.append(th,nm,ct);l.appendChild(d);});window.dispatchEvent(new Event("midias-atualizadas"));}
drop.onclick=()=>inp.click();inp.onchange=()=>{add(inp.files);inp.value=""};
drop.ondragover=e=>{e.preventDefault();drop.classList.add("on")};drop.ondragleave=()=>drop.classList.remove("on");
drop.ondrop=e=>{e.preventDefault();drop.classList.remove("on");add(e.dataTransfer.files)};
function msg(t,c){const m=$("#msg");m.className=c;m.textContent=t}
$("#f").onsubmit=e=>{e.preventDefault();
 if(!$("#tema").value.trim()&&!$("#lote").value.trim()){msg("Digite o tema (ou vários temas, um por linha).","er");return}
 if(arqs.length&&!$("#dir").checked){msg("Marque a confirmação de direitos de uso dos arquivos.","er");return}
 const erroMascote=window.mascoteEditor?.validar();if(erroMascote){msg(erroMascote,"er");return}
 if($("#lote").value.trim()&&!$("#tema").value.trim()&&$("#mascote_ativo")?.checked&&$("#mascote_fundo").value==="video"){msg("Para usar vídeo de fundo, crie um tema por vez.","er");return}
 const fd=new FormData($("#f"));fd.set("token",TOKEN);
 arqs.forEach((a,i)=>{fd.append("arquivos",a.f,a.f.name);fd.set("cena_"+i,a.cena||"");fd.set("inicio_"+i,a.inicio||"");fd.set("fim_"+i,a.fim||"")});
 const x=new XMLHttpRequest();x.open("POST","/enviar");const pg=$("#pg");pg.style.display="block";pg.value=0;$("#ok").disabled=true;msg("Enviando...","ok");
 x.upload.onprogress=ev=>{if(ev.lengthComputable)pg.value=ev.loaded/ev.total*100};
 x.upload.onload=()=>msg("Arquivos enviados. O computador está preparando o vídeo (pode levar alguns segundos com fotos grandes)...","ok");
 x.timeout=300000;x.ontimeout=()=>{pg.style.display="none";msg("Demorou demais. Abra “Meus vídeos”: o vídeo pode ter sido iniciado mesmo assim.","er");$("#ok").disabled=false};
 x.onload=()=>{pg.style.display="none";let r={};try{r=JSON.parse(x.responseText)}catch(_){}
  if(x.status===200&&r.ok){msg("Pronto! "+r.mensagem+" Acompanhe em “Meus vídeos”.","ok");arqs=[];draw();try{localStorage.removeItem("painel_rascunho")}catch(_){}
   $("#tema").value="";$("#lote").value="";$("#descricao").value="";$("#narrativa").value="";contar();$("#ok").disabled=false}
  else{msg("Erro: "+(r.erro||"não consegui enviar."),"er");$("#ok").disabled=false}};
 x.onerror=()=>{pg.style.display="none";msg("Erro: o painel parou. Feche e abra o painel.bat de novo.","er");$("#ok").disabled=false};
 x.send(fd);};
</script></body></html>
"""


def carregar_criar():
    sys.path.insert(0, str(RAIZ))
    import criar  # noqa: E402
    return criar


def nome_seguro(nome):
    base = Path(nome).name
    base = re.sub(r"[^A-Za-z0-9._ -]+", "_", base).strip(" .") or "arquivo"
    return base[:100]


def analisar(corpo, tipo):
    """Le multipart/form-data sem usar 'cgi' (que sumiu nas versoes novas do Python)."""
    msg = BytesParser(policy=policy.HTTP).parsebytes(b"Content-Type: " + tipo.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + corpo)
    campos, arquivos = {}, []
    for parte in msg.iter_parts():
        nome = parte.get_param("name", header="content-disposition")
        arq = parte.get_filename()
        dados = parte.get_payload(decode=True) or b""
        if arq:
            if dados:
                arquivos.append((arq, dados))
        elif nome:
            campos[nome] = dados.decode("utf-8", "replace")
    return campos, arquivos


def ler_config():
    """Le o config.json sem usar o criar.py (que poderia fazer perguntas)."""
    try:
        return json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def pasta_base(criar=None):
    cfg = ler_config()
    return (Path(cfg["pasta_dados"]) if cfg.get("pasta_dados") else RAIZ), cfg


def falta_cloudflare():
    cfg = ler_config()
    return len(str(cfg.get("cf_account_id", ""))) < 16 or len(str(cfg.get("cf_api_token", ""))) < 20


def quadros_do_video(video, destino, prefixo):
    ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ff:
        return []
    try:
        p = subprocess.run([ff, "-hide_banner", "-i", str(video)], capture_output=True, text=True, timeout=60)
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", p.stderr)
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 10.0
    except Exception:
        dur = 10.0
    saidas = []
    for k, frac in enumerate((0.2, 0.5, 0.8), 1):
        out = destino / f"{prefixo}_quadro{k}.jpg"
        r = subprocess.run([ff, "-y", "-loglevel", "error", "-ss", f"{dur * frac:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", "scale='min(1920,iw)':-2", "-q:v", "2", str(out)], capture_output=True, timeout=120)
        if r.returncode == 0 and out.exists() and out.stat().st_size > 1000:
            saidas.append(out)
    return saidas


def criar_trabalho(campos, arquivos):
    criar = carregar_criar()
    tema = re.sub(r"\s+", " ", campos.get("tema", "")).strip()
    if not tema:
        raise ValueError("Digite o tema.")
    cfg_mascote = configurar_mascote(campos)
    falas_exatas = cfg_mascote['ativo'] and campos.get('mascote_falas_exatas') == 'sim'
    if falas_exatas and (not campos.get('narrativa', '').strip() or cfg_mascote['fundo'] != 'video'):
        raise ValueError('Para falas exatas, envie um vídeo de fundo e preencha a narrativa.')
    if cfg_mascote['ativo'] and cfg_mascote['fundo'] == 'video' and not any(Path(n).suffix.lower() in VIDEOS for n, _ in arquivos):
        raise ValueError('Envie um vídeo de fundo ou escolha as cenas do editor.')
    base, cfg = pasta_base(criar)
    # nao sobrescreve um video antigo com o mesmo tema
    # o TEMA fica inteiro (e o titulo do video); so o NOME DA PASTA ganha numero quando ja existe
    nome_pasta = criar.slug(tema)
    if (base / "projetos" / nome_pasta).exists():
        raiz_nome = nome_pasta[:44].rstrip("-")
        n = 2
        while (base / "projetos" / f"{raiz_nome}-{n}").exists():
            n += 1
            if n > 500:
                raise ValueError("Muitos videos com este tema. Mude um pouco o tema.")
        nome_pasta = f"{raiz_nome}-{n}"
    proj = base / "projetos" / nome_pasta
    pasta_fotos = proj / "fotos"
    pasta_fotos.mkdir(parents=True, exist_ok=True)

    avisos, creditos, k = [], [], 0
    cenas_videos = set()
    midias_principal=[]
    for idx, (nome, dados) in enumerate(arquivos):
        ext = Path(nome).suffix.lower()
        if ext not in FOTOS | VIDEOS:
            avisos.append(f"Ignorei {nome} (tipo nao aceito).")
            continue
        k += 1
        cena = campos.get(f"cena_{idx}", "").strip()
        prefixo = f"cena{int(cena)}_" if cena.isdigit() and 1 <= int(cena) <= 30 else f"envio{k:02d}_"
        destino = pasta_fotos / f"{prefixo}{nome_seguro(nome)}"
        destino.write_bytes(dados)
        if ext in VIDEOS and cfg_mascote['ativo'] and cfg_mascote['fundo'] == 'video':
            pasta_midias = proj / 'midias'
            pasta_midias.mkdir(exist_ok=True)
            video = pasta_midias / destino.name
            destino.rename(video)
            cena_video = int(cena) if cena.isdigit() and 1 <= int(cena) <= 30 else None
            if cena_video in cenas_videos:
                raise ValueError('Escolha apenas um vídeo de fundo por cena e apenas um vídeo sem número de cena.')
            cenas_videos.add(cena_video)
            meta = sondar_video(video)
            cfg_mascote['videos'].append({'arquivo': video.relative_to(proj).as_posix(), 'cena': cena_video, **meta})
        elif ext in VIDEOS:
            from motion_editor import registrar_video
            pasta_midias=proj/'midias';pasta_midias.mkdir(exist_ok=True)
            video=pasta_midias/destino.name;destino.rename(video)
            cena_video=int(cena) if cena.isdigit() and 1<=int(cena)<=30 else None
            if cena_video is not None and any(m.get('cena')==cena_video for m in midias_principal):raise ValueError('Use apenas um vídeo fixo por cena.')
            midias_principal.append(registrar_video(proj,video,cena_video,campos.get(f'inicio_{idx}',''),campos.get(f'fim_{idx}','')))
        else:
            creditos.append(f"{destino.name} | proprio")
    if midias_principal:
        (proj/'midias_principal.json').write_text(json.dumps(midias_principal,ensure_ascii=False,indent=2),encoding='utf-8')
    if creditos:
        (pasta_fotos / "creditos.txt").write_text("\n".join(creditos) + "\n", encoding="utf-8")

    if cfg_mascote['ativo']:
        (proj / 'mascote.json').write_text(json.dumps(cfg_mascote, ensure_ascii=False, indent=2), encoding='utf-8')
        if falas_exatas:
            falas = [l.strip() for l in campos['narrativa'].splitlines() if l.strip()]
            if len(falas) > 100:
                raise ValueError('Use no máximo 100 falas, uma por linha.')
            (proj / 'falas_mascote.txt').write_text('\n'.join(falas), encoding='utf-8')

    linhas = []
    desc = re.sub(r"\s+", " ", campos.get("descricao", "")).strip()
    if desc:
        linhas.append(f"Contexto informado pelo autor: {desc}")
    for l in campos.get("narrativa", "").splitlines():
        l = l.strip()
        if l:
            linhas.append(l)
    if linhas:
        (proj / "fatos.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    cmd = [sys.executable, str(RAIZ / "criar.py"), tema]
    s = campos.get("serio", "auto")
    if s == "serio":
        cmd.append("--serio")
    elif s == "normal":
        cmd.append("--normal")
    if campos.get("pesquisar") == "nao":
        cmd.append("--sem-pesquisa")
    ajustes={'edicao':campos.get('edicao') if campos.get('edicao') in ('motion','anterior') else 'motion'}
    if campos.get('intensidade_motion') in ('suave','equilibrado','dinamico'):
        ajustes['intensidade_motion']=campos['intensidade_motion']
    if campos.get('variedade_motion') in ('consistente','criativa','maxima'):
        ajustes['variedade_motion']=campos['variedade_motion']
    if cfg_mascote['ativo']:
        ajustes.update({'mascote_voz': cfg_mascote['voz'], 'ritmo_fala': 1.0})
    if cfg_mascote['ativo'] and cfg_mascote['fundo'] == 'video':
        ajustes.update({'imagens': False, 'fotos_reais': 'nunca'})
        cmd.append('--sem-imagens')
    if falas_exatas:
        ajustes['mascote_falas_exatas'] = True
    dur = campos.get("duracao", "medio")
    if dur in ("curto", "medio", "longo"):
        ajustes["n_pontos"] = {"curto": 8, "medio": 10, "longo": 12}[dur]
    if campos.get("estilo") in ("realista", "cinematografico", "editorial"):
        ajustes["estilo_imagem"] = campos["estilo"]
    job = {"config": ajustes, "cmd": cmd, "tema": tema, "pasta": str(RAIZ), "projeto": str(proj), "video": str(base / "saidas" / (nome_pasta + ".mp4")), "nome_pasta": nome_pasta}
    (proj / "trabalho.json").write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
    return tema, proj, job, avisos, k


def abrir_janela(job_arquivo):
    """Abre uma janela preta (CMD) que roda o trabalho. Sem shell: o texto do tema nunca vira comando."""
    cmd = [sys.executable, str(Path(__file__).resolve()), "--executar", str(job_arquivo)]
    if os.name == "nt":
        subprocess.Popen(cmd, cwd=str(RAIZ), creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen(cmd, cwd=str(RAIZ))


class Handler(BaseHTTPRequestHandler):
    server_version = "Painel"

    def log_message(self, *a):
        pass

    def _host_ok(self):
        h = (self.headers.get("Host") or "").lower()
        return h in (f"127.0.0.1:{PORTA}", f"localhost:{PORTA}")

    def _json(self, codigo, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if not self._host_ok():
            self.send_error(403)
            return
        rota = self.path.split('?')[0]
        if rota.startswith('/mascotes/') or rota.startswith('/assets/'):
            import mimetypes
            nome = rota.rsplit('/', 1)[-1]
            permitidos = {'painel-mascote.css', 'painel-mascote.js'} if rota.startswith('/assets/') else {p + '.png' for p in __import__('mascote').POSES}
            if nome not in permitidos:
                self.send_error(404)
                return
            arquivo = RAIZ / 'assets' / (nome if rota.startswith('/assets/') else 'mascotes/' + nome)
            if not arquivo.is_file():
                self.send_error(404)
                return
            b = arquivo.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(nome)[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(len(b)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(b)
            return
        if self.path.startswith("/arquivo?"):
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            item = _arquivo_do_projeto((q.get("p") or [""])[0], (q.get("t") or [""])[0])
            if not item:
                self.send_error(404)
                return
            arq, mime = item
            tam = arq.stat().st_size
            ini, fim = 0, tam - 1
            rng = self.headers.get("Range")
            parcial = False
            if rng:
                m = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip())
                if m and (m.group(1) or m.group(2)):
                    if m.group(1):
                        ini = int(m.group(1))
                        fim = int(m.group(2)) if m.group(2) else tam - 1
                    else:
                        ini = max(0, tam - int(m.group(2)))
                    fim = min(fim, tam - 1)
                    parcial = ini <= fim
            self.send_response(206 if parcial else 200)
            self.send_header("Content-Type", mime)
            self.send_header("Accept-Ranges", "bytes")
            if parcial:
                self.send_header("Content-Range", f"bytes {ini}-{fim}/{tam}")
            self.send_header("Content-Length", str(fim - ini + 1))
            if (q.get("baixar") or [""])[0]:
                self.send_header("Content-Disposition", f'attachment; filename="{arq.name}"')
            self.end_headers()
            try:
                with open(arq, "rb") as fh:
                    fh.seek(ini)
                    restante = fim - ini + 1
                    while restante > 0:
                        bloco = fh.read(min(1 << 20, restante))
                        if not bloco:
                            break
                        self.wfile.write(bloco)
                        restante -= len(bloco)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if self.path.split("?")[0] == "/status":
            b = pagina_status().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)
            return
        if self.path.split("?")[0] != "/":
            self.send_error(404)
            return
        b = PAGINA.replace("__MASCOTE_PAINEL__", (RAIZ / "mascote_panel.html").read_text(encoding="utf-8")).replace("__TOKEN__", TOKEN).replace("__FALTA_CF__", "true" if falta_cloudflare() else "false").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:")
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        if not self._host_ok() or self.path not in ("/enviar", "/cloudflare", "/retomar", "/abrir", "/voz-mascote"):
            self.send_error(403)
            return
        origem = self.headers.get("Origin")
        if origem and origem not in (f"http://127.0.0.1:{PORTA}", f"http://localhost:{PORTA}"):
            self.send_error(403)
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > LIMITE:
            self._json(413, {"ok": False, "erro": "Envio vazio ou grande demais (limite 1,5 GB)."})
            return
        corpo = self.rfile.read(n)
        try:
            campos, arquivos = analisar(corpo, self.headers.get("Content-Type", ""))
            if not secrets.compare_digest(campos.get("token", ""), TOKEN):
                self._json(403, {"ok": False, "erro": "Senha da pagina invalida. Recarregue a pagina."})
                return
            if self.path == '/voz-mascote':
                perfil = campos.get('perfil', 'referencia')
                if perfil not in PERFIS and perfil not in PERFIS_ANTIGOS:
                    raise ValueError('Perfil de voz inválido.')
                perfil = normalizar_perfil(perfil)
                if not TRAVA_VOZ.acquire(blocking=False):
                    self._json(409, {'ok': False, 'erro': 'Uma amostra de voz já está sendo preparada. Aguarde.'})
                    return
                try:
                    with tempfile.TemporaryDirectory(prefix='mascote-preview-') as tmp:
                        saida = Path(tmp) / 'voz.wav'
                        r = subprocess.run([python_voz(), str(RAIZ / 'tts_mascote.py'), '--perfil', perfil,
                            '--teste', 'Quer entender como isso funciona? Calma, que eu vou te mostrar de um jeito bem simples.',
                            '--saida', str(saida)], cwd=str(RAIZ), capture_output=True, timeout=1800)
                        if r.returncode or not saida.exists():
                            detalhe = r.stderr.decode('utf-8', 'replace').strip().splitlines()
                            mensagem = detalhe[-1].removeprefix('ERRO: ') if detalhe and detalhe[-1].startswith('ERRO: ') else 'Não consegui gerar a voz de referência. Execute o novo instalar_voz_mascote.bat e confira o modelo instalado.'
                            self._json(400, {'ok': False, 'erro': mensagem})
                            return
                        b = saida.read_bytes()
                        self.send_response(200)
                        self.send_header('Content-Type', 'audio/wav')
                        self.send_header('Content-Length', str(len(b)))
                        self.send_header('Cache-Control', 'no-store')
                        self.end_headers()
                        self.wfile.write(b)
                except RuntimeError as e:
                    self._json(400, {'ok': False, 'erro': str(e)})
                except subprocess.TimeoutExpired:
                    self._json(408, {'ok': False, 'erro': 'A amostra demorou mais de 30 minutos. Feche outros programas pesados e confira a instalação.'})
                finally:
                    TRAVA_VOZ.release()
                return
            if self.path == "/abrir":
                nome = campos.get("projeto", "")
                base, _ = pasta_base()
                if not re.fullmatch(r"[a-z0-9-]{1,60}", nome) or not (base / "projetos" / nome).exists():
                    self._json(400, {"ok": False, "erro": "Projeto invalido."})
                    return
                pasta_saida = base / "saidas"
                pasta_saida.mkdir(exist_ok=True)
                if os.name == "nt" and not SEM_EXECUTAR:
                    os.startfile(str(pasta_saida))  # noqa: S606 - pasta fixa, sem texto do usuario
                self._json(200, {"ok": True})
                return
            if self.path == "/retomar":
                nome = campos.get("projeto", "")
                if not re.fullmatch(r"[a-z0-9-]{1,60}", nome):
                    self._json(400, {"ok": False, "erro": "Projeto invalido."})
                    return
                base, _ = pasta_base()
                trab = base / "projetos" / nome / "trabalho.json"
                if not trab.exists():
                    self._json(404, {"ok": False, "erro": "Nao achei o trabalho.json deste projeto."})
                    return
                if campos.get('nova_edicao')=='sim' or campos.get('nova_variacao')=='sim':
                    job_motion=json.loads(trab.read_text(encoding='utf-8'))
                    job_motion['cmd']=[a for a in job_motion['cmd'] if a not in ('--refazer-voz','--novo')]
                    if '--rerender' not in job_motion['cmd']:job_motion['cmd'].append('--rerender')
                    job_motion.setdefault('config',{})['edicao']='motion'
                    if campos.get('nova_variacao')=='sim':
                        pedido=secrets.token_hex(12)
                        job_motion['config']['motion_pedido']=pedido
                        trab=trab.with_name('trabalho_variacao_'+pedido+'.json')
                    else:
                        trab=trab.with_name('trabalho_motion.json')
                    trab.write_text(json.dumps(job_motion,ensure_ascii=False,indent=2),encoding='utf-8')
                if campos.get('nova_voz') == 'sim':
                    mc = base / 'projetos' / nome / 'mascote.json'
                    if not mc.exists() or not json.loads(mc.read_text(encoding='utf-8')).get('ativo'):
                        raise ValueError('Este projeto não usa a narração do personagem.')
                    job_voz = json.loads(trab.read_text(encoding='utf-8'))
                    job_voz['cmd'] = list(job_voz['cmd'])
                    for opcao in ('--refazer-voz', '--rerender'):
                        if opcao not in job_voz['cmd']:
                            job_voz['cmd'].append(opcao)
                    trab = trab.with_name('trabalho_voz.json')
                    trab.write_text(json.dumps(job_voz, ensure_ascii=False, indent=2), encoding='utf-8')
                if not SEM_EXECUTAR:
                    abrir_janela(trab)
                self._json(200, {"ok": True})
                return
            if self.path == "/cloudflare":
                i, t = campos.get("cfid", "").strip(), campos.get("cftk", "").strip()
                if not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", i) or not re.fullmatch(r"[A-Za-z0-9_-]{20,200}", t):
                    self._json(400, {"ok": False, "erro": "Account ID ou token com formato estranho. Copie de novo, sem espacos."})
                    return
                cfg = ler_config()
                cfg["cf_account_id"], cfg["cf_api_token"] = i, t
                (RAIZ / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
                self._json(200, {"ok": True})
                return
            lote = [re.sub(r"\s+", " ", x).strip() for x in campos.get("lote", "").splitlines() if x.strip()][:12]
            if lote and not campos.get("tema", "").strip():
                feitos = []
                for tema_i in lote:
                    t_, proj_, job_, av_, k_ = criar_trabalho({**campos, "tema": tema_i}, [])
                    feitos.append(t_)
                    if not SEM_EXECUTAR:
                        abrir_janela(proj_ / "trabalho.json")
                        time.sleep(1.5)
                self._json(200, {"ok": True, "mensagem": f"{len(feitos)} videos na fila (um por vez): " + "; ".join(feitos) + "."})
                return
            tema, proj, job, avisos, k = criar_trabalho(campos, arquivos)
            if not SEM_EXECUTAR:
                abrir_janela(proj / "trabalho.json")
            msg = f"Janela preta aberta criando \"{tema}\" ({k} arquivo(s) recebido(s)). O video fica em saidas\\."
            if avisos:
                msg += " Avisos: " + " ".join(avisos)
            self._json(200, {"ok": True, "mensagem": msg})
        except ValueError as e:
            self._json(400, {"ok": False, "erro": str(e)})
        except Exception as e:  # noqa: BLE001
            self._json(500, {"ok": False, "erro": f"{type(e).__name__}: {e}"})


def _sem_quickedit():
    """No Windows, clicar na janela preta PAUSA o programa. Isto desliga esse comportamento."""
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-10)
        modo = ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(modo)):
            k.SetConsoleMode(h, (modo.value | 0x80) & ~0x40)  # liga EXTENDED_FLAGS, desliga QUICK_EDIT
    except Exception:
        pass


def _gravar_status(pasta, **kw):
    arq = Path(pasta) / "status.json"
    try:
        atual = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        atual = {}
    atual.update(kw)
    arq.write_text(json.dumps(atual, ensure_ascii=False), encoding="utf-8")


def executar(job_arquivo):
    """Roda dentro da janela preta: nunca pergunta nada, grava tudo em log.txt e em status.json."""
    _sem_quickedit()
    job = json.loads(Path(job_arquivo).read_text(encoding="utf-8"))
    proj = Path(job["projeto"])
    logf = proj / "log.txt"
    print("=" * 60)
    print(" Criando o video:", job["tema"])
    print(" Pode sair do PC: nada vai pedir resposta. Acompanhe em 'Meus videos' no painel.")
    print("=" * 60)
    _gravar_status(proj, estado="fila", inicio=time.strftime("%d/%m/%Y %H:%M:%S"), tema=job["tema"], video=job.get("video", ""))
    # um video por vez (o PC nao aguenta dois ao mesmo tempo): espera a vez
    trava = RAIZ / ".fila_painel"
    esperou = False
    while True:
        try:
            fd = os.open(str(trava), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - trava.stat().st_mtime > 45 * 60:  # trava velha (janela fechada no meio)
                    trava.unlink()
                    continue
            except OSError:
                pass
            if not esperou:
                print("Ha outro video sendo criado. Este entra na fila e comeca sozinho quando o outro terminar.")
                _gravar_status(proj, estado="fila")
                esperou = True
            time.sleep(10)
    _gravar_status(proj, estado="rodando", inicio=time.strftime("%d/%m/%Y %H:%M:%S"), tema=job["tema"], video=job.get("video", ""))
    env = dict(os.environ, CRIAR_CONFIG_JSON=json.dumps(job.get("config") or {}), CRIAR_NOME_PROJETO=job.get("nome_pasta", ""), CRIAR_SEM_PERGUNTAS="1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    codigo = -1
    ultimo = time.time()
    with open(logf, "a", encoding="utf-8", errors="replace") as lf:
        try:
            p = subprocess.Popen(job["cmd"], cwd=job["pasta"], env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for linha in p.stdout:
                try:
                    print(linha, end="")
                except UnicodeEncodeError:
                    print(linha.encode("ascii", "replace").decode(), end="")
                lf.write(linha)
                lf.flush()
                if time.time() - ultimo > 30:
                    ultimo = time.time()
                    try:
                        os.utime(str(trava), None)
                    except OSError:
                        pass
            codigo = p.wait()
        except Exception as e:  # noqa: BLE001
            lf.write(f"\nERRO do painel: {type(e).__name__}: {e}\n")
            print(f"ERRO do painel: {type(e).__name__}: {e}")
    try:
        trava.unlink()
    except OSError:
        pass
    video = Path(job.get("video", ""))
    ok = codigo == 0 and video.exists()
    _gravar_status(proj, estado="pronto" if ok else "erro", fim=time.strftime("%d/%m/%Y %H:%M:%S"), codigo=codigo)
    print()
    if ok:
        print("PRONTO! Video em:", video)
    else:
        print(f"O PROGRAMA PAROU COM ERRO (codigo {codigo}). O texto completo esta em: {logf}")
        print("Tambem aparece em 'Meus videos' no painel. Esta janela fica aberta.")
    # nao pede nada: a janela so fica aberta para voce ler (feche quando quiser)
    while True:
        time.sleep(3600)


def _progresso(log_txt):
    """Le o log e devolve (percentual 0-100, texto da etapa)."""
    etapa, total, nome = 0, 6, ""
    for m in re.finditer(r"\[(\d+)/(\d+)\]\s+(.+)", log_txt):
        etapa, total, nome = int(m.group(1)), int(m.group(2)), m.group(3).strip()
    ren = re.findall(r"Rendered (\d+)/(\d+)", log_txt)
    pct = 0.0
    if etapa:
        pct = (etapa - 1) / max(1, total) * 100
    if ren and etapa >= 5:
        a, b = map(int, ren[-1])
        pct = (4 + a / max(1, b)) / max(1, total) * 100
    return min(99, round(pct)), (f"Etapa {etapa}/{total}: {nome}" if etapa else "Preparando...")


def pagina_status():
    base, _ = pasta_base()
    itens = []
    for st in sorted((base / "projetos").glob("*/status.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
        try:
            d = json.loads(st.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        pasta = st.parent
        lg = ""
        lf = pasta / "log.txt"
        if lf.exists():
            lg = lf.read_text(encoding="utf-8", errors="replace")[-6000:]
        estado = d.get("estado")
        cor = {"pronto": "#2fbf6b", "erro": "#e2635a"}.get(estado, "#f0a830")
        rot = {"pronto": "PRONTO", "erro": "ERRO", "rodando": "CRIANDO...", "fila": "NA FILA"}.get(estado, "?")
        video = Path(d.get("video", "x.mp4"))
        slug_ = html_escape(pasta.name)
        corpo = ""
        if estado in ("rodando", "fila"):
            pct, txt = _progresso(lg)
            corpo += f"<div class='barra'><div style='width:{pct}%'></div></div><small>{html_escape(txt)} · {pct}%</small>"
        if estado == "pronto" and video.exists():
            corpo += (f"<video controls preload='metadata' style='width:100%;max-width:340px;border-radius:12px;background:#000;margin:10px 0' "
                      f"src='/arquivo?p={slug_}&t=video'></video><div class='bt'>"
                      f"<a href='/arquivo?p={slug_}&t=video&baixar=1'>Baixar vídeo</a>"
                      + (f"<a href='/arquivo?p={slug_}&t=capa&baixar=1'>Baixar capa</a>" if video.with_name(video.stem + "_capa.png").exists() else "")
                      + f"<a href='/arquivo?p={slug_}&t=postagem' target='_blank'>Pacote de postagem</a>"
                      f"<a href='/arquivo?p={slug_}&t=legenda' target='_blank'>Legenda do post</a>"
                      f"<a href='/arquivo?p={slug_}&t=texto' target='_blank'>Texto na tela</a>"
                      + (f"<a href='/arquivo?p={slug_}&t=conferir' target='_blank' style='background:#f0a830;color:#1a1200'>CONFERIR antes de postar</a>" if video.with_name(video.stem + "_CONFERIR.txt").exists() else "")
                      + f"<button onclick=\"abrir('{slug_}')\">Abrir pasta</button></div>")
        try:
            rel = json.loads((pasta / "relatorio.json").read_text(encoding="utf-8")) if estado == "pronto" else None
        except (OSError, ValueError):
            rel = None
        if rel:
            vc = "#2fbf6b" if rel["veredito"].startswith("PRONTO") else ("#e2635a" if rel["veredito"].startswith("NAO") else "#f0a830")
            corpo += (f"<div style='border:1px solid {vc};border-radius:10px;padding:10px 14px;margin:8px 0'><b style='color:{vc}'>{html_escape(rel['veredito'])}</b><ul style='margin:6px 0 0;padding-left:18px;font-size:14px'>"
                      + "".join(f"<li>{'✔' if i['ok'] else '⚠'} {html_escape(i['txt'])}</li>" for i in rel["itens"])
                      + ("<li>⚠ Assunto sério: leia o CONFERIR antes de postar</li>" if rel.get("serio") else "") + "</ul></div>")
        if estado == "erro":
            corpo += (f"<p><button class='tent' onclick=\"retomar('{slug_}',this)\">Tentar de novo (continua de onde parou)</button></p>")
        elif estado == 'pronto':
            try:
                usa_mascote = json.loads((pasta / 'mascote.json').read_text(encoding='utf-8')).get('ativo')
            except (OSError, ValueError):
                usa_mascote = False
            if usa_mascote:
                corpo += f"<p><button class='tent' onclick=\"vozbr('{slug_}',this)\">Refazer com voz de referência</button></p>"
            if not usa_mascote:
                corpo += f"<p><button class='tent' onclick=\"motionnovo('{slug_}',this)\">Atualizar edição · manter voz</button></p>"
                corpo += f"<p><button class='tent' onclick=\"variarnovo('{slug_}',this)\">Nova variação · manter voz</button></p>"
        itens.append(
            f"<div class='c'><span style='color:{cor};font-weight:800'>{rot}</span> &nbsp; <b>{html_escape(d.get('tema', pasta.name))}</b>"
            f"<br><small>início {html_escape(d.get('inicio', ''))} · fim {html_escape(d.get('fim', '-'))}</small>{corpo}"
            f"<details {'open' if estado == 'erro' else ''}><summary>Ver o que aconteceu (log)</summary><pre>{html_escape(lg)}</pre></details></div>"
        )
    corpo = "".join(itens) or "<p>Nenhum vídeo ainda.</p>"
    return ("<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta http-equiv='refresh' content='15'>"
            "<title>Meus vídeos</title><style>body{background:#0b0c0f;color:#f2f2ee;font:16px Segoe UI,Arial;margin:0}main{max-width:860px;margin:0 auto;padding:24px 18px}"
            ".c{background:#14161b;border:1px solid #262932;border-radius:14px;padding:16px;margin-bottom:14px}pre{white-space:pre-wrap;background:#0b0c0f;padding:10px;border-radius:8px;font-size:12px;max-height:360px;overflow:auto}"
            "small{color:#9a9a94}a{color:#f0a830}.barra{height:10px;background:#262932;border-radius:6px;margin:10px 0 4px;overflow:hidden}.barra div{height:100%;background:#f0a830}"
            ".bt{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}.bt a,.bt button{background:#1f222a;border:1px solid #262932;border-radius:8px;padding:8px 12px;color:#f2f2ee;text-decoration:none;cursor:pointer;font:inherit;font-size:14px}"
            ".tent{background:#f0a830;border:0;border-radius:8px;padding:10px 16px;font-weight:800;cursor:pointer}</style></head><body><main><h1>Meus vídeos</h1>"
            "<p><a href='/'>← voltar ao painel</a> · a página se atualiza sozinha</p>" + corpo +
            "</main><script>const TOKEN='" + TOKEN + "';"
            "async function post(u,p,b){const fd=new FormData();fd.set('token',TOKEN);fd.set('projeto',p);const r=await fetch(u,{method:'POST',body:fd});return r.json()}"
            "async function retomar(p,b){b.disabled=true;const j=await post('/retomar',p);alert(j.ok?'Janela preta aberta. O vídeo continua de onde parou.':('Erro: '+j.erro));b.disabled=false}"
            "async function variarnovo(p,b){b.disabled=true;const fd=new FormData();fd.set('token',TOKEN);fd.set('projeto',p);fd.set('nova_variacao','sim');try{const r=await fetch('/retomar',{method:'POST',body:fd});const j=await r.json();alert(j.ok?'Criando outra montagem com a mesma narração. Acompanhe nesta página.':('Erro: '+j.erro))}catch(e){alert('Não consegui iniciar. Confira se o painel está aberto.')}finally{b.disabled=false}}"
            "async function motionnovo(p,b){b.disabled=true;const fd=new FormData();fd.set('token',TOKEN);fd.set('projeto',p);fd.set('nova_edicao','sim');try{const r=await fetch('/retomar',{method:'POST',body:fd});const j=await r.json();alert(j.ok?'Atualizando a edição e mantendo a narração. Acompanhe nesta página.':('Erro: '+j.erro))}catch(e){alert('Não consegui iniciar. Confira se o painel está aberto.')}finally{b.disabled=false}}"
            "async function vozbr(p,b){b.disabled=true;const fd=new FormData();fd.set('token',TOKEN);fd.set('projeto',p);fd.set('nova_voz','sim');try{const r=await fetch('/retomar',{method:'POST',body:fd});const j=await r.json();alert(j.ok?'Gerando a narração com sua voz de referência. Acompanhe a atualização nesta página.':('Erro: '+j.erro))}catch(e){alert('Não consegui iniciar. Confira se o painel está aberto.')}finally{b.disabled=false}}"
            "async function abrir(p){const j=await post('/abrir',p);if(!j.ok)alert('Erro: '+j.erro)}</script></body></html>")


def _arquivo_do_projeto(nome, tipo):
    """Resolve um arquivo do projeto SO dentro das pastas permitidas (sem caminhos livres)."""
    if not re.fullmatch(r"[a-z0-9-]{1,60}", nome or ""):
        return None
    base, _ = pasta_base()
    pasta = base / "projetos" / nome
    try:
        st = json.loads((pasta / "status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    video = Path(st.get("video", ""))
    if video.parent.resolve() != (base / "saidas").resolve():
        return None
    mapa = {"video": (video, "video/mp4"), "capa": (video.with_name(video.stem + "_capa.png"), "image/png"),
            "conferir": (video.with_name(video.stem + "_CONFERIR.txt"), "text/plain; charset=utf-8"),
            "texto": (pasta / "TEXTO_NA_TELA.txt", "text/plain; charset=utf-8"),
            "legenda": (pasta / "legenda_post.txt", "text/plain; charset=utf-8"),
            "postagem": (video.with_name(video.stem + "_POSTAGEM.txt"), "text/plain; charset=utf-8"),
            "relatorio": (pasta / "RELATORIO.txt", "text/plain; charset=utf-8")}
    item = mapa.get(tipo)
    return item if item and item[0].exists() else None


def html_escape(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--executar":
        executar(sys.argv[2])
        return
    srv = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    url = f"http://127.0.0.1:{PORTA}/"
    print("=" * 60)
    print(" PAINEL DE DOCUMENTARIOS")
    print(" Endereco (so o seu computador acessa):", url)
    print(" Deixe esta janela aberta enquanto usa o painel. Feche-a para encerrar.")
    print("=" * 60)
    if not os.environ.get("PAINEL_SEM_NAVEGADOR"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
