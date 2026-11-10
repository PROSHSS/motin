import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Confete} from '../Efeitos';
import {CenaSC, Esfera, FORTE, Manchete, PalavraFantasma, Pontos, SERIFA, TEXTO, clamp, sombraObjeto, useTema} from './Base';
import {Cartao, Icone} from './Objetos';
import type {Som} from './Cenas';

type P = {c: CenaSC; dur: number};
const ease = Easing.bezier(0.22, 1, 0.36, 1);
const fmt = (n: number) => Math.round(n).toLocaleString('pt-BR');

// =====================================================================
// COMPARAÇÃO: dois cartões (A x B) com selo "VS" e vencedor destacado
// =====================================================================
export const CenaComparacao: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cp = c.comparacao;
  if (!cp) return null;
  const lados = [
    {k: 'a' as const, d: cp.a, y: 800, de: -900},
    {k: 'b' as const, d: cp.b, y: 1330, de: 900},
  ];
  const vs = spring({frame: frame - 22, fps, config: {damping: 9, stiffness: 160, mass: 0.6}});
  const ven = ease(interpolate(frame, [58, 74], [0, 1], clamp));
  return (
    <AbsoluteFill>
      <Esfera x={960} y={380} r={330} />
      <Esfera x={90} y={1750} r={300} inicio={5} />
      <PalavraFantasma texto={c.fantasma ?? 'VS'} top={520} tam={360} />
      <Manchete linhas={c.manchete ?? []} top={230} inicio={4} />
      {lados.map((l, i) => {
        const e = spring({frame: frame - (6 + i * 10), fps, config: {damping: 15, stiffness: 95, mass: 0.9}});
        const ganha = cp.vencedor === l.k;
        const perde = !ganha;
        return (
          <div
            key={l.k}
            style={{
              position: 'absolute',
              left: 90,
              top: l.y - 215,
              width: 900,
              height: 430,
              borderRadius: 56,
              background: T.cartao,
              boxShadow: ganha && ven > 0 ? `0 0 0 ${8 * ven}px ${T.acento}, ${sombraObjeto(T, 1.2)}` : sombraObjeto(T, 1),
              transform: `translateX(${interpolate(e, [0, 1], [l.de, 0])}px) scale(${1 + (ganha ? 0.03 : -0.03) * ven})`,
              opacity: interpolate(e, [0, 0.3], [0, 1], clamp) * (perde ? 1 - 0.35 * ven : 1),
              padding: '34px 56px',
            }}
          >
            <div style={{fontFamily: TEXTO, fontWeight: 800, fontSize: 36, letterSpacing: 5, textTransform: 'uppercase', color: T.suave}}>{l.d.titulo}</div>
            <div style={{fontFamily: FORTE, fontSize: l.d.valor.length > 8 ? 92 : 116, letterSpacing: -4, color: T.cartaoTinta, lineHeight: 1.1, marginTop: 6}}>{l.d.valor}</div>
            <div style={{marginTop: 20, display: 'flex', flexDirection: 'column', gap: 10}}>
              {l.d.itens.slice(0, 3).map((it, k) => (
                <div key={k} style={{display: 'flex', alignItems: 'center', gap: 18, fontFamily: TEXTO, fontWeight: 600, fontSize: 40, color: T.cartaoTinta, opacity: interpolate(frame, [22 + i * 10 + k * 5, 32 + i * 10 + k * 5], [0, 1], clamp)}}>
                  <div style={{width: 16, height: 16, borderRadius: 8, background: ganha ? T.acento : T.suave}} />
                  {it}
                </div>
              ))}
            </div>
            {ganha ? (
              <div style={{position: 'absolute', right: 40, top: 30, width: 110, height: 110, borderRadius: 55, background: T.acento, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${ven}) rotate(${(1 - ven) * -40}deg)`}}>
                <Icone nome="Check" size={72} color={T.sobreAcento} sw={3.4} />
              </div>
            ) : null}
          </div>
        );
      })}
      <div
        style={{
          position: 'absolute', left: 540 - 62, top: 1065 - 62, width: 124, height: 124, borderRadius: 62,
          background: T.tinta, color: T.bg, fontFamily: FORTE, fontSize: 50, display: 'flex', alignItems: 'center', justifyContent: 'center',
          transform: `scale(${Math.max(0, vs)}) rotate(${interpolate(vs, [0, 1], [-90, 0])}deg)`, boxShadow: sombraObjeto(T, 0.8), zIndex: 5,
        }}
      >
        VS
      </div>
      <Confete inicio={66} x={540} y={cp.vencedor === 'a' ? 800 : 1330} qtd={24} cores={[T.acento, '#ffffff', T.tinta]} />
    </AbsoluteFill>
  );
};
export const sonsComparacao = (): Som[] => [
  {src: 'pop', f: 8, vol: 0.45},
  {src: 'pop', f: 18, vol: 0.45},
  {src: 'impacto', f: 24, vol: 0.5},
  {src: 'carimbo', f: 62, vol: 0.7},
  {src: 'brilho', f: 66, vol: 0.5},
];

// =====================================================================
// CONTADOR: número gigante que sobe, dentro de um anel que se enche
// =====================================================================
export const CenaContador: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const ct = c.contador;
  if (!ct) return null;
  const de = ct.de ?? 0;
  const p = ease(interpolate(frame, [10, 62], [0, 1], clamp));
  const valor = de + (ct.para - de) * p;
  const txt = `${ct.prefixo ?? ''}${fmt(valor)}${ct.sufixo ?? ''}`;
  const tam = txt.length <= 5 ? 280 : txt.length <= 8 ? 200 : txt.length <= 11 ? 150 : 118;
  const R = 400;
  const circ = 2 * Math.PI * R;
  const fim = frame >= 62;
  const pulso = fim ? 1 + 0.05 * Math.exp(-(frame - 62) * 0.25) * Math.cos((frame - 62) * 0.8) : 1;
  return (
    <AbsoluteFill>
      <Esfera x={120} y={400} r={320} />
      <Esfera x={980} y={1700} r={340} inicio={4} />
      <Manchete linhas={c.manchete ?? []} top={230} inicio={4} />
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0}}>
        <circle cx={540} cy={1110} r={R} fill={T.cartao} opacity={0.9} />
        <circle cx={540} cy={1110} r={R} fill="none" stroke={T.linha} strokeWidth={28} />
        <circle cx={540} cy={1110} r={R} fill="none" stroke={T.acento} strokeWidth={28} strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={circ * (1 - p)} transform="rotate(-90 540 1110)" />
      </svg>
      <div style={{position: 'absolute', left: 140, right: 140, top: 1110 - 250, textAlign: 'center', fontFamily: TEXTO, fontWeight: 800, fontSize: 38, letterSpacing: 6, textTransform: 'uppercase', color: T.suave, opacity: interpolate(frame, [4, 14], [0, 1], clamp)}}>
        {ct.rotulo}
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 1110 - tam * 0.62, textAlign: 'center', fontFamily: FORTE, fontSize: tam, letterSpacing: -6, color: T.cartaoTinta, transform: `scale(${pulso})`, whiteSpace: 'nowrap'}}>
        {txt}
      </div>
      <div style={{position: 'absolute', left: 170, right: 170, top: 1110 + 190, textAlign: 'center', fontFamily: SERIFA, fontStyle: 'italic', fontSize: 52, color: T.suave, opacity: interpolate(frame, [60, 74], [0, 1], clamp)}}>
        {ct.legenda}
      </div>
      <Confete inicio={62} x={540} y={1110} qtd={26} cores={[T.acento, '#ffffff', T.tinta]} />
    </AbsoluteFill>
  );
};
export const sonsContador = (): Som[] => [
  {src: 'pop', f: 3, vol: 0.4},
  {src: 'riser', f: 8, vol: 0.4},
  {src: 'impacto', f: 62, vol: 0.85},
  {src: 'brilho', f: 63, vol: 0.5},
];

// =====================================================================
// RANKING: barras horizontais que crescem em sequência
// =====================================================================
export const CenaRanking: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const itens = (c.ranking?.itens ?? []).slice(0, 5);
  const max = Math.max(1, ...itens.map((i) => i.valor));
  const topo = 700;
  const passo = 192;
  return (
    <AbsoluteFill>
      <Esfera x={950} y={420} r={330} />
      <Esfera x={110} y={1760} r={290} inicio={5} />
      <Manchete linhas={c.manchete ?? []} top={230} inicio={4} />
      {itens.map((it, i) => {
        const ini = 10 + i * 12;
        const e = spring({frame: frame - ini, fps, config: {damping: 15, stiffness: 110, mass: 0.8}});
        const barra = ease(interpolate(frame, [ini + 4, ini + 30], [0, 1], clamp));
        const topo1 = i === 0;
        const larg = 560;
        return (
          <div
            key={i}
            style={{
              position: 'absolute', left: 70, width: 940, top: topo + i * passo, height: passo - 26, borderRadius: 48,
              background: T.cartao, boxShadow: sombraObjeto(T, 0.8),
              opacity: interpolate(e, [0, 0.4], [0, 1], clamp), transform: `translateX(${interpolate(e, [0, 1], [-300, 0])}px)`,
            }}
          >
            <div style={{position: 'absolute', left: 28, top: 33, width: 98, height: 98, borderRadius: 49, background: topo1 ? T.acento : T.tinta, color: topo1 ? T.sobreAcento : T.bg, fontFamily: FORTE, fontSize: 52, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{i + 1}</div>
            <div style={{position: 'absolute', left: 156, top: 22, fontFamily: TEXTO, fontWeight: 800, fontSize: it.nome.length > 16 ? 34 : 42, color: T.cartaoTinta, whiteSpace: 'nowrap'}}>{it.nome}</div>
            <div style={{position: 'absolute', left: 156, top: 88, width: larg, height: 36, borderRadius: 18, background: T.linha}}>
              <div style={{width: (it.valor / max) * larg * barra, height: '100%', borderRadius: 18, background: topo1 ? T.acento : T.suave}} />
            </div>
            <div style={{position: 'absolute', right: 34, top: 40, fontFamily: FORTE, fontSize: 54, letterSpacing: -2, color: T.cartaoTinta, opacity: barra}}>{it.texto ?? fmt(it.valor * barra)}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
export const sonsRanking = (c: CenaSC): Som[] => [
  ...(c.ranking?.itens ?? []).slice(0, 5).map((_, i) => ({src: 'pop', f: 10 + i * 12, vol: 0.45})),
  {src: 'brilho', f: 10 + Math.min(5, c.ranking?.itens.length ?? 1) * 12 + 14, vol: 0.4},
];

// =====================================================================
// LINHA DO TEMPO: linha vertical que se desenha com pontos e anos
// =====================================================================
export const CenaLinhaTempo: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ev = (c.linha_tempo ?? []).slice(0, 4);
  const topo = 740;
  const passo = 265;
  const total = (ev.length - 1) * passo;
  const prog = ease(interpolate(frame, [8, 8 + ev.length * 22], [0, 1], clamp));
  return (
    <AbsoluteFill>
      <Esfera x={960} y={380} r={340} />
      <Esfera x={100} y={1700} r={300} inicio={5} />
      <Manchete linhas={c.manchete ?? []} top={230} inicio={4} />
      <div style={{position: 'absolute', left: 150 - 6, top: topo, width: 12, height: total * prog, borderRadius: 6, background: T.tinta}} />
      {ev.map((e, i) => {
        const ini = 8 + i * 22;
        const m = spring({frame: frame - ini, fps, config: {damping: 11, stiffness: 150, mass: 0.7}});
        return (
          <div key={i}>
            <div style={{position: 'absolute', left: 150 - 30, top: topo + i * passo - 30, width: 60, height: 60, borderRadius: 30, background: i === ev.length - 1 ? T.acento : T.bg, border: `10px solid ${i === ev.length - 1 ? T.acento : T.tinta}`, transform: `scale(${Math.max(0, m)})`}} />
            <div style={{position: 'absolute', left: 250, top: topo + i * passo - 60, opacity: interpolate(m, [0, 0.5], [0, 1], clamp), transform: `translateX(${interpolate(m, [0, 1], [60, 0])}px)`}}>
              <div style={{fontFamily: SERIFA, fontStyle: 'italic', fontSize: 98, color: i === ev.length - 1 ? T.acento : T.tinta, lineHeight: 1}}>{e.ano}</div>
              <div style={{fontFamily: TEXTO, fontWeight: 600, fontSize: 42, color: T.suave, marginTop: 8, maxWidth: 740, lineHeight: 1.2}}>{e.texto}</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
export const sonsLinhaTempo = (c: CenaSC): Som[] => (c.linha_tempo ?? []).slice(0, 4).map((_, i) => ({src: i === 0 ? 'pop' : 'tick', f: 8 + i * 22, vol: 0.5}));

// =====================================================================
// ALERTA: cartão vermelho que treme + selo carimbado
// =====================================================================
export const CenaAlerta: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = c.alerta;
  if (!a) return null;
  const e = spring({frame, fps, config: {damping: 11, stiffness: 150, mass: 0.7}});
  const tremer = frame < 16 ? Math.sin(frame * 2.4) * (16 - frame) * 0.9 : 0;
  const selo = spring({frame: frame - 40, fps, config: {damping: 8, stiffness: 200, mass: 0.6}});
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: T.alerta, opacity: interpolate(frame, [0, 4, 18], [0, 0.18, 0], clamp)}} />
      <Esfera x={950} y={380} r={320} />
      <Esfera x={110} y={1720} r={300} inicio={5} />
      {[0, 1, 2].map((k) => {
        const t = ((frame + k * 14) % 42) / 42;
        return <div key={k} style={{position: 'absolute', left: 540 - 440 - t * 80, top: 1080 - 340 - t * 80, width: 880 + t * 160, height: 680 + t * 160, borderRadius: 80 + t * 40, border: `6px solid ${T.alerta}`, opacity: (1 - t) * 0.5}} />;
      })}
      <Manchete linhas={c.manchete ?? []} top={230} inicio={4} />
      <div style={{position: 'absolute', left: 100, top: 1080 - 340, width: 880, height: 680, borderRadius: 64, background: T.cartao, boxShadow: sombraObjeto(T, 1.3), transform: `translateX(${tremer}px) scale(${interpolate(e, [0, 1], [0.6, 1])})`, opacity: interpolate(e, [0, 0.3], [0, 1], clamp), textAlign: 'center', padding: '60px 56px'}}>
        <div style={{width: 190, height: 190, borderRadius: 95, background: T.alerta, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <Icone nome="TriangleAlert" size={110} color="#fff" sw={2.6} />
        </div>
        <div style={{fontFamily: FORTE, fontSize: a.titulo.length > 14 ? 74 : 96, letterSpacing: -2, textTransform: 'uppercase', color: T.cartaoTinta, marginTop: 34, lineHeight: 1.05}}>{a.titulo}</div>
        <div style={{fontFamily: TEXTO, fontWeight: 600, fontSize: 44, color: T.suave, marginTop: 20, lineHeight: 1.25}}>{a.texto}</div>
      </div>
      {a.selo ? (
        <div style={{position: 'absolute', right: 70, top: 1080 + 250, padding: '10px 34px', border: `10px solid ${T.alerta}`, borderRadius: 24, color: T.alerta, fontFamily: FORTE, fontSize: 84, letterSpacing: 4, textTransform: 'uppercase', background: T.bg, transform: `rotate(-9deg) scale(${interpolate(selo, [0, 1], [3, 1])})`, opacity: interpolate(selo, [0, 0.3], [0, 1], clamp)}}>
          {a.selo}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
export const sonsAlerta = (): Som[] => [
  {src: 'impacto', f: 0, vol: 0.8},
  {src: 'carimbo', f: 42, vol: 0.85},
];

// =====================================================================
// CITAÇÃO: aspas grandes e frase revelada palavra por palavra
// =====================================================================
export const CenaCitacao: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const q = c.citacao;
  if (!q) return null;
  const palavras = q.texto.split(/\s+/);
  const n = q.texto.length;
  const tam = n <= 60 ? 92 : n <= 110 ? 74 : 60;
  return (
    <AbsoluteFill>
      <Esfera x={940} y={440} r={340} />
      <Esfera x={120} y={1700} r={320} inicio={4} />
      <Pontos x={170} y={500} />
      <div style={{position: 'absolute', left: 80, top: 440, fontFamily: SERIFA, fontSize: 520, lineHeight: 1, color: T.acento, opacity: interpolate(frame, [0, 14], [0, 0.9], clamp), transform: `translateY(${interpolate(frame, [0, 18], [60, 0], clamp)}px)`}}>“</div>
      <div style={{position: 'absolute', left: 90, right: 90, top: 900, fontFamily: SERIFA, fontStyle: 'italic', fontSize: tam, lineHeight: 1.18, color: T.tinta}}>
        {palavras.map((w, i) => {
          const e = interpolate(frame, [12 + i * 3, 12 + i * 3 + 10], [0, 1], clamp);
          return <span key={i} style={{display: 'inline-block', marginRight: tam * 0.25, opacity: e, filter: `blur(${(1 - e) * 10}px)`, transform: `translateY(${(1 - e) * 28}px)`}}>{w}</span>;
        })}
      </div>
      {q.autor ? (
        <div style={{position: 'absolute', left: 90, bottom: 340, display: 'flex', alignItems: 'center', gap: 24, opacity: interpolate(frame, [12 + palavras.length * 3, 24 + palavras.length * 3], [0, 1], clamp)}}>
          <div style={{width: 90, height: 6, borderRadius: 3, background: T.acento}} />
          <div style={{fontFamily: TEXTO, fontWeight: 800, fontSize: 40, letterSpacing: 5, textTransform: 'uppercase', color: T.suave}}>{q.autor}</div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
export const sonsCitacao = (c: CenaSC): Som[] => [
  {src: 'pop', f: 6, vol: 0.4},
  {src: 'brilho', f: 14 + (c.citacao?.texto.split(/\s+/).length ?? 6) * 3, vol: 0.4},
];
