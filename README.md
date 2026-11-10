# Motion — editor de vídeos com personagem narrador

O editor local está em **`editor/`**, com os personagens, o suporte à voz de referência,
as variações de motion e as legendas transparentes do pacote atualizado.
A prévia anterior no navegador foi preservada separadamente em `src/`.

## Abrir o painel no Windows

**O site do GitHub guarda o código; clicar em um `.bat` no site mostra seu
conteúdo, sem executar o programa.** O painel completo continua rodando no PC.
O GitHub Pages também não executa o servidor Python deste painel.

Se o editor já funciona no seu PC, mantenha a instalação atual:

1. Baixe por **Code → Download ZIP** e extraia.
2. Copie o **conteúdo de `editor/`** para a pasta onde seu editor já está instalado,
   substituindo os arquivos do programa. Não substitua `config.json`, projetos,
   vídeos, ambientes Python nem modelos: eles não vêm nesta atualização.
3. Abra o `painel.bat` da sua instalação normalmente.

Para receber as próximas alterações sem baixar vários ZIPs, use o GitHub Desktop
ou clone uma única cópia de trabalho:

```powershell
git clone https://github.com/PROSHSS/motin.git
```

O `painel.bat` na raiz é um atalho para o painel em `editor/`. Essa pasta precisa
ter as dependências da sua instalação: Node/Remotion (`npm ci` dentro de
`editor/`), Python, FFmpeg, Ollama e o ambiente/modelos da voz. Mantenha também
seu `config.json` nessa pasta. Copie a pasta **`vozes/` da instalação que você já
usa** para `editor/vozes/` para manter a voz aprovada. As gravações pessoais não
fazem parte desta versão pública. Os detalhes estão em `editor/INSTALAR.txt` e
`editor/LEIA_PRIMEIRO_PERSONAGENS.txt`.

O pacote atualizado pressupõe a instalação base existente. Arquivos opcionais
de motores antigos, como `tts_kokoro.py` e `align.py`, não estavam no pacote
enviado; preserve os que já existem no seu PC se você usa esses recursos.

## Atualizar uma cópia clonada

Com o painel fechado e os trabalhos terminados, abra `atualizar.bat` na raiz.
Ele usa `git pull --ff-only` e interrompe a atualização se houver alterações
locais nos arquivos do programa, sem forçar a substituição.

Projetos, vídeos, dependências e configurações locais estão no `.gitignore`.
**Download ZIP** não cria uma cópia Git: nesse caso, copie os arquivos manualmente
ou use o GitHub Desktop para começar a trabalhar com o repositório.

## Espaço no computador

O GitHub facilita guardar e atualizar o código. Ele não transfere automaticamente
a execução nem os arquivos grandes para a nuvem. Modelos de voz, modelos do
Ollama, ambientes Python e vídeos ainda ocupam espaço onde a geração acontece.
Não apague esses arquivos da instalação que você usa.

O editor já aceita `pasta_dados` no `editor/config.json` para guardar projetos e
saídas em outro disco. Por exemplo, `"pasta_dados": "D:/Motion-dados"` usa essa
pasta para novos trabalhos. Isso não move automaticamente os projetos antigos.

## Prévia no navegador com Codespaces

A prévia anterior em `src/` e `public/` permite editar e exportar um vídeo de
exemplo em Remotion. Ela abre **sem áudio**, porque a gravação não acompanha o
repositório público. Para usar uma narração local autorizada, coloque o WAV em
`public/narracao.wav` e altere `public/audio.json` para `{"narracao": true}`.
As gravações e os vídeos estão ignorados pelo Git.

**Essa prévia não é o painel completo e não inclui a geração
automática com Ollama, Cloudflare e voz.** O Codespaces usa Linux e não executa
`painel.bat` como o Windows.

No repositório, abra **Code → Codespaces → Create codespace**. No terminal:

```bash
npm ci
npm run dev -- --port=3000
```

Abra a porta **3000** na aba **Ports**, mantendo a visibilidade privada, e
selecione **Documentario**. Também é possível iniciar com
`bash scripts/start-preview.sh`. O Codespaces usa a cota/plano da sua conta;
pare o ambiente quando terminar.

Para conferir e exportar a prévia:

```bash
npm run check
npm run render:smoke
npm run render
```

Use Node.js 24. Se houver Chromium em `/usr/bin/chromium`, ele será usado no
Linux; outro caminho pode ser indicado em `REMOTION_BROWSER_EXECUTABLE`.
As melhorias anteriores dessa prévia estão em `MELHORIAS.md`.

## Organização

| Caminho | Conteúdo |
| --- | --- |
| `painel.bat` | Atalho para abrir o editor local no Windows |
| `atualizar.bat` | Atualiza uma cópia clonada sem forçar mudanças locais |
| `editor/` | Editor completo do pacote atualizado |
| `editor/src/showcase/` | Animações da edição principal |
| `editor/assets/mascotes/` | Expressões do personagem |
| `editor/vozes/` | Instruções para restaurar a referência da sua instalação local |
| `src/` e `public/` | Prévia independente com o exemplo anterior |
| `tests/data.test.mjs` | Validação dos dados da prévia |

Os dados do vídeo de exemplo foram preservados; o repositório não representa
verificação editorial dos fatos narrados nesse exemplo.
