import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_inteligencia import (
    adequacao, analisar_roteiro, assinatura_visual,
    escolher_cenas_midia, pontuacao_midia,
)

class TestesInteligencia(unittest.TestCase):
    def test_detectar_intencoes(self):
        cenas = [
            {'narracao': 'Você sabia deste segredo surpreendente?'},
            {'narracao': 'Primeiro, clique no aplicativo para começar.'},
            {'narracao': 'Mas veja a diferença antes e depois.'},
        ]
        planos = analisar_roteiro(cenas)
        self.assertEqual(len(planos), 3)
        self.assertIn('pergunta', planos[0]['intencoes'])
        self.assertIn('revelacao', planos[0]['intencoes'])
        self.assertIn('demonstracao', planos[1]['intencoes'])
        self.assertIn('contraste', planos[2]['intencoes'])
    def test_escolher_interface(self):
        cena = {'narracao': 'Clique na tela do aplicativo.'}
        a = analisar_roteiro([cena])[0]
        self.assertGreater(adequacao('interface', a, cena, 0, 3),
                           adequacao('editorial', a, cena, 0, 3))
    def test_midia_com_descricao(self):
        cenas = [
            {'narracao': 'O carro segue pela estrada.'},
            {'narracao': 'A impressora usa filamento para fabricar peças.'},
        ]
        arquivos = [
            {'arquivo': 'filmagem_01.mp4', 'descricao': 'impressora filamento'},
            {'arquivo': 'clip_09.mp4', 'etiquetas': ['carro', 'estrada']},
        ]
        self.assertEqual(escolher_cenas_midia(cenas, arquivos), {0: 1, 1: 0})
    def test_nao_inventar_midia(self):
        cena = {'narracao': 'Descoberta de um vaso.'}
        self.assertEqual(escolher_cenas_midia([cena], [{'arquivo': 'IMG_0023.mp4'}]), {})
        self.assertEqual(pontuacao_midia(cena, ''), 0)
    def test_assinatura_composicao(self):
        a = {'layout': 'palavra', 'variante': 1, 'corte': 2}
        self.assertNotEqual(assinatura_visual(a), assinatura_visual({**a, 'variante': 2}))

if __name__ == '__main__':
    unittest.main()
