"""Overlay não destrutivo do mascote Óbvio em quadros PIL; Python 3.9+ e Pillow.
Integração independente: não altera arquivos existentes do editor.
"""
from pathlib import Path
import json, hashlib, math, re, unicodedata
from PIL import Image

class MascoteObvio:
    def __init__(self, pasta=None):
        self.pasta=Path(pasta or Path(__file__).resolve().parent)
        self.catalogo=json.loads((self.pasta/'reacoes.json').read_text(encoding='utf-8'))
        self.reacoes=self.catalogo['reacoes']
        self._map={r['id']:r for r in self.reacoes}
        self._cache={}

    @staticmethod
    def _simples(s):
        s=unicodedata.normalize('NFD',str(s).lower())
        return ''.join(c for c in s if unicodedata.category(c)!='Mn')

    def selecionar_reacao(self, texto, emocao=None, cena=0, ultima=None):
        """Seleção determinística com filtro por emoção e evita repetição imediata.
        A classificação por palavras-chave é simples; um modelo semântico pode passar emocao.
        """
        t=self._simples(texto)
        if not emocao:
            sinais={
              'surpresa':['inacreditavel','surpreendente','impossivel','chocante','absurdo','ninguem esperava'],
              'investigacao':['por que','como funciona','descobriu','investigacao','pesquisa','misterio'],
              'indignacao':['injustica','revoltante','crime','denuncia','fraude'],
              'tristeza':['morreu','tragico','tragica','triste','lamentavel','acidente'],
              'alegria':['conseguiu','vitoria','excelente','sucesso','incrivel'],
              'explicacao':['entenda','veja','observe','repare','primeiro','resultado','explicacao']}
            emocao=next((e for e,pats in sinais.items() if any(p in t for p in pats)),'explicacao')
        cand=[r for r in self.reacoes if self._simples(emocao) in [self._simples(e) for e in r['emocao']]]
        if not cand: cand=list(self.reacoes)
        cand=[r for r in cand if r['id']!=ultima] or cand
        digest=hashlib.sha256(f'{t}|{emocao}|{int(cena)}'.encode('utf-8')).digest()
        return cand[int.from_bytes(digest[:4], 'big') % len(cand)]['id']

    def imagem(self, reacao_id):
        if reacao_id not in self._map: raise KeyError(f'Reação inválida: {reacao_id}')
        if reacao_id not in self._cache:
            self._cache[reacao_id]=Image.open(self.pasta/self._map[reacao_id]['arquivo']).convert('RGBA')
        return self._cache[reacao_id]

    def aplicar(self, quadro, reacao_id, tempo=0.0, altura=None,
                canto='inferior_esquerdo', margem_horizontal=None, margem_inferior=None,
                animar=True, opacidade=1.0):
        """Retorna quadro PIL com personagem RGBA composto (não modifica a entrada).
        `tempo` em segundos, `altura` em pixels do vídeo, margens em pixels.
        Padrão de 1080x1920: mascote ~330px e margem inferior 340px.
        """
        frame=quadro.convert('RGBA')
        W,H=frame.size
        altura=int(altura if altura is not None else H * (330/1920))
        margem_horizontal=int(margem_horizontal if margem_horizontal is not None else W*(36/1080))
        margem_inferior=int(margem_inferior if margem_inferior is not None else H*(340/1920))
        src=self.imagem(reacao_id)
        fator=1.0 + (0.012*math.sin(tempo*3.6) if animar else 0)
        h=max(2,int(altura*fator));w=max(2,int(h*src.width/src.height))
        layer=src.resize((w,h),Image.Resampling.LANCZOS)
        if opacidade<1.0:
            opacidade=max(0.0,min(1.0,opacidade))
            layer.putalpha(layer.getchannel('A').point(lambda a:int(a*opacidade)))
        x=margem_horizontal if canto=='inferior_esquerdo' else W-margem_horizontal-w
        y=H-margem_inferior-h-(int(4*math.sin(tempo*4)) if animar else 0)
        frame.alpha_composite(layer,(max(-w,x),max(-h,y)))
        return frame
