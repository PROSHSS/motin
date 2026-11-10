import React, {useLayoutEffect, useRef} from 'react';
import {useCurrentFrame} from 'remotion';

// ---------------------------------------------------------------------
// GUARDA ANTI-ESTOURO: nenhum texto sai da tela nem do cartao que o contem.
// A cada quadro mede (sem considerar animacoes) os textos da cena e, se algum
// passar do limite, reduz so o tamanho da letra o necessario.
// Elementos com data-guarda="ignorar" (palavras fantasma decorativas) ficam de fora.
// ---------------------------------------------------------------------
const MARGEM = 34;

const folha = (el: HTMLElement) => {
  // elemento "de texto": tem texto proprio e nenhum filho elemento com texto
  let tem = false;
  el.childNodes.forEach((n) => {
    if (n.nodeType === 3 && (n.textContent || '').trim()) tem = true;
  });
  return tem;
};

const posicaoNo = (el: HTMLElement, ancestral: HTMLElement) => {
  // posicao do layout (ignora transform) de `el` dentro de `ancestral`, subindo pela cadeia de offsetParent
  let x = 0;
  let y = 0;
  let n: HTMLElement | null = el;
  while (n && n !== ancestral) {
    x += n.offsetLeft;
    y += n.offsetTop;
    n = n.offsetParent as HTMLElement | null;
  }
  return n === ancestral ? {x, y} : null;
};

export const Guarda: React.FC<{children: React.ReactNode; largura?: number; altura?: number}> = ({
  children,
  largura = 1080,
  altura = 1920,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const frame = useCurrentFrame();
  useLayoutEffect(() => {
    const raiz = ref.current;
    if (!raiz) return;
    const todos = Array.from(raiz.querySelectorAll<HTMLElement>('*'));
    // 1) restaura o tamanho original
    todos.forEach((el) => {
      if (el.dataset.gOrig !== undefined) el.style.fontSize = el.dataset.gOrig;
    });
    // 2) mede e reduz
    todos.forEach((el) => {
      if (!folha(el)) return;
      if (el.closest('[data-guarda="ignorar"]')) return;
      if (el.dataset.gOrig === undefined) el.dataset.gOrig = el.style.fontSize;
      for (let passo = 0; passo < 4; passo++) {
        let k = 1;
        // (a) conteudo mais largo que a propria caixa (palavra comprida)
        if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0) k = Math.min(k, el.clientWidth / el.scrollWidth);
        // (b) passa do limite de algum ancestral que corta (overflow) ou da tela
        let a: HTMLElement | null = el.parentElement;
        while (a && a !== raiz.parentElement) {
          const cs = getComputedStyle(a);
          const corta = cs.overflow !== 'visible' || a === raiz;
          if (corta) {
            const p = posicaoNo(el, a);
            const limW = a === raiz ? largura : a.clientWidth;
            const limH = a === raiz ? altura : a.clientHeight;
            if (p && limW > 0) {
              const esq = p.x;
              const dir = p.x + el.offsetWidth;
              const m = a === raiz ? MARGEM : 10;
              if (dir > limW - m) {
                const util = Math.max(40, limW - m - Math.max(esq, m));
                k = Math.min(k, util / Math.max(1, el.offsetWidth));
              }
              if (esq < m - 2 && a === raiz) k = Math.min(k, Math.max(0.4, (el.offsetWidth - (m - esq) * 2) / el.offsetWidth));
              if (p.y + el.offsetHeight > limH - 6 && limH > 0 && el.offsetHeight > 0 && a !== raiz) {
                k = Math.min(k, Math.max(0.5, (limH - 6 - p.y) / el.offsetHeight));
              }
            }
          }
          if (a === raiz) break;
          a = a.parentElement;
        }
        if (k >= 0.985) break;
        const atual = parseFloat(getComputedStyle(el).fontSize);
        el.style.fontSize = `${Math.max(14, atual * k * 0.97)}px`;
      }
    });
  }, [frame]);
  return (
    <div ref={ref} style={{position: 'absolute', left: 0, top: 0, width: largura, height: altura, overflow: 'hidden'}}>
      {children}
    </div>
  );
};
