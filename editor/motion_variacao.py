"""Identidade por projeto, memória de montagens concluídas e vocabulário visual."""
import hashlib
import json
import re
import secrets
import sqlite3
import tempfile
import unicodedata
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from motion_inteligencia import assinatura_visual

VERSAO_DIRECAO='direcao-contextual-v8.1'
DOMINIOS={
 'tecnologia':(r'\b(tiktok|live|lives|aplicativo|celular|tela|software|computador|internet|digital|interface|botao|clique|configuracao|gravacao|video|videos)\b',('Smartphone','Play','MessageCircle'),('#c7fb65','#67e8f9','#c4b5fd')),
 'financas':(r'\b(dinheiro|financiamento|parcela|parcelas|banco|bancos|economia|custo|custos|preco|precos|orcamento|salario|juros|pagamento|pagar|reais)\b',('Wallet','Coins','CreditCard'),('#79efb4','#f9cf78','#7fb7ff')),
 'saude':(r'\b(saude|medico|medica|hospital|sono|dormir|exercicio|exercicios|energia|alimentacao|corpo|respirar|treino)\b',('HeartPulse','Heart','Activity'),('#6ee7c8','#a5b4fc','#abd979')),
 'mobilidade':(r'\b(carro|carros|motor|polo|uber|rodovia|viagem|transito|estrada|trajeto|rota|quilometros|combustivel|dirigir)\b',('Car','MapPin','Route'),('#ff9b75','#76d8ee','#e8d07c')),
 'impressao3d':(r'\b(impressao|impressora|impressoras|filamento|blender|modelagem|fdm|extrusor|camadas|pecas)\b',('Printer','Box','Layers'),('#f8b36d','#bfa5fc','#79ded1')),
 'historia':(r'\b(historia|historico|seculo|seculos|antigo|antiga|documento|documentos|arquivo|arquivos|epoca|passado|origem)\b',('BookOpen','FileText','Clock'),('#eac488','#b8bcdf','#a2c3c9')),
 'natureza':(r'\b(natureza|animal|animais|planta|plantas|floresta|clima|chuva|agua|oceano|ambiente|terra|planeta)\b',('Leaf','Globe','Droplets'),('#acd88c','#79cbd6','#e6ce91')),
 'culinaria':(r'\b(receita|cozinha|cozinhar|comida|bolo|ingredientes|forno|panela|misturar|mistura)\b',('ChefHat','CookingPot','Utensils'),('#f4b28b','#d9d78a','#d9b4e9')),
}

def normal(t):
 return ''.join(c for c in unicodedata.normalize('NFKD',str(t).lower()) if not unicodedata.combining(c))

def numero_aleatorio(semente,*partes):
 s='|'.join([str(semente),*(str(p) for p in partes)])
 return int(hashlib.sha256(s.encode()).hexdigest()[:16],16)/0xffffffffffffffff

def dominio(texto,padrao='geral'):
 t=normal(texto);scores={k:len(re.findall(v[0],t)) for k,v in DOMINIOS.items()}
 melhores=sorted(scores,key=lambda k:(scores[k],len(k)),reverse=True)
 return melhores[0] if melhores and scores[melhores[0]] else padrao

def acao(texto,c=None):
 t=normal(texto);c=c or {}
 regras=[('proteger',r'\b(prote[gj]\w*|seguranca|privacidade|cadeado|bloquear|bloqueio)\b'),('buscar',r'\b(busc\w*|pesquis\w*|procur\w*|encontr\w*)\b'),('produzir',r'\b(impress\w*|imprim\w*|extrusor|filamento|camadas|fabricar|modelar)\b'),('percorrer',r'\b(rota|trajeto|viajar|viagem|dirigir|estrada|caminho|percorrer)\b'),('comunicar',r'\b(mensagem|mensagens|comentario|comentarios|convers\w*|chat|publico|live|lives)\b'),('transformar',r'\b(transform\w*|mud\w*|trocar|diferenca|antes|depois)\b'),('conectar',r'\b(conect\w*|ligar|relacionar|juntos|entre|rede)\b'),('etapas',r'\b(primeiro|segundo|terceiro|depois|passo|passos|etapa|etapas)\b')]
 if c.get('checklist') or c.get('tipo')=='processo':return 'etapas'
 for a,p in regras:
  if re.search(p,t):return a
 return 'observar'

