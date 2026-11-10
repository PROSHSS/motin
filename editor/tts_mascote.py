"""Narração local condicionada pelo áudio e pela transcrição enviados pelo usuário.

Qwen3-TTS Base faz a clonagem por referência, sem converter uma voz pronta.
Depois da instalação, texto e gravação permanecem no computador.
"""
import argparse
import bisect
import difflib
import gc
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from mascote import PERFIS, PERFIS_ANTIGOS
from voz_referencia import carregar_referencia, pasta_modelo, pasta_alinhador

VERSAO_VOZ = 'referencia-real-qwen-icl-v6'
SR = 24000


def limpar_texto(texto):
    return re.sub(r'\s+', ' ', str(texto)).strip()


def sintetizar(texto):
    try:
        import numpy as np
        import soundfile as sf
        import torch
        from qwen_tts import Qwen3TTSModel
    except ImportError as e:
        raise RuntimeError('Execute instalar_voz_mascote.bat. Esta voz usa o ambiente separado .venv-voz.') from e
    modelo_dir = pasta_modelo()
    if not (modelo_dir / 'model.safetensors').is_file() or not (modelo_dir / 'speech_tokenizer' / 'model.safetensors').is_file():
        raise RuntimeError('Falta o modelo local de voz. Execute instalar_voz_mascote.bat para concluir o download.')
    referencia, transcricao = carregar_referencia()
    try:
        info = sf.info(referencia)
        if not 3 <= info.duration <= 30:
            raise RuntimeError('A referência precisa ter entre 3 e 30 segundos de fala limpa.')
        torch.set_num_threads(min(4, os.cpu_count() or 1))
        torch.manual_seed(7)
        print('Carregando a voz de referência local. No processador pode levar alguns minutos...', flush=True)
        modelo = Qwen3TTSModel.from_pretrained(str(modelo_dir), device_map='cpu', dtype=torch.float32,
                                              attn_implementation='sdpa', local_files_only=True)
        with torch.inference_mode():
            prompt = modelo.create_voice_clone_prompt(ref_audio=str(referencia), ref_text=transcricao,
                                                      x_vector_only_mode=False)
            print('Gerando a narração com o áudio e a expressão da referência...', flush=True)
            audios, sr = modelo.generate_voice_clone(text=texto, language='Portuguese', voice_clone_prompt=prompt,
                non_streaming_mode=True, max_new_tokens=min(8192, max(256, len(texto.split()) * 16 + 128)),
                temperature=.8, subtalker_temperature=.8)
        audio = np.asarray(audios[0], dtype=np.float32).reshape(-1)
        del modelo, prompt, audios
        gc.collect()
        if sr != SR or len(audio) < sr * .1 or not np.isfinite(audio).all() or np.max(np.abs(audio)) < .0001:
            raise RuntimeError('O modelo retornou áudio vazio ou inválido; a voz anterior foi preservada.')
        # Somente proteção contra clipping; sem mudar pitch, velocidade, pausas ou equalização.
        pico = float(np.max(np.abs(audio)))
        if pico > .98:
            audio *= .98 / pico
        return audio, sr
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f'Não consegui gerar a voz por referência: {e}. Confira instalar_voz_mascote.bat.') from e


def palavras_estimadas(texto, duracao):
    palavras = texto.split()
    passo = duracao / max(1, len(palavras))
    return [{'palavra': p, 'inicio': i * passo, 'fim': (i + .92) * passo} for i, p in enumerate(palavras)]


def alinhar_palavras(audio, sr, texto):
    """Alinha localmente; mantém a grafia do roteiro nas legendas."""
    duracao = len(audio) / sr
    try:
        from faster_whisper import WhisperModel
        from scipy.signal import resample_poly
        pasta = pasta_alinhador()
        if not (pasta / 'model.bin').is_file():
            raise RuntimeError('Alinhador local ainda não instalado.')
        modelo = WhisperModel(str(pasta), device='cpu', compute_type='int8', cpu_threads=4, local_files_only=True)
        # Array evita depender da decodificação de áudio pelo PyAV.
        segmentos, _ = modelo.transcribe(resample_poly(audio, 2, 3), language='pt', beam_size=5,
                                         word_timestamps=True, initial_prompt=texto[:1000], vad_filter=False)
        faladas = [{'palavra': p.word.strip(), 'inicio': max(0, p.start), 'fim': min(duracao, p.end)}
                   for s in segmentos for p in s.words or [] if p.word.strip() and p.end > p.start]
        if not faladas or difflib.SequenceMatcher(None, chave_texto(texto),
                ''.join(chave_texto(p['palavra']) for p in faladas), autojunk=False).ratio() < .65:
            raise RuntimeError('Alinhamento pouco confiável.')
        originais = texto.split()
        tempos = tempos_da_fala(originais, faladas, duracao)
        return [{'palavra': palavra, 'inicio': tempo['inicio'], 'fim': tempo['fim']}
                for palavra, tempo in zip(originais, tempos)]
    except Exception as e:
        print(f'AVISO: legendas com tempos estimados ({e}). A voz permanece intacta.', flush=True)
        return palavras_estimadas(texto, duracao)


