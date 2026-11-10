import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {CenaSC, FINA, FORTE, SERIFA, TEXTO, clamp, hash, useTema} from './Base';
import type {Som} from './Cenas';

// Cenas "de variedade" (inspiradas em motion design de perfis de edicao): todo texto vem da NARRACAO (montado por programa).
type P = {c: CenaSC; dur: number};
const ease = Easing.bezier(0.22, 1, 0.36, 1);
const fit = (txt: string, max: number, larg: number, k = 0.56) => Math.max(40, Math.min(max, Math.floor(larg / (Math.max(1, txt.length) * k))));
const lumHex = (hex: string) => {
  const h = /^#[0-9a-f]{6}$/i.test(hex) ? hex : '#c9a24a';
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

// ---------------------------------------------------------------------
// CARTAZ: tipografia cinetica em "tela inclinada" (palavras batem, uma riscada, seta desenhada)
// ---------------------------------------------------------------------
export const CenaCartaz: React.FC<P> = ({c, dur}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pal = (c.palavras ?? []).slice(0, 6);
  const real = new Set(c.realce ?? []);
  const cores = [T.tinta, T.acento, '#ffffff', T.acentoClaro];
  const t = frame / fps;
  const tilt = interpolate(frame, [0, dur], [-16, -9], clamp);
  const entrada = ease(interpolate(frame, [0, 22], [0, 1], clamp));
  const tam = pal.map((w) => fit(w, 230, 640, 0.6));
  const alturas = tam.map((s) => s * 1.02);
  const total = alturas.reduce((a, b) => a + b, 0);
  let y0 = 960 - total / 2;
  return (
    <AbsoluteFill style={{perspective: 1800}}>
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 38%, ${T.acento}22 0%, transparent 60%)`}} />
      <div
        style={{
          position: 'absolute', left: 90, right: 90, top: 250, bottom: 330, borderRadius: 38,
          background: 'linear-gradient(160deg, #17171b 0%, #0a0a0c 100%)', border: '3px solid rgba(255,255,255,0.12)',
          boxShadow: `0 60px 120px rgba(0,0,0,0.7), 0 0 90px ${T.acento}33`,
          transform: `rotateY(${tilt * entrada}deg) rotateX(${5 * entrada}deg) translateX(${(1 - entrada) * 300}px)`, transformOrigin: '30% 50%',
        }}
      />
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, transform: `rotateY(${tilt * 0.55 * entrada}deg)`, transformOrigin: '50% 50%'}}>
        {pal.map((w, i) => {
          const ini = 10 + i * 9;
          const e = spring({frame: frame - ini, fps, config: {damping: 11, stiffness: 160, mass: 0.7}});
          const y = (y0 += 0, 0);
          void y;
          const topo = 960 - total / 2 + alturas.slice(0, i).reduce((a, b) => a + b, 0);
          const risc = real.has(i) ? ease(interpolate(frame, [ini + 14, ini + 26], [0, 1], clamp)) : 0;
          return (
            <div key={i} style={{position: 'absolute', left: 150, right: 190, top: topo, height: alturas[i], display: 'flex', alignItems: 'center', justifyContent: i % 2 ? 'flex-end' : 'flex-start'}}>
              <div
                style={{
                  position: 'relative', fontFamily: FORTE, fontWeight: 900, fontSize: tam[i], lineHeight: 1, letterSpacing: -3, textTransform: 'uppercase', whiteSpace: 'nowrap',
                  color: cores[i % cores.length], opacity: interpolate(e, [0, 0.4], [0, 1], clamp),
                  transform: `scale(${interpolate(e, [0, 1], [1.7, 1])}) rotate(${interpolate(e, [0, 1], [i % 2 ? 6 : -6, 0])}deg)`,
                  textShadow: '0 8px 30px rgba(0,0,0,0.6)', filter: `blur(${interpolate(e, [0, 0.7], [10, 0], clamp)}px)`,
                }}
              >
                {w}
                {real.has(i) ? (
                  <svg style={{position: 'absolute', left: -10, top: '34%', width: 'calc(100% + 20px)', height: tam[i] * 0.4, overflow: 'visible'}} viewBox="0 0 100 20" preserveAspectRatio="none">
                    <path d="M0 14 C 20 2, 40 18, 60 6 S 90 10, 100 4" stroke={T.alerta} strokeWidth={5} fill="none" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - risc} />
                  </svg>
                ) : null}
              </div>
            </div>
          );
        })}
        {/* seta desenhada */}
        <svg style={{position: 'absolute', left: 560, top: 1280, width: 360, height: 260, overflow: 'visible'}} viewBox="0 0 360 260">
          <path d="M20 20 C 180 0, 330 80, 300 220" stroke={T.acento} strokeWidth={9} fill="none" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - ease(interpolate(frame, [30 + pal.length * 9, 56 + pal.length * 9], [0, 1], clamp))} />
          <path d="M255 190 L300 228 L335 175" stroke={T.acento} strokeWidth={9} fill="none" strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - ease(interpolate(frame, [52 + pal.length * 9, 64 + pal.length * 9], [0, 1], clamp))} />
        </svg>
      </div>
      <div style={{position: 'absolute', left: 120, top: 280, fontFamily: TEXTO, fontWeight: 800, fontSize: 26, letterSpacing: 6, color: T.suave, opacity: 0.8}}>{(c.rotulo ?? '').toUpperCase()}</div>
      <div style={{display: 'none'}}>{t}</div>
    </AbsoluteFill>
  );
};
export const sonsCartaz = (c: CenaSC): Som[] => [
  ...(c.palavras ?? []).slice(0, 6).map((_, i) => ({src: 'pop', f: 10 + i * 9, vol: 0.35})),
  {src: 'impacto', f: 10, vol: 0.5},
];

// ---------------------------------------------------------------------
// FOTO EM MOLDURA: foto num cartao com zoom lento + palavra-chave brilhando (estilo documentario)
// ---------------------------------------------------------------------
export const CenaFotoMoldura: React.FC<P> = ({c, dur}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const p = frame / Math.max(1, dur);
  const e = ease(interpolate(frame, [0, 22], [0, 1], clamp));
  const tags = (c.tags ?? []).slice(0, 2);
  const linhas = (c.linhas ?? []).slice(0, 4);
  const dir = hash((c.foto ?? 'x').length * 3.1) > 0.5 ? 1 : -1;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 30%, ${T.acento}28 0%, transparent 62%)`}} />
      <div
        style={{
          position: 'absolute', left: 70, right: 70, top: 300, height: 760, borderRadius: 26, overflow: 'hidden', background: '#000',
          border: '3px solid rgba(255,255,255,0.14)', boxShadow: `0 50px 100px rgba(0,0,0,0.75), 0 0 80px ${T.acento}30`,
          transform: `translateY(${(1 - e) * 140}px) scale(${0.92 + 0.08 * e})`, opacity: e,
        }}
      >
        {c.foto ? (
          <Img src={staticFile(c.foto)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'grayscale(0.25) contrast(1.08)', transform: `scale(${1.08 + 0.16 * p}) translateX(${dir * p * 40}px)`}} />
        ) : (
          <div style={{width: '100%', height: '100%', background: 'radial-gradient(ellipse at 50% 40%, #2a2a30 0%, #0c0c0f 75%)'}} />
        )}
        <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(0,0,0,0) 45%, rgba(0,0,0,0.78) 100%)'}} />
        <div style={{position: 'absolute', left: 30, bottom: 28, right: 30, display: 'flex', flexWrap: 'wrap', gap: 14}}>
          {tags.map((tg, i) => {
            const te = spring({frame: frame - (18 + i * 10), fps: 30, config: {damping: 13, stiffness: 140}});
            return (
              <div key={i} style={{fontFamily: FORTE, fontWeight: 900, fontSize: fit(tg, 120, 900 / Math.max(1, tags.length), 0.62), letterSpacing: 1, textTransform: 'uppercase', color: T.acento,
                textShadow: `0 0 28px ${T.acento}, 0 0 60px ${T.acento}88, 0 4px 0 rgba(0,0,0,0.6)`, opacity: te, transform: `translateY(${(1 - te) * 30}px) scale(${0.9 + 0.1 * te})`}}>
                {tg}
              </div>
            );
          })}
        </div>
      </div>
      <div style={{position: 'absolute', left: 90, right: 90, top: 1110}}>
        {linhas.map((l, i) => {
          const le = ease(interpolate(frame, [30 + i * 8, 46 + i * 8], [0, 1], clamp));
          return (
            <div key={i} style={{fontFamily: i === 0 ? TEXTO : FINA, fontWeight: i === 0 ? 800 : 400, fontSize: 52, lineHeight: 1.18, color: i === 0 ? T.tinta : T.suave, opacity: le, transform: `translateX(${(1 - le) * -40}px)`}}>
              {l}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
export const sonsFotoMoldura = (): Som[] => [{src: 'papel', f: 4, vol: 0.4}, {src: 'brilho', f: 20, vol: 0.35}];

// ---------------------------------------------------------------------
// BUSCA: barra de pesquisa digitando + resultados
// ---------------------------------------------------------------------
export const CenaBusca: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const q = c.consulta ?? '';
  const letras = Math.min(q.length, Math.max(0, Math.floor((frame - 14) * 0.9)));
  const e = ease(interpolate(frame, [0, 18], [0, 1], clamp));
  const res = (c.resultados ?? []).slice(0, 3);
  const ini = 14 + Math.ceil(q.length / 0.9) + 6;
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 70, right: 70, top: 470, height: 130, borderRadius: 70, background: T.claro ? '#fff' : '#202127', border: `3px solid ${T.acento}`, boxShadow: `0 20px 60px rgba(0,0,0,0.5), 0 0 50px ${T.acento}44`, display: 'flex', alignItems: 'center', padding: '0 44px', gap: 28, opacity: e, transform: `translateY(${(1 - e) * -60}px)`}}>
        <svg width="62" height="62" viewBox="0 0 24 24" fill="none" stroke={T.acento} strokeWidth="2.6" strokeLinecap="round"><circle cx="10.5" cy="10.5" r="6.5" /><path d="M16 16l5 5" /></svg>
        <div style={{fontFamily: TEXTO, fontWeight: 600, fontSize: fit(q, 62, 760, 0.52), color: T.tinta, whiteSpace: 'nowrap'}}>
          {q.slice(0, letras)}
          <span style={{opacity: Math.floor(frame / 8) % 2 ? 0 : 1, color: T.acento}}>|</span>
        </div>
      </div>
      <div style={{position: 'absolute', left: 90, right: 90, top: 690}}>
        {res.map((r, i) => {
          const re = spring({frame: frame - (ini + i * 12), fps: 30, config: {damping: 14, stiffness: 120}});
          return (
            <div key={i} style={{marginBottom: 54, opacity: interpolate(re, [0, 0.5], [0, 1], clamp), transform: `translateY(${(1 - re) * 60}px)`}}>
              <div style={{fontFamily: TEXTO, fontWeight: 700, fontSize: 30, color: T.suave, marginBottom: 6, letterSpacing: 1}}>{(c.rotulo ?? 'RESULTADO').toUpperCase()} {i + 1}</div>
              <div style={{fontFamily: TEXTO, fontWeight: 800, fontSize: fit(r, 58, 900, 0.5), lineHeight: 1.12, color: i === 0 ? T.acento : T.tinta}}>{r}</div>
              <div style={{height: 3, background: T.linha, marginTop: 18, width: `${re * 100}%`}} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
export const sonsBusca = (c: CenaSC): Som[] => [
  {src: 'clique', f: 14, vol: 0.5},
  ...(c.resultados ?? []).slice(0, 3).map((_, i) => ({src: 'pop', f: 14 + Math.ceil((c.consulta ?? '').length / 0.9) + 6 + i * 12, vol: 0.35})),
];

// ---------------------------------------------------------------------
// PILULA: fundo na cor de destaque, manchete com a palavra-chave numa pilula + formas girando
// ---------------------------------------------------------------------
const Estrela: React.FC<{x: number; y: number; r: number; cor: string; giro: number}> = ({x, y, r, cor, giro}) => {
  const pts = Array.from({length: 24}, (_, i) => {
    const a = (i / 24) * Math.PI * 2;
    const rr = i % 2 ? r * 0.72 : r;
    return `${r + Math.cos(a) * rr},${r + Math.sin(a) * rr}`;
  }).join(' ');
  return (
    <svg style={{position: 'absolute', left: x - r, top: y - r, width: r * 2, height: r * 2, transform: `rotate(${giro}deg)`}} viewBox={`0 0 ${r * 2} ${r * 2}`}>
      <polygon points={pts} fill={cor} />
    </svg>
  );
};
export const CenaPilula: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const fundo = T.acento;
  const escuroTxt = lumHex(fundo) > 0.45;
  const tx = escuroTxt ? '#101012' : '#ffffff';
  const pil = escuroTxt ? '#101012' : '#ffffff';
  const pilTx = escuroTxt ? fundo : '#101012';
  const linhas = (c.linhas ?? []).slice(0, 4);
  const dest = (c.destaque ?? '').toLowerCase();
  const e = ease(interpolate(frame, [0, 16], [0, 1], clamp));
  return (
    <AbsoluteFill style={{background: fundo, clipPath: `circle(${e * 150}% at 50% 50%)`}}>
      <Estrela x={110} y={300} r={190} cor={tx} giro={frame * 1.2} />
      <Estrela x={1010} y={1560} r={230} cor={pil} giro={-frame * 0.9} />
      <Estrela x={930} y={430} r={90} cor={pil} giro={frame * 2} />
      <div style={{position: 'absolute', left: 90, right: 90, top: 330, bottom: 450, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
        {linhas.map((l, i) => {
          const le = spring({frame: frame - (8 + i * 9), fps: 30, config: {damping: 13, stiffness: 150}});
          const partes = l.split(/(\s+)/);
          return (
            <div key={i} style={{fontFamily: FORTE, fontWeight: 900, fontSize: fit(l, 118, 880, 0.58), lineHeight: 1.14, color: tx, letterSpacing: -2, marginBottom: 12, opacity: interpolate(le, [0, 0.4], [0, 1], clamp), transform: `translateX(${(1 - le) * -120}px)`}}>
              {partes.map((w, k) => {
                const limpo = w.toLowerCase().replace(/[^a-zà-ÿ0-9%$]/g, '');
                const eh = dest && limpo === dest.replace(/[^a-zà-ÿ0-9%$]/g, '');
                return eh ? (
                  <span key={k} style={{background: pil, color: pilTx, borderRadius: 26, padding: '0 22px', display: 'inline-block', transform: `scale(${interpolate(le, [0, 1], [0.6, 1])}) rotate(${-2 * (1 - le)}deg)`}}>{w}</span>
                ) : (
                  <span key={k}>{w}</span>
                );
              })}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
export const sonsPilula = (): Som[] => [{src: 'whoosh', f: 2, vol: 0.4}, {src: 'pop', f: 14, vol: 0.45}, {src: 'pop', f: 23, vol: 0.4}];

// ---------------------------------------------------------------------
// GLITCH: palavra gigante com divisao de cor (RGB) e interferencia
// ---------------------------------------------------------------------
export const CenaGlitch: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const w = (c.palavra ?? '').toUpperCase();
  const tam = fit(w, 300, 900, 0.64);
  const ciclo = frame % 34;
  const forte = ciclo < 5 || (frame > 10 && frame < 22);
  const j = (n: number) => (hash(frame * 3.7 + n) - 0.5) * (forte ? 46 : 5);
  const e = ease(interpolate(frame, [0, 14], [0, 1], clamp));
  const base: React.CSSProperties = {position: 'absolute', left: 0, right: 0, top: 760, textAlign: 'center', fontFamily: FORTE, fontWeight: 900, fontSize: tam, lineHeight: 1, letterSpacing: -4, whiteSpace: 'nowrap'};
  const linhas = (c.linhas ?? []).slice(0, 3);
  return (
    <AbsoluteFill style={{background: '#050506'}}>
      <div style={{...base, color: '#ff2a55', transform: `translate(${j(1) - 8}px, ${j(2)}px)`, mixBlendMode: 'screen', opacity: e}}>{w}</div>
      <div style={{...base, color: '#00e5ff', transform: `translate(${j(3) + 8}px, ${j(4)}px)`, mixBlendMode: 'screen', opacity: e}}>{w}</div>
      <div style={{...base, color: '#ffffff', transform: `translate(${j(5)}px, 0)`, opacity: e, clipPath: forte ? `inset(${Math.floor(hash(frame) * 60)}% 0 ${Math.floor(hash(frame + 9) * 30)}% 0)` : undefined}}>{w}</div>
      <AbsoluteFill style={{background: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 2px, transparent 2px, transparent 5px)', opacity: 0.6}} />
      <div style={{position: 'absolute', left: 90, right: 90, top: 1010}}>
        {linhas.map((l, i) => {
          const le = ease(interpolate(frame, [22 + i * 9, 36 + i * 9], [0, 1], clamp));
          return <div key={i} style={{fontFamily: TEXTO, fontWeight: 700, fontSize: 52, color: i ? T.suave : T.acento, textAlign: 'center', opacity: le, transform: `translateY(${(1 - le) * 24}px)`, letterSpacing: 2}}>{l}</div>;
        })}
      </div>
    </AbsoluteFill>
  );
};
export const sonsGlitch = (): Som[] => [{src: 'impacto', f: 2, vol: 0.6}, {src: 'riser', f: 0, vol: 0.2}, {src: 'tick', f: 12, vol: 0.4}];

// ---------------------------------------------------------------------
// PASTA: cartoes empilhados que se abrem em leque (1, 2, 3)
// ---------------------------------------------------------------------
export const CenaPasta: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const itens = (c.cartoes ?? []).slice(0, 3);
  const cores = [T.acento, '#7c5cff', '#ff4d6d'];
  const tit = c.titulo ?? '';
  const te = ease(interpolate(frame, [0, 18], [0, 1], clamp));
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 80, right: 80, top: 260, fontFamily: FORTE, fontWeight: 900, fontSize: fit(tit, 130, 920, 0.6), lineHeight: 1.02, textTransform: 'uppercase', color: T.tinta, letterSpacing: -3, opacity: te, transform: `translateY(${(1 - te) * 60}px)`}}>{tit}</div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 560}}>
        {itens.map((it, i) => {
          const ini = 10 + i * 12;
          const e = spring({frame: frame - ini, fps: 30, config: {damping: 13, stiffness: 110, mass: 0.9}});
          const abre = ease(interpolate(frame, [ini + 14, ini + 34], [0, 1], clamp));
          return (
            <div key={i} style={{
              position: 'absolute', left: 120 + i * 40 * abre, top: i * 285 * abre + (1 - e) * 900, width: 780, height: 300, borderRadius: 40,
              background: `linear-gradient(145deg, ${cores[i]}, ${cores[i]}cc)`, boxShadow: '0 30px 70px rgba(0,0,0,0.55)',
              transform: `rotate(${(i - 1) * -3.5 * abre}deg)`, padding: '34px 44px', zIndex: i + 1,
            }}>
              <div style={{fontFamily: TEXTO, fontWeight: 900, fontSize: 30, letterSpacing: 4, color: lumHex(cores[i]) > 0.5 ? '#111' : '#fff', opacity: 0.85}}>{(c.rotulo ?? 'ITEM').toUpperCase()} {i + 1}</div>
              <div style={{fontFamily: FORTE, fontWeight: 900, fontSize: fit(it, 72, 1000, 0.6), lineHeight: 1.06, marginTop: 14, color: lumHex(cores[i]) > 0.5 ? '#111' : '#fff', textTransform: 'uppercase', letterSpacing: -1}}>{it}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
export const sonsPasta = (c: CenaSC): Som[] => (c.cartoes ?? []).slice(0, 3).map((_, i) => ({src: 'papel', f: 10 + i * 12, vol: 0.45}));
void SERIFA;
