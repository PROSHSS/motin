# Motin — criação de vídeos

Projeto Remotion para montar vídeos verticais com narração, legendas e gráficos.

## Testar sem baixar o código

Depois que este código estiver no GitHub:

1. No repositório, clique em **Code → Codespaces → Create codespace**.
2. Aguarde a preparação inicial. O ambiente instala as dependências e inicia a prévia.
3. Na aba **Ports**, abra a porta **3000** no navegador, mantendo a visibilidade privada.
4. No Remotion Studio, selecione **Documentario** e use o botão de reprodução.

O Codespaces pode consumir a cota da sua conta GitHub. Pare o ambiente quando terminar.

Nas próximas vezes, reabra o **mesmo Codespace**. O código fica no editor online;
você não precisa baixar um ZIP a cada melhoria. Se a prévia não abrir, execute
`bash scripts/start-preview.sh` no terminal e abra a porta 3000.

## Onde fazer alterações

| Arquivo | O que altera |
| --- | --- |
| `src/Video.tsx` | Visual, cenas, gráficos e legendas |
| `src/Root.tsx` | Composição, carregamento e duração |
| `public/roteiro.json` | Título e conteúdo das cenas |
| `public/tempos_cenas.json` | Início e fim de cada cena, em segundos |
| `public/palavras.json` | Palavras e tempos das legendas |
| `public/narracao.wav` | Áudio da narração |

Salve o arquivo no editor para atualizar a prévia. Após mudar arquivos de `public/`,
recarregue a página para carregar os dados novos. Os tempos devem corresponder ao áudio.

Antes de trocar dados ou alterar código, crie uma branch no painel Source Control.
Depois de testar, faça **Commit** e **Push/Sync Changes** para guardar a alteração
no GitHub. Salvar no editor muda o Codespace; enviar ao GitHub permite recuperar
o trabalho em outro ambiente. Não publique credenciais ou `config.json`.

Se uma melhoria for enviada ao GitHub a partir de outro ambiente, salve e envie
primeiro suas mudanças locais; depois use **Pull** na mesma branch para recebê-la.
O GitHub não sincroniza automaticamente o conteúdo de um Codespace já aberto.

## Verificar e exportar

No terminal:

```bash
npm run check          # TypeScript e testes de dados
npm run render:smoke   # Exporta um segundo para out/smoke.mp4
npm run render         # Exporta o vídeo completo para out/video.mp4
```

Você só precisa baixar o MP4 quando quiser guardar ou compartilhar o vídeo final.
A prévia no navegador serve para testar as alterações sem exportar tudo.
Ela pode ser menos fluida que o vídeo exportado, dependendo da máquina.

## Executar fora do Codespaces

Use Node.js 24, rode `npm ci` e depois `npm run dev`.
O Chromium instalado em `/usr/bin/chromium` é usado automaticamente no Linux.
Em outro caminho, configure `REMOTION_BROWSER_EXECUTABLE`; sem navegador instalado,
o Remotion usará seu fluxo padrão de download.

## Escopo

Esta versão contém a composição Documentario do ZIP enviado, com melhorias de
legendas, visual e validação. Os dados de exemplo são preservados, sem verificação
editorial. Geração automática com Ollama, Cloudflare e voz não está integrada aqui.
Consulte `MELHORIAS.md` para os detalhes das alterações anteriores.