def simbolo(texto,padrao='geral',indice=0):
 d=dominio(texto,padrao);t=normal(texto)
 especiais=[(r'\b(segur\w*|prote[gj]\w*|privacidade|cadeado)\b','ShieldCheck'),(r'\b(mensagem|mensagens|comentario|comentarios|chat)\b','MessageCircle'),(r'\b(busc\w*|pesquis\w*)\b','Search'),(r'\b(tempo|hora|minuto|segundo|prazo)\b','Clock'),(r'\b(pessoa|pessoas|publico|gente)\b','Users')]
 for p,n in especiais:
  if re.search(p,t):return n
 return DOMINIOS[d][1][indice%len(DOMINIOS[d][1])] if d in DOMINIOS else ('Lightbulb','Layers','Sparkles')[indice%3]

def identidade_conteudo(dados):
 cenas=[]
 for c in dados.get('cenas',[]):
  v=c.get('video') or {}
  cenas.append({'tipo':c.get('tipo'),'narracao':c.get('narracao'),'foto':c.get('foto') or (c.get('cena') or {}).get('imagem'),'recorte':c.get('recorte'),'numero':c.get('numero'),'contador':c.get('contador'),'comparacao':c.get('comparacao'),'checklist':c.get('checklist'),'video':{'arquivo':v.get('arquivo'),'inicio':v.get('trecho_inicio',v.get('inicio')),'fim':v.get('trecho_fim',v.get('fim'))}})
 return hashlib.sha256(json.dumps({'titulo':dados.get('titulo'),'cenas':cenas},ensure_ascii=False,sort_keys=True).encode()).hexdigest()

@contextmanager
def _db(base):
 base=Path(base);base.mkdir(parents=True,exist_ok=True)
 db=sqlite3.connect(str(base/'memoria_motion.sqlite3'),timeout=3)
 db.execute('CREATE TABLE IF NOT EXISTS montagens (id TEXT PRIMARY KEY,projeto TEXT NOT NULL,plano TEXT NOT NULL,criado TEXT DEFAULT CURRENT_TIMESTAMP)')
 try:
  with db:yield db
 finally:db.close()

def memoria(base):
 try:
  with _db(base) as db:
   rows=db.execute('SELECT plano FROM montagens ORDER BY rowid DESC LIMIT 12').fetchall()
  return [json.loads(r[0]) for r in rows]
 except (sqlite3.Error,ValueError,OSError):return []

def preparar_direcao(dados,proj,base,pedido=''):
 """Congela seed e histórico: repetir um render mantém exatamente a mesma direção."""
 proj=Path(proj);path=proj/'direcao_motion.json';fingerprint=identidade_conteudo(dados)
 try:
  ctx=json.loads(path.read_text(encoding='utf-8'))
  if isinstance(ctx,dict) and ctx.get('versao')==VERSAO_DIRECAO and ctx.get('conteudo')==fingerprint and (not pedido or ctx.get('pedido','')==pedido) and isinstance(ctx.get('semente'),int):return ctx
 except (OSError,ValueError,TypeError):pass
 anteriores=memoria(base)
 ctx={'versao':VERSAO_DIRECAO,'id':secrets.token_hex(16),'conteudo':fingerprint,'pedido':pedido,'semente':secrets.randbits(32),'historico':anteriores,'dominio':dominio(dados.get('titulo','')+' '+' '.join(c.get('narracao','') for c in dados.get('cenas',[])))}
 proj.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=proj,prefix='.direcao-',suffix='.json',delete=False) as f:
  json.dump(ctx,f,ensure_ascii=False,indent=2);temp=Path(f.name)
 temp.replace(path)
 return ctx

