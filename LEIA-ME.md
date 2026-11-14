# Kit do personagem Óbvio — Além do Óbvio

Pacote derivado das DUAS pranchas de expressões fornecidas.

## Conteúdo
- `sprites/`: 66 PNGs com transparência, cada expressão em um arquivo separado.
- `reacoes.json`: catálogo com identificadores, emoções, caminhos e dimensões.
- `mascote_overlay.py`: módulo Python independente para selecionar reações e sobrepor o personagem em quadros PIL.
- `exemplo_integracao.py`: demonstração funcional sem alterar arquivos do editor.
- `catalogo_visual.png`: conferência rápida das expressões.

## Instalação/uso
1. Copie a pasta Kit_Alem_do_Obvio para um local no seu projeto.
2. Instale Pillow, se ainda não estiver instalado: `pip install Pillow`.
3. Execute `python exemplo_integracao.py` na pasta do kit para criar `exemplo_1080x1920.png`.
4. Para integrar ao gerador Python, use `MascoteObvio.selecionar_reacao(...)` e `MascoteObvio.aplicar(...)` na etapa de composição de quadros.

**IMPORTANTE:** este kit não altera automaticamente o editor existente. Os arquivos-fonte do editor precisam ser analisados para conectar as opções à interface, análise do roteiro e pipeline real. Não foram feitas mudanças na instalação do usuário.

## Padrões recomendados do preset
- Vídeos 1080 x 1920, 9:16.
- Mascote preferencialmente no canto inferior esquerdo e afastado de textos da interface TikTok.
- Personagem visível quando acrescenta algo ao contexto; não em todos os quadros.
- Reações orientadas pela emoção do roteiro, com variação e sem repetição imediata.
- Legendas SEM tarja preta: somente texto + contorno/sombra discreta, renderizados diretamente sobre a cena.
- Narração em português brasileiro e tom responsivo ao assunto.

## Limitações
A classificação de emoções usa etiquetas curadas e palavras-chave simples; análise semântica avançada, sincronização labial, renderização real, áudio, legendas do editor e anti-repetição entre vídeos dependem do código do projeto e de testes no pipeline do usuário. Não foram testados nesse kit.