def chave_texto(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.lower()) if c.isalnum())


def tempos_da_fala(textos, palavras, duracao):
    """Encontra as cenas na mesma gravação; nenhuma pausa ou junção é inserida no áudio."""
    originais = [chave_texto(t) for t in textos]
    limites = [0]
    for t in originais:
        limites.append(limites[-1] + len(t))
    original = ''.join(originais)
    spans, cursor = [], 0
    for p in palavras:
        n = len(chave_texto(p['palavra']))
        if n:
            spans.append((cursor, cursor + n, p['inicio'], p['fim']))
            cursor += n
    falado = ''.join(chave_texto(p['palavra']) for p in palavras)
    if not original or not spans:
        raise ValueError('Não consegui identificar palavras na narração.')
    blocos = None
    if original != falado:
        matcher = difflib.SequenceMatcher(None, original, falado, autojunk=False)
        if matcher.ratio() < 0.65:
            # Apenas o posicionamento das cenas é estimado. A fala continua intacta.
            return [{'cena': i + 1, 'inicio': round(duracao * limites[i] / len(original), 6),
                     'fim': round(duracao * limites[i + 1] / len(original), 6)} for i in range(len(textos))]
        blocos = matcher.get_matching_blocks()

    def mapear(pos):
        if blocos is None:
            return pos
        antes_a = antes_b = 0
        for a, b, n in blocos:
            if pos < a:
                return antes_b + (pos - antes_a) / max(1, a - antes_a) * (b - antes_b)
            if pos <= a + n:
                return b + pos - a
            antes_a, antes_b = a + n, b + n
        return len(falado)

    inicios = [s[0] for s in spans]
    finais = [s[1] for s in spans]
    def segundo(pos, lado):
        if lado == 'inicio':
            idx = min(len(spans) - 1, bisect.bisect_right(inicios, pos) - 1)
        else:
            idx = min(len(spans) - 1, bisect.bisect_left(finais, pos))
        a, b, ini, fim = spans[max(0, idx)]
        return max(0, min(duracao, ini + max(0, min(1, (pos - a) / (b - a))) * (fim - ini)))

    tempos = []
    for i in range(len(textos)):
        ini = 0.0 if i == 0 else segundo(mapear(limites[i]), 'inicio')
        fim = duracao if i == len(textos) - 1 else segundo(mapear(limites[i + 1]), 'fim')
        if fim <= ini:
            # Alinhamento não confiável: usa divisão proporcional, sem tocar no áudio.
            return [{'cena': k + 1, 'inicio': round(duracao * limites[k] / len(original), 6),
                     'fim': round(duracao * limites[k + 1] / len(original), 6)} for k in range(len(textos))]
        tempos.append({'cena': i + 1, 'inicio': round(ini, 6), 'fim': round(fim, 6)})
    return tempos


def gerar(textos, perfil='referencia'):
    textos = [limpar_texto(t) for t in textos]
    if not textos:
        raise ValueError('O roteiro está sem falas.')
    for i, texto in enumerate(textos):
        if not chave_texto(texto):
            raise ValueError(f'A cena {i + 1} está sem narração.')
    texto = '\n'.join(textos)
    audio, sr = sintetizar(texto)
    duracao = len(audio) / sr
    palavras = alinhar_palavras(audio, sr, texto)
    tempos = tempos_da_fala(textos, palavras, duracao)
    print(f'{duracao:.1f}s | voz por referência | narração contínua, {len(textos)} cenas', flush=True)
    return audio, sr, tempos, palavras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--perfil', choices=list(PERFIS) + list(PERFIS_ANTIGOS), default=os.environ.get('MASCOTE_VOZ', 'referencia'))
    ap.add_argument('--teste', help='Texto curto para ouvir no painel')
    ap.add_argument('--saida', default='teste_mascote.wav')
    args = ap.parse_args()
    if args.teste:
        textos = [args.teste[:500]]
    else:
        roteiro = json.loads(Path('roteiro.json').read_text(encoding='utf-8'))
        textos = [c.get('narracao', '') for c in roteiro['cenas']]
    audio, sr, tempos, palavras = gerar(textos, args.perfil)
    import soundfile as sf
    # Só substitui a voz anterior depois que toda a nova fala foi gerada.
    pasta = Path(args.saida).resolve().parent if args.teste else Path.cwd()
    with tempfile.TemporaryDirectory(prefix='nova-voz-', dir=pasta) as tmp:
        temp = Path(tmp)
        sf.write(temp / 'voz.wav', audio, sr)
        if args.teste:
            (temp / 'voz.wav').replace(args.saida)
        else:
            (temp / 'tempos.json').write_text(json.dumps(tempos, ensure_ascii=False, indent=2), encoding='utf-8')
            (temp / 'palavras.json').write_text(json.dumps(palavras, ensure_ascii=False), encoding='utf-8')
            (temp / 'voz.wav').replace('narracao.wav')
            (temp / 'tempos.json').replace('tempos_cenas.json')
            (temp / 'palavras.json').replace('palavras.json')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as e:
        print(f'ERRO: {e}', file=sys.stderr, flush=True)
        sys.exit(1)
