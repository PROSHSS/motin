"""Direção da edição principal; preserva fala, fontes, números e arquivos de voz."""
import copy
import hashlib
import json
import math
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path
from motion_variacao import planejar_variedade, detalhes_visual, numero_aleatorio, acao
from motion_inteligencia import analisar_roteiro, adequacao, escolher_cenas_midia
VERSAO_MOTION='motion-contextual-v8.1'
LAYOUTS=('impacto','morph','interface','colagem','orbita','recorte','tipografia','comparativo','sequencia','editorial','dados','demonstracao','palavra','dividida','profundidade')
STOP=set('a o as os um uma de da do das dos e em no na nos nas por para com que se ao aos ou mas mais como seu sua seus suas esse essa isso este esta aqui voce vai vou ele ela muito'.split())

STOP.update('quer pesquise proteja converse transforme observe imprima percorra assista acompanhe aprenda entenda deixe veja mostre traga use conecte construa misture alterne continue repare precisa acompanhar querer fazer mostrar sendo esta deve pode cada todo toda sem agora'.split())

def norm(t):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(t).lower()) if not unicodedata.combining(c))

def tokens(t):
    return re.findall(r'[\wÀ-ÿ%$]+',norm(t))

def frases(t):
    out=[]
    for parte in re.split(r'(?<=[.!?;:])\s+|,\s+', ' '.join(str(t).split())):
        p=parte.split()
        while len(p)>8:
            k=6
            while k>3 and norm(p[k-1]).strip('.,!?') in STOP:k-=1
            out.append(' '.join(p[:k]));p=p[k:]
        if p:out.append(' '.join(p))
    return out[:5]

def chaves(t):
    out=[]
    for w in re.findall(r'[\wÀ-ÿ%$-]+',t):
        if len(w)>3 and norm(w) not in STOP and norm(w) not in [norm(p) for p in out]:out.append(w)
    return out[:5] or t.split()[:2]

def icone(t):
    t=norm(t)
    for terms,name in [(('video','live','assist','gravar'),'Play'),(('dinheiro','preco','valor','custo'),'Coins'),(('segur','proteg','privac'),'ShieldCheck'),(('mensag','convers','coment'),'MessageCircle'),(('pessoa','publico','gente'),'Users'),(('busca','pesquis','procur'),'Search'),(('tempo','hora','minuto'),'Clock'),(('document','regra'),'FileText'),(('celular','tela','aplicativo','toque'),'Smartphone'),(('mundo','internet','rede'),'Globe'),(('ideia','entender','aprend','explic'),'Lightbulb')]:
        if any(x in t for x in terms):return name
    return 'Layers'

def registrar_video(proj,arquivo,cena=None,inicio='',fim=''):
    from mascote import sondar_video
    m=sondar_video(arquivo)
    try:a=float(inicio or 0);b=float(fim) if str(fim).strip() else m['duracao']
    except (ValueError,TypeError):raise ValueError('Informe início e fim do trecho em segundos.')
    if not math.isfinite(a) or not math.isfinite(b) or not 0<=a<b<=m['duracao']+.05 or b-a<.15:raise ValueError('Confira o início e o fim do trecho dentro da duração do vídeo.')
    return {'arquivo':arquivo.relative_to(proj).as_posix(),'cena':cena,'inicio':a,'fim':min(b,m['duracao']),**m}

