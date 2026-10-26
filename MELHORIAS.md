# Melhorias do projeto de vídeo

Esta versão melhora o projeto Remotion Documentario enviado em doc-video.zip.
Não inclui a integração completa com Ollama, Cloudflare ou geração de voz.

## Alterações

- Saída de cada cena calculada pela duração da própria cena.
- Limites das cenas arredondados de forma consistente, evitando lacunas de um quadro.
- Legendas ocultas antes/depois da fala e em pausas maiores que 350 ms.
- Destaque dourado somente durante o intervalo da palavra falada.
- Legendas com fundo e contraste; ajuste de títulos longos.
- Imagens opcionais em cenas de tipo imagem: adicione `"imagem": "foto.jpg"`
  à cena e coloque foto.jpg na pasta public. Imagens recebem movimento suave
  e sobreposição escura para manter o texto legível.
- Fundo com gradiente e barras com acabamento dourado.
- Porcentagens com vírgula ou ponto; frações com denominador zero são rejeitadas.
- Mensagens de erro para JSON inválido, cenas sem tempos, intervalos sobrepostos,
  tipos desconhecidos e palavras fora de ordem.
- Duração considera o fim das cenas e das palavras.

## Executar

Com Node.js 24 e npm instalados:

    npm ci
    npx tsc --noEmit
    node --experimental-strip-types --test tests/data.test.mjs
    npm run preview
    npm run render

No ambiente Linux preparado, utilize o navegador já instalado:

    npm run preview -- --browser-executable=/usr/bin/chromium
    npm run render -- --browser-executable=/usr/bin/chromium --concurrency=2

Os três arquivos public/roteiro.json, public/tempos_cenas.json e
public/palavras.json devem estar sincronizados com public/narracao.wav.
O campo cena nos tempos começa em 1 e segue a ordem do roteiro.
Os dados de exemplo foram preservados e não foram checados como fatos jornalísticos.
