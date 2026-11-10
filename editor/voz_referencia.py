"""Caminhos e identidade da referência; seguro importar sem Torch no painel."""
import hashlib
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MODELO_ID = 'Qwen/Qwen3-TTS-12Hz-0.6B-Base'


def carregar_referencia():
    manifesto = RAIZ / 'vozes' / 'referencia.json'
    try:
        cfg = json.loads(manifesto.read_text(encoding='utf-8'))
        pasta = manifesto.parent.resolve()
        audio = (pasta / cfg['arquivo']).resolve()
        if not audio.is_relative_to(pasta) or not audio.is_file():
            raise ValueError('Áudio ausente ou fora da pasta vozes.')
        texto = ' '.join(cfg['transcricao'].split())
        if not texto:
            raise ValueError('A transcrição está vazia.')
        return audio, texto
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise RuntimeError('Não consegui ler vozes/referencia.json e seu áudio. Reextraia a pasta vozes do pacote.') from e


def identidade_referencia():
    audio, texto = carregar_referencia()
    return hashlib.sha256(audio.read_bytes() + texto.encode('utf-8') + MODELO_ID.encode()).hexdigest()


def python_voz():
    override = os.environ.get('MASCOTE_PYTHON_VOZ')
    executavel = Path(override) if override else RAIZ / '.venv-voz' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not executavel.is_file():
        raise RuntimeError('Execute o novo instalar_voz_mascote.bat para instalar a clonagem local da voz.')
    return str(executavel)


def pasta_modelo():
    return Path(os.environ.get('MASCOTE_MODELO_VOZ', str(RAIZ / 'modelos-voz' / 'Qwen3-TTS-0.6B')))


def pasta_alinhador():
    return Path(os.environ.get('MASCOTE_MODELO_ASR', str(RAIZ / 'modelos-voz' / 'whisper-tiny')))