def preparar_midias(proj,dados):
    manifest=proj/'midias_principal.json'
    if not manifest.exists():
        antigas=[]
        for a in sorted(proj.iterdir()):
            m=re.match(r'^(?:cena(\d+)_|envio\d+_)',a.name)
            if a.is_file() and m and a.suffix.lower() in ('.mp4','.mov','.webm','.mkv','.m4v'):antigas.append(registrar_video(proj,a,int(m.group(1)) if m.group(1) else None))
        if not antigas:return
        manifest.write_text(json.dumps(antigas,ensure_ascii=False,indent=2),encoding='utf-8')
    midias=json.loads(manifest.read_text(encoding='utf-8'));fixos={};livres=[]
    for m in midias:
        origem=(proj/m['arquivo']).resolve()
        if not origem.is_relative_to(proj.resolve()) or not origem.is_file():raise ValueError('Um vídeo está faltando ou fora do projeto.')
        alvo=proj/'public'/m['arquivo'];alvo.parent.mkdir(parents=True,exist_ok=True)
        if not alvo.exists() or alvo.stat().st_size!=origem.stat().st_size:shutil.copyfile(origem,alvo)
        if m.get('cena') is None:livres.append(m)
        elif int(m['cena']) in fixos:raise ValueError('Use apenas um vídeo fixo por cena.')
        else:fixos[int(m['cena'])]=m
    # Busca afinidade de assunto quando arquivo ou metadados permitem.
    # Sem rotulos, mantem distribuicao anterior dos projetos ja existentes.
    mapa=escolher_cenas_midia(dados['cenas'],livres) if livres else {}
    por_cena={indice:livres[j] for j,indice in mapa.items()}
    sem_rotulo=not mapa and not any(
        m.get('descricao') or m.get('etiquetas') for m in livres
    )
    j=0
    for i,c in enumerate(dados['cenas']):
        m=fixos.get(i+1) or por_cena.get(i)
        if m is None and livres and sem_rotulo and (i%2==1 or len(dados['cenas'])==1):
            m=livres[j%len(livres)]
            j+=1
        if m:
            c['video']={k:copy.deepcopy(m[k]) for k in ('arquivo','inicio','fim','duracao')}
            c['video'].update({'automatico':m.get('cena') is None,'trecho_inicio':m['inicio'],'trecho_fim':m['fim']})
            c['credito_video']='Vídeo enviado pelo autor'

def escolher(c,i,n,uso,recentes,plano=None,analise=None):
    plano=plano or {'semente':1,'historico':[]}
    t=norm(c.get('narracao',''));act=acao(t,c)
    if c.get('tipo') in ('grafico','ranking','fato_documento','linha_tempo') or (c.get('cena') or {}).get('tipo') in ('documento','numero_gigante','grafico_barras','grafico_linha','rosca','painel','versus'):return 'original'
    if c.get('numero') or c.get('contador'):return 'dados'
    if c.get('comparacao'):return 'comparativo'
    if c.get('recorte'):op=['recorte','colagem','editorial']
    elif c.get('video'):op=['editorial','colagem','dividida','profundidade']
    elif i==0:op=['impacto','tipografia','palavra']+(['demonstracao'] if act!='observar' else [])
    elif act=='etapas':op=['sequencia','demonstracao','morph','profundidade']
    elif act in ('proteger','buscar','produzir','percorrer','comunicar'):op=['demonstracao','morph','interface','profundidade'] if plano.get('dominio')=='tecnologia' else ['demonstracao','morph','tipografia','profundidade']
    elif any(x in t for x in ('aplicativo','celular','tela','toque','clique','configur')):op=['interface','demonstracao','sequencia','morph']
    elif act=='transformar':op=['morph','demonstracao','comparativo','tipografia','palavra']
    elif act=='conectar':op=['orbita','demonstracao','morph','profundidade']
    elif c.get('foto'):op=['colagem','editorial','tipografia','dividida','profundidade']
    elif i==n-1:op=['tipografia','impacto','morph','palavra']
    else:op=['morph','tipografia','impacto','orbita','demonstracao','palavra','profundidade']
    if n>=7 and i>1 and not any(c.get(x) for x in ('video','numero','contador','comparacao')) and all(uso[x] for x in op):op += [x for x in ('orbita','tipografia','impacto','demonstracao','morph','palavra','profundidade') if x not in op and not uso[x]][:2]
    livres=[x for x in op if x not in recentes[-2:]] or [x for x in op if x not in recentes[-1:]] or op
    historico=plano.get('historico',[])[:6]
    def custo(x):
        passado=sum(sum(z.get('layout')==x for z in h.get('cenas',[]))/(k+2) for k,h in enumerate(historico))
        aberturas=sum(h.get('abertura')==x for h in historico[:3]) if i==0 else 0
        return uso[x]*3+passado*.55+aberturas*2+op.index(x)*.06+numero_aleatorio(plano['semente'],'layout',i,x)*1.2-adequacao(x,analise,c,i,n)*.48
    return min(livres,key=custo)

