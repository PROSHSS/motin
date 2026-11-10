"""Regressões da integração: python -m unittest discover -s tests -v."""
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mascote
import painel


class MascoteTests(unittest.TestCase):
    def test_frame_zero_e_rejeicao_de_duplicatas(self):
        troca = {'por': 'frame', 'numero': 0, 'posicao': 'ambos', 'expressao': 'feliz', 'expressao_direita': 'pensativo'}
        cfg = mascote.configurar({'mascote_ativo': 'sim', 'mascote_trocas': json.dumps([troca])})
        self.assertEqual(cfg['quadros'][0]['numero'], 0)
        with self.assertRaises(ValueError):
            mascote.configurar({'mascote_ativo': 'sim', 'mascote_trocas': json.dumps([troca, troca])})
        troca['numero'] = 1.5
        with self.assertRaises(ValueError):
            mascote.configurar({'mascote_ativo': 'sim', 'mascote_trocas': json.dumps([troca])})

    def test_limites_e_campos_invalidos(self):
        cfg = mascote.configurar({'mascote_tamanho': 'NaN', 'mascote_rodape': '-100', 'mascote_volume': '999', 'mascote_voz': 'arquivo.exe'})
        self.assertEqual(cfg['tamanho'], 27)
        self.assertEqual(cfg['rodape'], 80)
        self.assertEqual(cfg['volume_original'], 0.35)
        self.assertEqual(cfg['voz'], 'referencia')
        # Rascunho antigo inválido não bloqueia o modo sem personagem.
        self.assertFalse(mascote.configurar({'mascote_trocas': 'rascunho inválido'})['ativo'])

    def test_video_continuo_nao_vira_fotografia(self):
        with tempfile.TemporaryDirectory() as tmp:
            campos = {'tema': 'Teste narrador', 'narrativa': 'Primeira explicação.\nSegunda reação!',
                      'mascote_ativo': 'sim', 'mascote_falas_exatas': 'sim', 'mascote_fundo': 'video',
                      'mascote_posicao': 'ambos', 'mascote_voz': 'divertido'}
            with patch.object(painel, 'pasta_base', return_value=(Path(tmp), {})), \
                    patch.object(painel, 'sondar_video', return_value={'duracao': 7.5, 'tem_audio': True}), \
                    patch.object(painel, 'quadros_do_video', side_effect=AssertionError('Vídeo de fundo não deve virar foto.')):
                _, proj, job, _, _ = painel.criar_trabalho(campos, [('fundo.mp4', b'video-de-teste')])
            cfg = json.loads((proj / 'mascote.json').read_text())
            self.assertEqual(cfg['videos'][0]['duracao'], 7.5)
            self.assertEqual(cfg['posicao'], 'ambos')
            self.assertEqual(job['config']['imagens'], False)
            self.assertEqual(job['config']['ritmo_fala'], 1.0)
            self.assertEqual(job['config']['mascote_voz'], 'referencia')
            dados = mascote.roteiro_direto(proj, 'Teste narrador')
            self.assertEqual([c['narracao'] for c in dados['cenas']], ['Primeira explicação.', 'Segunda reação!'])
            (proj / 'public').mkdir()
            mascote.preparar(proj, dados, painel.RAIZ)
            self.assertEqual((proj / 'public' / cfg['videos'][0]['arquivo']).read_bytes(), b'video-de-teste')
            self.assertEqual(len(list((proj / 'public/mascotes').glob('*.png'))), 12)

    def test_modo_anterior_sem_personagem(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(painel, 'pasta_base', return_value=(Path(tmp), {})):
            _, proj, job, _, _ = painel.criar_trabalho({'tema': 'Modo anterior'}, [])
            self.assertFalse((proj / 'mascote.json').exists())
            self.assertNotIn('mascote_voz', job['config'])

    def test_fundo_obrigatorio_e_narrativa_obrigatoria(self):
        with self.assertRaises(ValueError):
            painel.criar_trabalho({'tema': 'Teste', 'mascote_ativo': 'sim'}, [])
        with self.assertRaises(ValueError):
            painel.criar_trabalho({'tema': 'Teste', 'mascote_ativo': 'sim', 'mascote_falas_exatas': 'sim'}, [('v.mp4', b'v')])



if __name__ == '__main__':
    unittest.main()
