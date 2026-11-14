import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motion_editor as M

class TestesIntegracao(unittest.TestCase):
    def dados(self):
        return {'titulo': 'Teste de variedade', 'cenas': [
            {'tipo': 'citacao', 'narracao': frase, 'duracao': 3}
            for frase in [
                'Você sabia deste segredo surpreendente?',
                'Primeiro, clique no aplicativo para iniciar.',
                'A estrada revela o trajeto.',
                'Mas o resultado mudou completamente depois.',
                'Agora veja a diferença.',
                'Por fim, entenda o que aconteceu.',
                'Uma explicação transforma o assunto.',
                'A história continua e o cenário se transforma.',
            ]
        ]}
    def test_plano_reproduzivel(self):
        ctx = {'id':'demo','semente':9123,'historico':[],
               'dominio':'tecnologia','versao':'direcao-contextual-v8.1'}
        a, b = self.dados(), self.dados()
        self.assertEqual(M.dirigir(a,[],[],contexto=ctx), M.dirigir(b,[],[],contexto=ctx))
    def test_preservacao_de_texto(self):
        dados=self.dados()
        old=copy.deepcopy(dados)
        M.dirigir(dados,[],[])
        for cena,original in zip(dados['cenas'],old['cenas']):
            self.assertEqual(cena['narracao'],original['narracao'])
            self.assertIn('intencao', cena['motion'])
            self.assertIn('foco', cena['motion'])
    def test_graficos_fatos_intactos(self):
        d={'titulo':'Dados','cenas':[
            {'tipo':'grafico','duracao':3,'narracao':'Dados do estudo.', 'grafico':{'valores':[2,4,7]}},
            {'tipo':'contador','duracao':3,'narracao':'O valor é 87.', 'contador':{'para':87}},
        ]}
        M.dirigir(d,[],[])
        self.assertEqual(d['cenas'][0]['motion']['layout'],'original')
        self.assertEqual(d['cenas'][1]['motion']['layout'],'dados')
        self.assertEqual(d['cenas'][0]['grafico']['valores'],[2,4,7])

if __name__ == '__main__':
    unittest.main()
