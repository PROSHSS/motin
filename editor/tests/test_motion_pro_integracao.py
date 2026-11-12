"""Integração: planejamento de cenas Motion Pro sem TTS e sem APIs externas."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motion_editor as M


class IntegracaoMotionProTests(unittest.TestCase):
    def cenas(self):
        frases = [
            "Você sabia deste segredo surpreendente?",
            "Primeiro, clique no aplicativo para iniciar.",
            "A paisagem aparece e a estrada mostra o trajeto.",
            "Mas o resultado mudou completamente depois.",
            "Agora veja a diferença.",
            "Por fim, entenda o que aconteceu.",
            "Uma boa explicação transforma o assunto.",
            "A história continua e o cenário se transforma.",
        ]
        return {"titulo": "Teste de variedade", "cenas": [
            {"tipo": "citacao", "narracao": frase, "duracao": 3}
            for frase in frases
        ]}

    def test_motion_adiciona_direcao_sem_mudar_fala(self):
        d = self.cenas()
        original = copy.deepcopy(d)
        M.dirigir(d, [], [])
        for c, antes in zip(d["cenas"], original["cenas"]):
            self.assertEqual(c["narracao"], antes["narracao"])
            self.assertEqual(c["duracao"], antes["duracao"])
            self.assertIn("intencao", c["motion"])
            self.assertIn("foco", c["motion"])
            self.assertIn(c["motion"]["layout"], M.LAYOUTS)

    def test_plano_reprodutivel(self):
        ctx = {"id": "demo", "semente": 9123, "historico": [],
               "dominio": "tecnologia", "versao": "direcao-contextual-v8.1"}
        a, b = self.cenas(), self.cenas()
        self.assertEqual(M.dirigir(a, [], [], contexto=ctx),
                         M.dirigir(b, [], [], contexto=ctx))

    def test_preserva_cenas_fatuais_originais(self):
        d = {"titulo": "Dados", "cenas": [
            {"tipo": "grafico", "narracao": "O estudo mostra estes números.",
             "duracao": 3, "grafico": {"valores": [2, 4, 7]}},
            {"tipo": "contador", "narracao": "O valor é 87.",
             "duracao": 3, "contador": {"para": 87, "rotulo": "valor"}},
        ]}
        M.dirigir(d, [], [])
        self.assertEqual(d["cenas"][0]["motion"]["layout"], "original")
        self.assertEqual(d["cenas"][1]["motion"]["layout"], "dados")
        self.assertEqual(d["cenas"][0]["grafico"]["valores"], [2, 4, 7])
        self.assertEqual(d["cenas"][1]["contador"]["para"], 87)


if __name__ == "__main__":
    unittest.main()
