from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from mascote_overlay import MascoteObvio

kit=MascoteObvio(Path(__file__).resolve().parent)
quadro=Image.new('RGBA',(1080,1920),'#F5F3EF')
d=ImageDraw.Draw(quadro)
d.rectangle((0,0,1080,195), fill='#171717')
d.text((60,80),'ALÉM DO ÓBVIO',fill='white',stroke_width=0)
d.rounded_rectangle((70,340,1010,900),radius=36,fill='#DFE5EA')
d.text((160,590),'ASSUNTO DO VÍDEO',fill='#171717')
reacao=kit.selecionar_reacao('Veja por que isso aconteceu',emocao='explicacao')
quadro=kit.aplicar(quadro,reacao,tempo=1.2)
# Exemplo de legenda sobre a cena, sem faixa ou fundo.
d=ImageDraw.Draw(quadro)
d.text((470,1480),'Olhe para isso!',fill='white',stroke_width=4,stroke_fill='#171717')
saida=Path(__file__).resolve().parent/'exemplo_1080x1920.png'
quadro.convert('RGB').save(saida)
print(f'Quadro gerado: {saida.name}; reação {reacao}')
