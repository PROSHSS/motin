"""Configuração e preparação do apresentador, compartilhadas pelo painel e render."""
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

POSES = ['explicando', 'feliz', 'professor', 'surpreso', 'pensativo', 'desconfiado',
         'bravo', 'preocupado', 'ideia', 'positivo', 'estudando', 'ok']
POSICOES = ['esquerda', 'direita', 'ambos', 'oculto']
PERFIS = {'referencia': {'idioma': 'pt-BR', 'motor': 'qwen-referencia'}}
PERFIS_ANTIGOS = {p: 'referencia' for p in ('conversa', 'jovem', 'serio', 'divertido', 'suave', 'natural', 'feminina')}


def normalizar_perfil(perfil):
    return perfil if perfil in PERFIS else PERFIS_ANTIGOS.get(perfil, 'referencia')


def numero(v, padrao, minimo, maximo):
    try:
        n = float(v)
    except (ValueError, TypeError):
        n = padrao
    return max(minimo, min(maximo, n)) if math.isfinite(n) else padrao


def configurar(campos):
    ativo = campos.get('mascote_ativo') in ('sim', True)
    cfg = {
        'ativo': ativo,
        'posicao': campos.get('mascote_posicao', 'esquerda'),
        'expressao': campos.get('mascote_expressao', 'professor'),
        'expressao_direita': campos.get('mascote_expressao_direita', 'pensativo'),
        'tamanho': numero(campos.get('mascote_tamanho'), 27, 16, 38),
        'rodape': numero(campos.get('mascote_rodape'), 240, 80, 500),
        'animar': campos.get('mascote_animar', 'sim') == 'sim',
        'automatico': campos.get('mascote_automatico', 'sim') == 'sim',
        'voz': normalizar_perfil(campos.get('mascote_voz', 'referencia')),
        'fundo': campos.get('mascote_fundo', 'video'),
        'encaixe': campos.get('mascote_encaixe', 'cover'),
        'volume_original': numero(campos.get('mascote_volume'), 0, 0, 35) / 100,
        'repetir_video': campos.get('mascote_repetir', 'sim') == 'sim',
        'cenas': [], 'quadros': [], 'videos': [],
    }
    for k, permitidos, padrao in [('posicao', POSICOES, 'esquerda'),
                                   ('expressao', POSES, 'professor'),
                                   ('expressao_direita', POSES, 'pensativo'),
                                   ('voz', PERFIS, 'referencia'),
                                   ('fundo', ['video', 'editor'], 'video'),
                                   ('encaixe', ['cover', 'contain'], 'cover')]:
        if cfg[k] not in permitidos:
            cfg[k] = padrao
    if not ativo:
        return cfg
    try:
        trocas = json.loads(campos.get('mascote_trocas') or '[]')
    except (TypeError, ValueError):
        raise ValueError('As trocas do personagem estão inválidas. Recarregue o painel.')
    if not isinstance(trocas, list) or len(trocas) > 300:
        raise ValueError('Use até 300 trocas de personagem.')
    usados = set()
    for troca in trocas:
        if not isinstance(troca, dict):
            raise ValueError('Troca de personagem inválida.')
        por = troca.get('por', 'cena')
        if por not in ('cena', 'frame'):
            raise ValueError('Escolha uma cena ou um frame para cada troca.')
        n = numero(troca.get('numero'), -1, -1, 108000)
        if n != int(n) or n < (1 if por == 'cena' else 0) or (por == 'cena' and n > 100):
            raise ValueError('Cena deve ser de 1 a 100; frame deve ser inteiro de 0 a 108000.')
        chave = (por, int(n))
        if chave in usados:
            raise ValueError('Há duas trocas para a mesma cena ou frame.')
        usados.add(chave)
        item = {'numero': int(n)}
        for k, op in [('posicao', POSICOES), ('expressao', POSES), ('expressao_direita', POSES)]:
            v = troca.get(k)
            if v not in op:
                raise ValueError('Escolha a posição e as expressões de cada troca.')
            item[k] = v
        cfg['cenas' if por == 'cena' else 'quadros'].append(item)
    cfg['quadros'].sort(key=lambda x: x['numero'])
    return cfg


def sondar_video(arquivo):
    ffprobe = shutil.which('ffprobe') or shutil.which('ffprobe.exe')
    if not ffprobe:
        raise ValueError('Instale o FFmpeg com ffprobe no PATH para usar vídeos de fundo.')
    try:
        r = subprocess.run([ffprobe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(arquivo)],
                           capture_output=True, text=True, timeout=45)
        d = json.loads(r.stdout)
        videos = [s for s in d.get('streams', []) if s.get('codec_type') == 'video']
        dur = float(d.get('format', {}).get('duration') or videos[0].get('duration', 0))
        if r.returncode or not videos or not math.isfinite(dur) or dur < 0.1:
            raise ValueError()
        return {'duracao': dur, 'tem_audio': any(s.get('codec_type') == 'audio' for s in d.get('streams', []))}
    except (ValueError, KeyError, IndexError, subprocess.TimeoutExpired):
        raise ValueError(f'Não consegui ler o vídeo {Path(arquivo).name}. Converta para MP4 e envie novamente.')


def preparar(proj, dados, raiz):
    """Copia os assets reais para o public específico deste projeto."""
    arquivo = proj / 'mascote.json'
    if not arquivo.exists():
        return
    cfg = json.loads(arquivo.read_text(encoding='utf-8'))
    if not cfg.get('ativo'):
        return
    destino = proj / 'public' / 'mascotes'
    destino.mkdir(parents=True, exist_ok=True)
    for pose in POSES:
        origem = raiz / 'assets' / 'mascotes' / (pose + '.png')
        if not origem.exists():
            raise ValueError(f'Falta o personagem {pose}.png. Copie a pasta assets do pacote atualizado.')
        shutil.copyfile(origem, destino / origem.name)
    for v in cfg.get('videos', []):
        relativo = Path(v['arquivo'])
        origem = (proj / relativo).resolve()
        if not origem.is_relative_to(proj.resolve()) or not origem.is_file():
            raise ValueError('O vídeo de fundo não existe dentro deste projeto.')
        alvo = proj / 'public' / relativo
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem, alvo)
    dados['mascote'] = cfg


def roteiro_direto(proj, tema):
    arquivo = proj / 'falas_mascote.txt'
    falas = [l.strip() for l in arquivo.read_text(encoding='utf-8').splitlines() if l.strip()]
    if not falas:
        raise ValueError('Escreva pelo menos uma fala para o personagem.')
    return {'titulo': tema, 'narrado': True, 'modo': 'escuro', 'acento': '#ff3e38', 'cenas': [
        {'tipo': 'citacao', 'narracao': f, 'duracao': max(2.5, len(f.split()) / 2.7),
         'citacao': {'texto': f}, 'manchete': []} for f in falas]}