def dirigir(dados,tempos,palavras,modo='motion',contexto=None):
    for c in dados['cenas']:c.pop('motion',None)
    dados['edicao']=modo
    if modo!='motion':
        dados.pop('direcao_motion',None)
        return dados
    plano=planejar_variedade(dados,contexto)
    fps=int(dados.get('fps') or 30);uso=Counter();recentes=[];cursores={};visuais=[]
    analises=analisar_roteiro(dados['cenas'])
    for i,c in enumerate(dados['cenas']):
        nar=c.get('narracao','')
        if not c.get('foto') and (c.get('cena') or {}).get('imagem'):c['foto']=c['cena']['imagem']
        layout=escolher(c,i,len(dados['cenas']),uso,recentes,plano,analises[i]);uso[layout]+=1;recentes.append(layout)
        tp=tempos[i] if i<len(tempos) else {'inicio':sum(x.get('duracao',3) for x in dados['cenas'][:i]),'fim':sum(x.get('duracao',3) for x in dados['cenas'][:i+1])}
        ini=0 if i==0 else max(0,round(tp['inicio']*fps)-9)/fps;dur=max(.5,tp['fim']-ini)
        v=c.get('video')
        if v and v.get('automatico'):
            a,b=v.get('trecho_inicio',v['inicio']),v.get('trecho_fim',v['fim']);cur=cursores.get(v['arquivo'],a)
            if cur>=b-.2:cur=a
            v['inicio']=round(cur,4);v['fim']=b;cursores[v['arquivo']]=cur+dur
        local=[p for p in palavras if tp['inicio']-.12<=p.get('inicio',0)<tp['fim']];batidas=[];cursor=0;partes=frases(nar)
        for k,texto in enumerate(partes):
            alvo=tokens(texto);at=None
            for j in range(cursor,len(local)):
                span=[w for p in local[j:j+len(alvo)+1] for w in tokens(p['palavra'])]
                if alvo and span[:min(3,len(alvo))]==alvo[:3]:at=max(0,local[j]['inicio']-ini);cursor=j+len(alvo);break
            if at is None:at=.12+k*max(.1,dur-.4)/max(1,len(partes))
            batidas.append({'texto':texto,'em':round(min(at,dur-.15),4),'icone':icone(texto)})
        titulo=' '.join(p.get('t','') for l in (c.get('manchete') or []) for p in l if isinstance(p,dict)).strip()
        if not titulo or len(titulo)>80 or not set(tokens(titulo)).issubset(set(tokens(nar))):
            titulo=re.split(r'(?<=[.!?])\s+',nar)[0]
            if len(titulo)>80:titulo=partes[0] if partes else nar
        c['motion']={'layout':layout,'claro':i%4==2,'indice':i,'titulo':titulo,'chaves':chaves(nar),'icone':icone(nar),'batidas':batidas,'duracao':round(dur,4),'legendas':bool(palavras),'versao':VERSAO_MOTION,'intencao':analises[i]['intencao'],'intensidade':analises[i]['intensidade']}
        detalhes_visual(c,i,plano,visuais)
        visuais.append(c['motion'])
    return dados

def assinatura(dados,proj,modo):
    p=proj/'midias_principal.json'
    s=json.dumps({'modo':modo,'versao':VERSAO_MOTION,'cenas':dados['cenas'],'midias':p.read_text(encoding='utf-8') if p.exists() else ''},sort_keys=True,ensure_ascii=False)
    return hashlib.sha256(s.encode()).hexdigest()
