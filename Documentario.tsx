import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {TEXTO, clamp, useTema} from './Base';

export type Pal = {palavra: string; inicio: number; fim: number};
export type Grupo = {ini: number; fim: number; idx: number[]};

// Agrupa a narracao em frases curtas (ate 4 palavras / pontuacao). Usado pelas legendas e pelo zoom.
export const agruparPalavras = (palavras: Pal[]): Grupo[] => {
  const g: Grupo[] = [];
  let cur: number[] = [];
  palavras.forEach((p, i) => {
    cur.push(i);
    const pontua = /[.,;:!?…]$/.test(p.palavra);
    const longa = cur.map((k) => palavras[k].palavra).join(' ').length >= 24;
    if (cur.length >= 4 || longa || (pontua && cur.length >= 2) || (pontua && /[.!?…]$/.test(p.palavra))) {
      g.push({ini: palavras[cur[0]].inicio, fim: p.fim, idx: cur});
      cur = [];
    }
  });
  if (cur.length) g.push({ini: palavras[cur[0]].inicio, fim: palavras[cur[cur.length - 1]].fim, idx: cur});
  return g;
};

// ---------- CAMERA: tremor de camera na mao + "punch-in" a cada frase falada ----------
export const Camera: React.FC<{grupos: Grupo[]; ativo: boolean; batidas?: number[]; children: React.ReactNode}> = ({grupos, ativo, batidas = [], children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!ativo) return <AbsoluteFill>{children}</AbsoluteFill>;
  const t = frame / fps;
  // pulso: sobe rapido no inicio de cada frase e relaxa devagar
  let pulso = 0;
  for (let i = grupos.length - 1; i >= 0; i--) {
    const dt = t - grupos[i].ini;
    if (dt >= 0) {
      pulso = Math.exp(-dt * 2.2) * Math.min(1, dt / 0.08);
      break;
    }
  }
  // respiro lento (a "camera" se aproxima devagar o tempo todo)
  const deriva = 0.012 * Math.sin(frame / 95);
  // batida no meio das cenas longas: um "corte de camera" (aproximacao rapida) para nunca ficar parado
  let bat = 0;
  for (const b of batidas) {
    const d = frame - b;
    if (d >= 0 && d < 24) bat = Math.max(bat, Math.exp(-d / 7) * Math.min(1, d / 2));
  }
  // sem pulsos nem batidas: so uma aproximacao MUITO lenta e continua (nunca vai e volta)
  void pulso; void deriva; void bat;
  const esc = 1.02 + Math.min(0.03, frame / 3000);
  const x = 3.2 * Math.sin(frame * 0.071) + 1.8 * Math.sin(frame * 0.173 + 1.3);
  const y = 3.6 * Math.sin(frame * 0.058 + 0.7) + 1.6 * Math.sin(frame * 0.151);
  const rot = 0.14 * Math.sin(frame * 0.047 + 2.1);
  return (
    <AbsoluteFill style={{transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scale(${esc})`, transformOrigin: '50% 46%'}}>
      {children}
    </AbsoluteFill>
  );
};

// ---------- ACABAMENTO DE CINEMA: vinheta, tom de cor, grao vivo, riscos de filme ----------
export const Acabamento: React.FC<{cortes: number[]; serio?: boolean}> = ({cortes, serio}) => {
  const frame = useCurrentFrame();
  const T = useTema();
  // vazamento de luz nos cortes
  let luz = 0;
  let lado = 0;
  cortes.forEach((c, i) => {
    const d = frame - (c - 3);
    if (d >= 0 && d < 16) {
      const v = Math.sin((d / 16) * Math.PI);
      if (v > luz) { luz = v; lado = i % 2; }
    }
  });
  const claro = T.claro;
  return (
    <>
      {/* tom de cor: sombras frias, luzes quentes (fica mais "filmado") */}
      <AbsoluteFill style={{pointerEvents: 'none', zIndex: 30, mixBlendMode: 'soft-light', opacity: claro ? 0.22 : 0.34,
        background: serio ? 'linear-gradient(180deg, rgba(120,170,200,0.55) 0%, rgba(10,30,60,0.65) 100%)' : 'linear-gradient(180deg, rgba(255,170,90,0.55) 0%, rgba(40,70,120,0.55) 100%)'}} />
      {/* vinheta */}
      <AbsoluteFill style={{pointerEvents: 'none', zIndex: 31,
        background: `radial-gradient(ellipse at 50% 48%, rgba(0,0,0,0) 52%, rgba(0,0,0,${claro ? 0.22 : serio ? 0.5 : 0.42}) 100%)`}} />
      {/* vazamento de luz */}
      {luz > 0.01 ? (
        <AbsoluteFill style={{pointerEvents: 'none', zIndex: 32, mixBlendMode: 'screen', opacity: luz * 0.55,
          background: `radial-gradient(ellipse at ${lado ? '95% 20%' : '5% 75%'}, rgba(255,150,60,0.95) 0%, rgba(255,90,40,0.35) 35%, rgba(255,90,40,0) 70%)`}} />
      ) : null}
      {/* grao de filme (mais forte que o grao base, troca a cada 2 quadros) */}
      <AbsoluteFill style={{opacity: claro ? 0.07 : 0.11, pointerEvents: 'none', mixBlendMode: 'overlay', zIndex: 33}}>
        <svg width="1080" height="1920" viewBox="0 0 540 960" preserveAspectRatio="none">
          <filter id="gf">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={(Math.floor(frame / 2) * 7) % 97} />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="540" height="960" filter="url(#gf)" />
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------- BARRA DE PROGRESSO fina no topo (segura o espectador ate o fim) ----------
export const Progresso: React.FC<{total: number; cortes?: number[]}> = ({total, cortes = []}) => {
  const frame = useCurrentFrame();
  const T = useTema();
  const p = interpolate(frame, [0, total], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: '100%', height: 7, zIndex: 40, background: 'rgba(255,255,255,0.14)'}}>
      <div style={{width: `${p * 100}%`, height: '100%', background: T.acento, boxShadow: `0 0 12px ${T.acento}`}} />
      {cortes.map((c, i) => (
        <div key={i} style={{position: 'absolute', top: 0, bottom: 0, left: `${(c / total) * 100}%`, width: 3, background: 'rgba(0,0,0,0.75)'}} />
      ))}
    </div>
  );
};

// ---------- LEGENDA DOCUMENTARIO: fundo transparente, contorno discreto e palavra falada em destaque ----------
export const LegendaDoc: React.FC<{palavras: Pal[]; grupos: Grupo[]; bottom?: number}> = ({palavras, grupos, bottom = 330}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  if (!grupos.length) return null;
  const gi = grupos.findIndex((g, i) => t >= g.ini - 0.08 && t < (grupos[i + 1]?.ini ?? Infinity) - 0.05);
  if (gi < 0) return null;
  const grp = grupos[gi];
  const ate = Math.min(Math.max(grp.fim + 0.6, grp.ini + 1.1), grupos[gi + 1]?.ini ?? Infinity);
  if (t > ate) return null;
  const entrada = Easing.out(Easing.cubic)(interpolate(t - grp.ini, [-0.08, 0.18], [0, 1], clamp));
  const saida = interpolate(t, [ate - 0.12, ate], [1, 0], clamp);
  let atual = -1;
  grp.idx.forEach((k) => { if (t >= palavras[k].inicio) atual = k; });
  return (
    <div style={{position: 'absolute', left: 48, right: 150, bottom, display: 'flex', justifyContent: 'center', zIndex: 15, opacity: entrada * saida, background: 'transparent'}}>
      <div style={{position: 'relative', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', rowGap: 2, columnGap: 16, maxWidth: 980,
        transform: `translateY(${(1 - entrada) * 22}px)`}}>
        {grp.idx.map((k) => {
          const p = palavras[k];
          const dita = t >= p.inicio;
          const ativa = k === atual;
          const pop = ativa ? 1 + 0.12 * Math.exp(-(t - p.inicio) * 11) : 1;
          // numeros e siglas ficam em destaque o tempo todo (o olho acha o dado importante)
          const forte = /\d/.test(p.palavra) || /^[A-ZÀ-Ý]{2,}[.,;:!?]*$/.test(p.palavra);
          return (
            <span key={k} style={{
              fontFamily: TEXTO, fontWeight: 900, fontSize: forte ? 82 : 70, lineHeight: 1.12, letterSpacing: -0.5,
              color: ativa || (forte && dita) ? T.acento : T.claro ? '#15151b' : '#ffffff', opacity: dita ? 1 : 0.7,
              WebkitTextStroke: T.claro ? '1px rgba(255,255,255,0.7)' : '1px rgba(0,0,0,0.65)',
              textShadow: T.claro ? '0 2px 4px rgba(255,255,255,0.8)' : '0 2px 4px rgba(0,0,0,0.75)',
              transform: `scale(${pop})`, display: 'inline-block',
            }}>{p.palavra}</span>
          );
        })}
      </div>
    </div>
  );
};
