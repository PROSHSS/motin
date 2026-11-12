"""Testes do diretor contextual: nao necessitam de internet nem GPU."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_inteligencia import (
    adequacao, analisar_roteiro, assinatura_visual, escolher_cenas_midia,
    pontuacao_midia,
)


class MotionProInteligenciaTests(unittest.TestCase):
    def test_contexto_intencao(self):
        cenas = [
            {"narracao": "Você sabia deste segredo surpreendente?"},
            {"narracao": "Primeiro, abra o aplicativo e clique no menu."},
            {"narracao": "Mas veja a diferença entre o antes e o depois."},
        ]
        a = analisar_roteiro(cenas)
        self.assertEqual(len(a), 3)
        self.assertIn("pergunta", a[0]["intencoes"])
        self.assertIn("revelacao", a[0]["intencoes"])
        self.assertIn("demonstracao", a[1]["intencoes"])
        self.assertIn("contraste", a[2]["intencoes"])

    def test_adequacao_e_realidade_do_conteudo(self):
        cena = {"narracao": "Clique na tela para iniciar."}
        analise = analisar_roteiro([cena])[0]
        self.assertGreater(adequacao("interface", analise, cena, 0, 3),
                           adequacao("editorial", analise, cena, 0, 3))
        self.assertNotIn("numero", analise)

    def test_midia_com_etiquetas(self):
        cenas = [
            {"narracao": "O carro segue pela estrada."},
            {"narracao": "A impressora usa filamento para fabricar peças."},
            {"narracao": "Uma dúvida sobre o aplicativo."},
        ]
        arquivos = [
            {"arquivo": "filmagem_01.mp4", "descricao": "impressora filamento"},
            {"arquivo": "clip_09.mp4", "etiquetas": ["carro", "estrada"]},
        ]
        self.assertEqual(escolher_cenas_midia(cenas, arquivos), {0: 1, 1: 0})

    def test_midia_desconhecida_nao_tem_semantica_inventada(self):
        cenas = [{"narracao": "Descoberta arqueológica de um vaso."}]
        arquivos = [{"arquivo": "IMG_0023.mp4"}]
        self.assertEqual(escolher_cenas_midia(cenas, arquivos), {})
        self.assertEqual(pontuacao_midia(cenas[0], ""), 0)

    def test_fixa_e_prioritaria(self):
        cenas = [{"narracao": "A roda do carro."}, {"narracao": "Uma rota."}]
        arquivos = [
            {"arquivo": "qualquer.mp4", "cena": 2},
            {"arquivo": "carro.mp4", "descricao": "carro"},
        ]
        self.assertEqual(escolher_cenas_midia(cenas, arquivos), {0: 1, 1: 0})

    def test_assinatura_inclui_estrutura(self):
        base = {"layout": "palavra", "variante": 1, "corte": 2}
        a = assinatura_visual(base)
        self.assertEqual(a, assinatura_visual(dict(base)))
        self.assertNotEqual(a, assinatura_visual({**base, "variante": 2}))
        self.assertNotEqual(a, assinatura_visual({**base, "foco": 1}))


if __name__ == "__main__":
    unittest.main()
