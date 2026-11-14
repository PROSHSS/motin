# -*- coding: utf-8 -*-
"""Testes offline apos instalacao local, sem executar voz/geracao."""
import os
import subprocess
import sys
from pathlib import Path
from instalar import localizar_editor


def verificar():
    editor = localizar_editor()
    print('\nTestando', editor, '\n')
    stages = [
        ([sys.executable, '-m', 'compileall', '-q', str(editor)], editor, 'Sintaxe Python'),
        ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_motion_pro*.py', '-v'], editor, 'Testes Motion Pro'),
    ]
    tsc = editor / 'node_modules' / '.bin' / 'tsc.cmd'
    if tsc.is_file():
        stages.append(([str(tsc), '--noEmit'], editor, 'Compilacao TypeScript'))
    else:
        print('Aviso: node_modules nao existe. Pulando TypeScript; nao instalarei nada automaticamente.')
    has_error = False
    for cmd, cwd, label in stages:
        print('\n===', label, '===')
        try:
            p = subprocess.run(cmd, cwd=str(cwd), timeout=180, check=False)
            if p.returncode != 0:
                print('FALHOU:', label, 'codigo', p.returncode)
                has_error = True
            else:
                print('OK:', label)
        except (OSError, subprocess.TimeoutExpired) as err:
            print('Nao foi possivel executar:', label, err)
            has_error = True
    print('\nRESULTADO:', 'VERIFICAR ERROS ACIMA' if has_error else 'TESTES DISPONIVEIS CONCLUIDOS')
    return int(has_error)


if __name__ == '__main__':
    sys.exit(verificar())