def registrar_sucesso(dados,proj,base):
 """Chamado apenas depois de o MP4 ter sido exportado e substituído com sucesso."""
 ctx=dados.get('direcao_motion')
 if not ctx:return False
 plano={'id':ctx['id'],'dominio':ctx.get('dominio','geral'),'cor':ctx.get('cor'),'abertura':dados['cenas'][0].get('motion',{}).get('layout') if dados.get('cenas') else None,'cenas':[{'layout':c.get('motion',{}).get('layout'),'variante':c.get('motion',{}).get('variante',0),'acao':c.get('motion',{}).get('acao'),'corte':c.get('motion',{}).get('corte',0),'assinatura':assinatura_visual(c.get('motion',{})),'foco':c.get('motion',{}).get('foco'),'densidade':c.get('motion',{}).get('densidade'),'movimento':c.get('motion',{}).get('movimento')} for c in dados.get('cenas',[])]}
 try:
  with _db(base) as db:db.execute('INSERT OR IGNORE INTO montagens(id,projeto,plano) VALUES(?,?,?)',(ctx['id'],str(Path(proj).resolve()),json.dumps(plano,ensure_ascii=False)))
  return True
 except (sqlite3.Error,OSError):return False

def planejar_variedade(dados,ctx=None):
 seed=(ctx or {}).get('semente',dados.get('semente',int(identidade_conteudo(dados)[:8],16)))
 hist=(ctx or {}).get('historico',[])
 dom=(ctx or {}).get('dominio') or dominio(dados.get('titulo','')+' '+' '.join(c.get('narracao','') for c in dados['cenas']))
 paletas=DOMINIOS.get(dom,('',(),('#c7fb65','#8cdde6','#d5b6fc')))[2]
 recentes=[p.get('cor') for p in hist[:3]]
 cor=min(paletas,key=lambda x:(recentes.count(x),numero_aleatorio(seed,'cor',x)))
 if ctx:dados['direcao_motion']={k:ctx[k] for k in ('id','versao','semente','dominio')};dados['direcao_motion']['cor']=cor
 return {'semente':seed,'historico':hist,'dominio':dom,'cor':cor}

def detalhes_visual(c,i,plano,layouts):
 dom=dominio(c.get('narracao',''),plano['dominio']);act=acao(c.get('narracao',''),c);seed=plano['semente'];layout=c['motion']['layout']
 hist=[s for s in reversed(layouts) if s.get('layout')==layout]+[s for h in plano['historico'] for s in h.get('cenas',[]) if s.get('layout')==layout]
 variantes=list(range(3))
 variante=min(variantes,key=lambda v:(sum(s.get('variante',0)==v for s in hist[:8]),numero_aleatorio(seed,'variante',i,layout,v)))
 corte=int(numero_aleatorio(seed,'corte',i)*4)%4
 if i and corte==layouts[-1].get('corte'):corte=(corte+1)%4
 m=c['motion']
 foco=int(numero_aleatorio(seed,'foco',i,layout)*3)%3
 densidade=int(numero_aleatorio(seed,'densidade',i,layout)*3)%3
 movimento=int(numero_aleatorio(seed,'movimento',i,layout)*4)%4
 assinatura=f'{layout}|{variante}|{corte}|{foco}|{densidade}|{movimento}'
 # A estrutura, e nao somente a paleta, pesa no historico.
 assinaturas_recentes=[s.get('assinatura') for h in plano['historico'][:5] for s in h.get('cenas',[])]
 if assinatura in assinaturas_recentes:
  foco=(foco+1)%3
 if layouts and layouts[-1].get('layout')==layout and layouts[-1].get('variante')==variante:
  variante=(variante+1)%3
 m.update({'dominio':dom,'acao':act,'variante':variante,'acento':plano['cor'],'corte':corte,'camera':int(numero_aleatorio(seed,'camera',i)*4)%4,'velocidade':.88+numero_aleatorio(seed,'ritmo',i)*.24,'foco':foco,'densidade':densidade,'movimento':movimento})
 claro=int(numero_aleatorio(seed,'luz',i)*4)==0
 if len(layouts)>=2 and layouts[-1].get('claro')==layouts[-2].get('claro')==claro:claro=not claro
 m['claro']=claro
 labels=c.get('checklist') or m['chaves']
 m['objetos']=[{'texto':s,'icone':simbolo(s,dom,j),'em':m['batidas'][min(j,len(m['batidas'])-1)]['em'] if m['batidas'] else j*.5} for j,s in enumerate(labels[:3])]
 m['icone']=simbolo(c.get('narracao',''),dom)
 for j,b in enumerate(m['batidas']):b['icone']=simbolo(b['texto'],dom,j)
