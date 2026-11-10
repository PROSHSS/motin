import contextlib
import os
import json
import subprocess
import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import criar
import mascote
import tts_mascote
import voz_referencia


class VozBrasileiraTests(unittest.TestCase):
    def setUp(self):
        # Os testes usam um WAV sintético, sem depender da gravação pessoal.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        referencia = Path(tmp.name) / 'referencia-teste.wav'
        with wave.open(str(referencia), 'wb') as arquivo:
            arquivo.setnchannels(1)
            arquivo.setsampwidth(2)
            arquivo.setframerate(24000)
            arquivo.writeframes(b'\x00\x00' * 24000 * 4)
        for modulo in (voz_referencia, tts_mascote):
            p = patch.object(modulo, 'carregar_referencia', return_value=(referencia, 'Referência de teste.'))
            p.start()
            self.addCleanup(p.stop)


    def test_cenas_repetidas_seguem_a_gravacao_sem_inserir_pausa(self):
        palavras = [
            {'palavra': 'Olha', 'inicio': .1, 'fim': .35},
            {'palavra': 'só', 'inicio': .4, 'fim': .7},
            {'palavra': 'Olha', 'inicio': 1.2, 'fim': 1.45},
            {'palavra': 'só', 'inicio': 1.5, 'fim': 1.8},
        ]
        tempos = tts_mascote.tempos_da_fala(['Olha só.', 'Olha só.'], palavras, 2.0)
        self.assertEqual(tempos, [{'cena': 1, 'inicio': 0, 'fim': .7}, {'cena': 2, 'inicio': 1.2, 'fim': 2}])

    def test_moeda_em_um_limite_e_acentos_preservam_a_cena(self):
        palavras = [
            {'palavra': 'Custa', 'inicio': .1, 'fim': .4},
            {'palavra': 'R$ 35,90', 'inicio': .5, 'fim': 2.5},
            {'palavra': 'Chega', 'inicio': 3.0, 'fim': 3.4},
            {'palavra': 'às', 'inicio': 3.45, 'fim': 3.6},
            {'palavra': '10h', 'inicio': 3.7, 'fim': 4.4},
        ]
        tempos = tts_mascote.tempos_da_fala(['Custa R$35,90.', 'Chega às 10h.'], palavras, 4.6)
        self.assertEqual(tempos[0]['fim'], 2.5)
        self.assertEqual(tempos[1]['inicio'], 3)
        self.assertEqual(tempos[1]['fim'], 4.6)

    def test_grafia_expandida_nao_altera_o_audio_nem_inverte_cenas(self):
        palavras = [{'palavra': 'Prazo dois mil e vinte e seis.', 'inicio': 0, 'fim': 3},
                    {'palavra': 'Pronto.', 'inicio': 3.5, 'fim': 4}]
        tempos = tts_mascote.tempos_da_fala(['Prazo 2026.', 'Pronto.'], palavras, 4.2)
        self.assertEqual(tempos[0]['inicio'], 0)
        self.assertGreaterEqual(tempos[1]['inicio'], tempos[0]['fim'])
        self.assertEqual(tempos[-1]['fim'], 4.2)





    def test_cache_antigo_forca_voz_nova_sem_apagar_antes_da_sintese(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            (proj / 'roteiro.json').write_text(json.dumps({'cenas': [{'narracao': 'Teste.'}]}))
            (proj / 'narracao.wav').write_bytes(b'voz-antiga')
            (proj / 'tempos_cenas.json').write_text('[]')
            (proj / '.voz_mascote').write_text('mascote-v1')
            class SemInternet(Exception):
                pass
            with patch.object(voz_referencia, 'python_voz', return_value=sys.executable), patch.object(criar, 'rodar', side_effect=SemInternet):
                with self.assertRaises(SemInternet):
                    criar.etapa_narracao(proj, {'mascote_voz': 'jovem'}, {}, sys.executable, 'mascote', False)
            self.assertEqual((proj / 'narracao.wav').read_bytes(), b'voz-antiga')
            with patch.object(voz_referencia, 'python_voz', return_value=sys.executable), patch.object(criar, 'rodar') as executar:
                self.assertTrue(criar.etapa_narracao(proj, {'mascote_voz': 'jovem'}, {}, sys.executable, 'mascote', False))
                self.assertEqual(executar.call_args[0][2]['MASCOTE_VOZ'], 'referencia')
                executar.reset_mock()
                self.assertFalse(criar.etapa_narracao(proj, {'mascote_voz': 'natural'}, {}, sys.executable, 'mascote', False))
                executar.assert_not_called()

    def test_pipeline_preserva_voz_palavras_e_renderiza_mp4_desatualizado(self):
        class RenderIniciado(Exception):
            pass
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            proj = base / 'projetos' / 'teste-fluido'
            (proj / 'public').mkdir(parents=True)
            (base / 'saidas').mkdir()
            (base / 'saidas/teste-fluido.mp4').write_bytes(b'video-antigo')
            dados = {'titulo': 'Teste fluido', 'narrado': True, 'cenas': [{'tipo': 'citacao', 'duracao': 1, 'narracao': 'Olá.', 'citacao': {'texto': 'Olá.'}}]}
            (proj / 'roteiro.json').write_text(json.dumps(dados))
            (proj / 'mascote.json').write_text(json.dumps({'ativo': True, 'voz': 'jovem', 'fundo': 'video', 'videos': []}))
            (proj / 'public/narracao.wav').write_bytes(b'voz-publica-antiga')
            def nova_voz(*a):
                (proj / 'narracao.wav').write_bytes(b'voz-brasileira-nova')
                (proj / 'tempos_cenas.json').write_text('[{"inicio":0,"fim":1}]')
                (proj / 'palavras.json').write_text('[{"palavra":"Olá.","inicio":0.1,"fim":0.8}]')
                return True
            def preparar_audio(*a):
                (proj / 'public/audio.json').write_text('{}')
            args = types.SimpleNamespace(novo=False, fatos=None, voz=None, refazer_voz=False, sem_musica=True, rerender=False)
            cfg = {**criar.PADRAO, 'pasta_dados': str(base)}
            with patch.object(criar, 'etapa_narracao', side_effect=nova_voz), \
                 patch.object(criar, 'desacelerar', side_effect=AssertionError('Não desacelerar a voz natural.')), \
                 patch.object(criar, 'ajustar_minimos', side_effect=AssertionError('Não alongar as cenas.')), \
                 patch.object(criar, 'polir_voz', side_effect=AssertionError('Não aplicar efeito no timbre.')), \
                 patch.object(criar, 'preparar_audio', side_effect=preparar_audio), \
                 patch.object(criar, 'validar_roteiro'), patch.object(criar, 'auditar_texto_tela'), \
                 patch.object(criar, 'rodar', side_effect=RenderIniciado):
                with self.assertRaises(RenderIniciado):
                    criar.produzir_showcase('Teste fluido', args, cfg, {})
            self.assertEqual((proj / 'public/narracao.wav').read_bytes(), b'voz-brasileira-nova')
            self.assertEqual(json.loads((proj / 'public/palavras.json').read_text())[0]['inicio'], .1)
            self.assertEqual((base / 'saidas/teste-fluido.mp4').read_bytes(), b'video-antigo')


    def test_clonagem_usa_audio_transcricao_e_portugues_sem_mudar_pitch(self):
        import numpy as np
        class Modelo:
            def create_voice_clone_prompt(self, **kw):
                self.prompt = kw
                return ['referencia-codificada']
            def generate_voice_clone(self, **kw):
                self.geracao = kw
                return [np.ones(24000, dtype=np.float32) * .1], 24000
        modelo = Modelo()
        carregador = types.SimpleNamespace(from_pretrained=lambda *a, **kw: modelo)
        torch = types.SimpleNamespace(set_num_threads=lambda *a: None, manual_seed=lambda *a: None,
                                      inference_mode=contextlib.nullcontext, float32='float32')
        texto = 'Primeira explicação.\nAgora vem a surpresa!'
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            (pasta / 'speech_tokenizer').mkdir()
            (pasta / 'model.safetensors').touch()
            (pasta / 'speech_tokenizer/model.safetensors').touch()
            with patch.dict(sys.modules, {'torch': torch, 'qwen_tts': types.SimpleNamespace(Qwen3TTSModel=carregador)}), \
                 patch.object(tts_mascote, 'pasta_modelo', return_value=pasta):
                audio, sr = tts_mascote.sintetizar(texto)
        ref, transcricao = voz_referencia.carregar_referencia()
        self.assertEqual(modelo.prompt, {'ref_audio': str(ref), 'ref_text': transcricao, 'x_vector_only_mode': False})
        self.assertEqual(modelo.geracao['language'], 'Portuguese')
        self.assertEqual(modelo.geracao['text'], texto)
        self.assertEqual(modelo.geracao['voice_clone_prompt'], ['referencia-codificada'])
        self.assertNotIn('pitch', modelo.geracao)
        self.assertEqual(sr, 24000)
        np.testing.assert_array_equal(audio, np.ones(24000, dtype=np.float32) * .1)

    def test_narracao_e_continua_e_mantem_tempos(self):
        import numpy as np
        audio = np.ones(48000, dtype=np.float32) * .1
        palavras = [{'palavra': 'Olha.', 'inicio': .1, 'fim': .7}, {'palavra': 'Pronto!', 'inicio': 1.2, 'fim': 1.8}]
        with patch.object(tts_mascote, 'sintetizar', return_value=(audio, 24000)) as sintetizar, \
             patch.object(tts_mascote, 'alinhar_palavras', return_value=palavras):
            saida, sr, tempos, _ = tts_mascote.gerar(['Olha.', 'Pronto!'])
        sintetizar.assert_called_once_with('Olha.\nPronto!')
        self.assertIs(saida, audio)
        self.assertEqual(tempos, [{'cena': 1, 'inicio': 0, 'fim': .7}, {'cena': 2, 'inicio': 1.2, 'fim': 2}])

    def test_falha_na_clonagem_preserva_arquivos_existentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            saida = pasta / 'voz.wav'
            saida.write_bytes(b'voz-anterior')
            with patch.object(sys, 'argv', ['tts_mascote.py', '--teste', 'Teste.', '--saida', str(saida)]), \
                 patch.object(tts_mascote, 'gerar', side_effect=RuntimeError('modelo indisponível')):
                with self.assertRaisesRegex(RuntimeError, 'modelo indisponível'):
                    tts_mascote.main()
            self.assertEqual(saida.read_bytes(), b'voz-anterior')

    def test_identidade_muda_quando_audio_ou_transcricao_mudam(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'ref.wav'
            p.write_bytes(b'audio-1')
            with patch.object(voz_referencia, 'carregar_referencia', return_value=(p, 'Texto um.')):
                antes = voz_referencia.identidade_referencia()
                p.write_bytes(b'audio-2')
                self.assertNotEqual(antes, voz_referencia.identidade_referencia())
            with patch.object(voz_referencia, 'carregar_referencia', return_value=(p, 'Texto dois.')):
                self.assertNotEqual(antes, voz_referencia.identidade_referencia())

    def test_perfis_antigos_migram_para_referencia_real(self):
        for antigo in ['conversa', 'jovem', 'serio', 'divertido', 'suave', 'natural', 'feminina']:
            self.assertEqual(mascote.normalizar_perfil(antigo), 'referencia')
        self.assertEqual(mascote.PERFIS['referencia']['idioma'], 'pt-BR')


if __name__ == '__main__':
    unittest.main()
