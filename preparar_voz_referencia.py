"""Baixa pesos públicos uma vez; nunca envia o áudio ou o roteiro."""
import os
from voz_referencia import MODELO_ID, pasta_modelo, pasta_alinhador, carregar_referencia


def main():
    from huggingface_hub import snapshot_download
    os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
    carregar_referencia()
    print('Baixando modelo de voz (~2,5 GB). Pode retomar executando este instalador novamente.', flush=True)
    snapshot_download(MODELO_ID, revision='5d83992436eae1d760afd27aff78a71d676296fc',
                      local_dir=str(pasta_modelo()), max_workers=3)
    print('Baixando alinhador das legendas (~75 MB)...', flush=True)
    snapshot_download('Systran/faster-whisper-tiny', local_dir=str(pasta_alinhador()), max_workers=3,
                      allow_patterns=['config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt'])
    print('Pronto. Abra painel.bat e clique em Ouvir voz. A geração da voz é local.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise SystemExit(f'ERRO: {e}\nConfira a internet e execute instalar_voz_mascote.bat novamente.')
