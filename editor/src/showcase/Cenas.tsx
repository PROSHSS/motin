import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import * as Lucide from 'lucide-react';
import {Cursor, Confete} from '../Efeitos';
import {
  CenaSC,
  Esfera,
  FINA,
  FORTE,
  Manchete,
  PalavraFantasma,
  Pontos,
  SERIFA,
  TEXTO,
  aberracao,
  clamp,
  filtroAberracao,
  sombraObjeto,
  useMola,
  useTema,
} from './Base';
import {Botao, Cartao, Celular, ConteudoPreco, Etiqueta, Lupa, TileIcone} from './Objetos';

type P = {c: CenaSC; dur: number};
export type Som = {src: string; f: number; vol: number};
const ease = Easing.bezier(0.22, 1, 0.36, 1);

// =====================================================================
// 1) GANCHO: palavra fantasma + etiqueta que despenca balançando
// =====================================================================
export const CenaGancho: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const v = c.variante ?? 'etiqueta';
  const txt = c.etiqueta?.texto ?? '-70%';
  const base = (
    <>
      <Esfera x={80} y={170} r={340} />
      <Esfera x={1010} y={1560} r={300} inicio={6} />
      <PalavraFantasma texto={c.fantasma ?? 'FALSO'} top={560} />
      <Pontos x={110} y={1180} />
    </>
  );
  if (v === 'carimbo') {
    const e = spring({frame: frame - 6, fps, config: {damping: 9, stiffness: 190, mass: 0.7}});
    const tremer = frame >= 6 && frame < 18 ? Math.sin(frame * 3) * (18 - frame) * 0.8 : 0;
    return (
      <AbsoluteFill>
        {base}
        <div style={{position: 'absolute', left: 90, right: 90, top: 790, height: 500, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: `16px solid ${T.alerta}`, borderRadius: 48, color: T.alerta, background: T.bg, opacity: interpolate(e, [0, 0.2], [0, 1], clamp), transform: `translateX(${tremer}px) rotate(${interpolate(e, [0, 1], [14, -7])}deg) scale(${interpolate(e, [0, 1], [3.2, 1])})`, boxShadow: `0 30px 60px ${T.sombra}`}}>
          <div style={{fontFamily: FORTE, fontSize: txt.length > 6 ? 150 : 210, letterSpacing: -4, textTransform: 'uppercase', lineHeight: 1}}>{txt}</div>
          {c.etiqueta?.sub ? <div style={{fontFamily: TEXTO, fontWeight: 900, fontSize: 52, letterSpacing: 10, marginTop: 14}}>{c.etiqueta.sub}</div> : null}
        </div>
        <Manchete linhas={c.manchete ?? []} top={250} inicio={10} />
      </AbsoluteFill>
    );
  }
  if (v === 'digitando') {
    const total = txt.length;
    const n = Math.min(total, Math.max(0, Math.floor((frame - 4) / 1.6)));
    const caret = frame % 14 < 8 ? '|' : ' ';
    return (
      <AbsoluteFill>
        {base}
        <div style={{position: 'absolute', left: 90, right: 90, top: 760, fontFamily: SERIFA, fontStyle: 'italic', fontSize: total > 36 ? 96 : 120, lineHeight: 1.1, color: T.tinta, textAlign: 'center'}}>
          {txt.slice(0, n)}
          <span style={{color: T.acento}}>{caret}</span>
        </div>
        {c.etiqueta?.sub ? <div style={{position: 'absolute', left: 0, right: 0, top: 1280, textAlign: 'center', fontFamily: TEXTO, fontWeight: 800, fontSize: 46, letterSpacing: 8, textTransform: 'uppercase', color: T.suave, opacity: interpolate(frame, [4 + total * 1.6, 14 + total * 1.6], [0, 1], clamp)}}>{c.etiqueta.sub}</div> : null}
        <Manchete linhas={c.manchete ?? []} top={250} inicio={8} />
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill>
      {base}
      <Etiqueta texto={txt} sub={c.etiqueta?.sub} x={540} y={900} inicio={2} />
      <Manchete linhas={c.manchete ?? []} top={250} inicio={8} />
    </AbsoluteFill>
  );
};
export const sonsGancho = (): Som[] => [
  {src: 'impacto', f: 0, vol: 0.9},
  {src: 'carimbo', f: 16, vol: 0.7},
];

// =====================================================================
// 2) CELULAR: notificações caem em cascata
// =====================================================================
export const CenaCelular: React.FC<P> = ({c}) => (
  <AbsoluteFill>
    <Esfera x={930} y={380} r={360} />
    <Esfera x={80} y={1700} r={280} inicio={5} />
    <PalavraFantasma texto={c.fantasma ?? 'TELA'} top={430} tam={380} />
    <Celular x={540} y={940} escala={0.9} inicio={4} notificacoes={c.notificacoes ?? []} />
    <Manchete linhas={c.manchete ?? []} top={250} inicio={6} />
  </AbsoluteFill>
);
export const sonsCelular = (c: CenaSC): Som[] =>
  (c.notificacoes ?? []).slice(0, 4).map((_, i) => ({src: 'pop', f: 4 + 20 + i * 12, vol: 0.45}));

// =====================================================================
// 3) LUPA: passa sobre o preço antigo e amplia
// =====================================================================
const CartaoPrecoFixo: React.FC<{preco: string; rotulo: string; riscar: number}> = ({preco, rotulo, riscar}) => {
  const T = useTema();
  return (
    <div
      style={{
        position: 'absolute',
        left: 540 - 440,
        top: 1050 - 190,
        width: 880,
        height: 380,
        borderRadius: 58,
        background: T.cartao,
        boxShadow: sombraObjeto(T, 1.1),
        overflow: 'hidden',
      }}
    >
      <ConteudoPreco preco={preco} rotulo={rotulo} riscar={riscar} />
    </div>
  );
};

export const CenaLupa: React.FC<P> = ({c}) => {
  const frame = useCurrentFrame();
  const riscar = ease(interpolate(frame, [32, 46], [0, 1], clamp));
  const lx = interpolate(ease(interpolate(frame, [14, 50], [0, 1], clamp)), [0, 1], [230, 800]);
  const ly = 1030 + Math.sin(frame / 7) * 10;
  const apar = interpolate(frame, [12, 22], [0, 1], clamp);
  const preco = c.lupa?.preco ?? 'R$ 1.299';
  const rotulo = c.lupa?.rotulo ?? 'PREÇO ANTES';
  return (
    <AbsoluteFill>
      <Esfera x={160} y={420} r={340} />
      <Esfera x={980} y={1720} r={330} inicio={4} />
      <PalavraFantasma texto={c.fantasma ?? 'PREÇO'} top={470} tam={400} />
      <Cartao x={540} y={1050} w={880} h={380}>
        <ConteudoPreco preco={preco} rotulo={rotulo} riscar={riscar} />
      </Cartao>
      <Lupa lx={lx} ly={ly} r={190} zoom={1.65} opac={apar}>
        <CartaoPrecoFixo preco={preco} rotulo={rotulo} riscar={riscar} />
      </Lupa>
      <Manchete linhas={c.manchete ?? []} top={250} inicio={6} />
    </AbsoluteFill>
  );
};
export const sonsLupa = (): Som[] => [
  {src: 'pop', f: 3, vol: 0.45},
  {src: 'whoosh', f: 14, vol: 0.3},
  {src: 'tick', f: 34, vol: 0.6},
];

// =====================================================================
// 4) PROCESSO: campo digitando, cursor clica, preço sobe, selo de desconto
// =====================================================================
export const CenaProcesso: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = c.processo ?? {rotulo: 'Preço do produto', campo: 'R$ 999', de: 'R$ 1.299', para: 'R$ 909', badge: '30% OFF', final: '', botao: 'Aplicar'};
  const CX = 540;
  const CY = 1150;
  const W = 920;
  const H = 840;
  const X0 = CX - W / 2;
  const Y0 = CY - H / 2;
  const digitado = p.campo.slice(0, Math.max(0, Math.floor((frame - 16) / 3)));
  const caret = frame % 16 < 9 && frame < 62 ? '|' : '';
  const clique = 60;
  const apertar = interpolate(frame, [clique, clique + 3, clique + 9], [1, 0.9, 1], clamp);
  const contar = ease(interpolate(frame, [clique + 3, clique + 18], [0, 1], clamp));
  const mostrandoDe = frame >= clique + 3;
  const numDe = Math.round(999 + (1299 - 999) * contar);
  const textoDe = frame >= clique + 20 ? p.de : `R$ ${numDe.toLocaleString('pt-BR')}`;
  const sobe = interpolate(frame, [clique + 3, clique + 8, clique + 22], [0, 1, 0.55], clamp);
  const eBadge = spring({frame: frame - (clique + 28), fps, config: {damping: 8, stiffness: 190, mass: 0.6}});
  const risca = ease(interpolate(frame, [clique + 36, clique + 46], [0, 1], clamp));
  const ePara = spring({frame: frame - (clique + 42), fps, config: {damping: 13, stiffness: 120, mass: 0.8}});
  const eFinal = interpolate(frame, [clique + 58, clique + 70], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <Esfera x={140} y={330} r={360} />
      <Esfera x={1000} y={1650} r={300} inicio={5} />
      <Pontos x={850} y={440} />
      <Manchete linhas={c.manchete ?? []} top={240} inicio={6} />
      <Cartao x={CX} y={CY} w={W} h={H} inicio={2}>
        <div style={{position: 'absolute', left: 56, top: 48, fontFamily: TEXTO, fontWeight: 800, fontSize: 36, letterSpacing: 4, textTransform: 'uppercase', color: T.suave}}>
          {p.rotulo}
        </div>
        {/* campo */}
        <div
          style={{
            position: 'absolute',
            left: 56,
            top: 120,
            width: W - 112,
            height: 150,
            borderRadius: 32,
            background: T.claro ? '#f1f0ec' : '#26262b',
            border: `4px solid ${mostrandoDe ? T.alerta : T.linha}`,
            display: 'flex',
            alignItems: 'center',
            padding: '0 40px',
            fontFamily: FORTE,
            fontSize: 96,
            letterSpacing: -3,
            color: mostrandoDe ? `rgb(${Math.round(22 + 204 * sobe)},${Math.round(22 + 30 * (1 - sobe))},${Math.round(26 + 16 * (1 - sobe))})` : T.cartaoTinta,
          }}
        >
          {mostrandoDe ? textoDe : digitado}
          <span style={{opacity: 0.8, color: T.acento}}>{caret}</span>
        </div>
        <Botao texto={p.botao} x={W - 56 - 150} y={370} w={300} h={104} apertar={apertar} />
        {/* resultado */}
        <div style={{position: 'absolute', left: 56, right: 56, top: 450}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 28, height: 150}}>
            <div style={{position: 'relative', fontFamily: FORTE, fontSize: 92, letterSpacing: -3, color: T.suave, opacity: mostrandoDe && frame >= clique + 30 ? 1 : 0}}>
              {p.de}
              <div style={{position: 'absolute', left: -8, top: '56%', height: 10, width: `calc(${risca * 100}% + 16px)`, borderRadius: 6, background: T.alerta}} />
            </div>
            <div
              style={{
                padding: '14px 34px',
                borderRadius: 60,
                background: T.acento,
                color: T.sobreAcento,
                fontFamily: FORTE,
                fontSize: 52,
                transform: `scale(${Math.max(0, eBadge)}) rotate(${interpolate(eBadge, [0, 1], [-18, -4])}deg)`,
                boxShadow: `0 14px 26px ${T.sombra}`,
              }}
            >
              {p.badge}
            </div>
          </div>
          <div
            style={{
              fontFamily: FORTE,
              fontSize: 168,
              letterSpacing: -6,
              color: T.cartaoTinta,
              transform: `translateY(${interpolate(ePara, [0, 1], [60, 0])}px) scale(${interpolate(ePara, [0, 1], [0.8, 1])})`,
              opacity: interpolate(ePara, [0, 0.4], [0, 1], clamp),
              lineHeight: 1.1,
            }}
          >
            {p.para}
          </div>
          <div style={{fontFamily: SERIFA, fontStyle: 'italic', fontSize: 50, color: T.suave, opacity: eFinal, marginTop: 6}}>{p.final}</div>
        </div>
      </Cartao>
      <Cursor pontos={[{f: clique, x: X0 + W - 56 - 100, y: Y0 + 370 + 20, clique: true}]} sumirApos={26} />
    </AbsoluteFill>
  );
};
export const sonsProcesso = (): Som[] => [
  {src: 'pop', f: 3, vol: 0.45},
  {src: 'tick', f: 22, vol: 0.4},
  {src: 'tick', f: 31, vol: 0.4},
  {src: 'tick', f: 40, vol: 0.4},
  {src: 'clique', f: 60, vol: 0.7},
  {src: 'riser', f: 56, vol: 0.25},
  {src: 'carimbo', f: 88, vol: 0.75},
  {src: 'pop', f: 102, vol: 0.5},
];

// =====================================================================
// 5) GRÁFICO: clica em "ver histórico" e a linha de 90 dias se desenha
// =====================================================================
export const CenaGrafico: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const g = c.grafico ?? {rotulo: 'Preço nos últimos 90 dias', valores: [100, 102, 99, 101, 100, 148, 150, 149, 151, 150, 105, 104], marcadores: [], botao: 'Ver histórico'};
  const CX = 540;
  const CY = 1130;
  const W = 940;
  const H = 820;
  const X0 = CX - W / 2;
  const Y0 = CY - H / 2;
  const n = g.valores.length;
  const mn = Math.min(...g.valores);
  const mx = Math.max(...g.valores);
  const gx = (i: number) => 60 + ((W - 120) * i) / Math.max(1, n - 1);
  const gy = (v: number) => 250 + 460 - ((v - mn) / (mx - mn || 1)) * 380;
  const clique = 14;
  const apertar = interpolate(frame, [clique, clique + 3, clique + 9], [1, 0.9, 1], clamp);
  const p = ease(interpolate(frame, [clique + 6, clique + 44], [0, 1], clamp));
  const d = g.valores.map((v, i) => `${i === 0 ? 'M' : 'L'} ${gx(i)} ${gy(v)}`).join(' ');
  const cabeca = p * (n - 1);
  const ci = Math.min(n - 2, Math.floor(cabeca));
  const cf = cabeca - ci;
  const hx = gx(ci) + (gx(ci + 1) - gx(ci)) * cf;
  const hy = gy(g.valores[ci]) + (gy(g.valores[ci + 1]) - gy(g.valores[ci])) * cf;
  return (
    <AbsoluteFill>
      <Esfera x={940} y={360} r={350} />
      <Esfera x={120} y={1740} r={300} inicio={5} />
      <Manchete linhas={c.manchete ?? []} top={240} inicio={6} />
      <Cartao x={CX} y={CY} w={W} h={H} inicio={2}>
        <div style={{position: 'absolute', left: 56, top: 52, fontFamily: TEXTO, fontWeight: 800, fontSize: 34, letterSpacing: 3, textTransform: 'uppercase', color: T.suave}}>
          {g.rotulo}
        </div>
        <Botao texto={g.botao} x={W - 56 - 160} y={96} w={320} h={92} apertar={apertar} escuro />
        <svg width={W} height={H} style={{position: 'absolute', left: 0, top: 0}}>
          {[0, 1, 2, 3].map((k) => (
            <line key={k} x1={40} x2={W - 40} y1={250 + k * 153} y2={250 + k * 153} stroke={T.linha} strokeWidth={3} strokeDasharray="8 12" />
          ))}
          <line x1={40} x2={W - 40} y1={gy(g.valores[0])} y2={gy(g.valores[0])} stroke={T.suave} strokeWidth={4} strokeDasharray="4 10" opacity={interpolate(p, [0.1, 0.3], [0, 1], clamp)} />
          <path d={d} fill="none" stroke={T.cartaoTinta} strokeWidth={12} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - p} />
          {p > 0 ? (
            <>
              <circle cx={hx} cy={hy} r={30} fill={T.acento} opacity={0.35} />
              <circle cx={hx} cy={hy} r={16} fill={T.acento} stroke={T.cartao} strokeWidth={6} />
            </>
          ) : null}
        </svg>
        {g.marcadores.map((m, k) => {
          const quando = m.i / (n - 1);
          const e = interpolate(p, [quando, quando + 0.08], [0, 1], clamp);
          const alto = g.valores[m.i] >= (mn + mx) / 2;
          return (
            <div
              key={k}
              style={{
                position: 'absolute',
                left: Math.min(Math.max(gx(m.i) - 130, 10), W - 270),
                width: 260,
                top: gy(g.valores[m.i]) + (alto ? -120 : 54),
                textAlign: 'center',
                opacity: e,
                transform: `translateY(${interpolate(e, [0, 1], [alto ? 20 : -20, 0])}px) scale(${interpolate(e, [0, 1], [0.8, 1])})`,
              }}
            >
              <span
                style={{
                  display: 'inline-block',
                  padding: '10px 26px',
                  borderRadius: 40,
                  background: k === 0 ? T.alerta : T.acento,
                  color: k === 0 ? '#fff' : T.sobreAcento,
                  fontFamily: TEXTO,
                  fontWeight: 900,
                  fontSize: 34,
                  whiteSpace: 'nowrap',
                }}
              >
                {m.texto}
              </span>
            </div>
          );
        })}
      </Cartao>
      <Cursor pontos={[{f: clique, x: X0 + W - 56 - 110, y: Y0 + 96 + 12, clique: true}]} sumirApos={20} />
    </AbsoluteFill>
  );
};
export const sonsGrafico = (c: CenaSC): Som[] => {
  const n = (c.grafico?.valores.length ?? 12) - 1;
  const base: Som[] = [
    {src: 'pop', f: 3, vol: 0.45},
    {src: 'clique', f: 14, vol: 0.7},
  ];
  (c.grafico?.marcadores ?? []).forEach((m) =>
    base.push({src: 'pop', f: Math.round(14 + 6 + (m.i / n) * 44 + 4), vol: 0.5}),
  );
  return base;
};

// =====================================================================
// 6) RAJADA: ícones em corte rápido, com flash e franja RGB
// =====================================================================
export const PASSO_RAJADA = 15;
export const CenaRajada: React.FC<P> = ({c, dur}) => {
  const frame = useCurrentFrame();
  const itens = c.rajada ?? [];
  const idx = Math.min(itens.length - 1, Math.floor(frame / PASSO_RAJADA));
  const local = frame - idx * PASSO_RAJADA;
  const flash = interpolate(local, [0, 3], [0.75, 0], clamp);
  const amp = interpolate(local, [0, 5], [11, 0], clamp);
  const it = itens[idx];
  const T = useTema();
  const posicoes = [
    {x: 150, y: 520, r: 300},
    {x: 940, y: 600, r: 340},
    {x: 220, y: 1500, r: 330},
    {x: 900, y: 1560, r: 300},
    {x: 540, y: 900, r: 420},
  ];
  const pos = posicoes[idx % posicoes.length];
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', inset: 0, filter: filtroAberracao(amp)}}>
        <Esfera x={pos.x} y={pos.y} r={pos.r} inicio={idx * PASSO_RAJADA} />
        <Manchete linhas={c.manchete ?? []} top={230} inicio={2} />
        {it ? <TileIcone key={idx} icone={it.icone} texto={it.texto} destaque={idx === itens.length - 1} local={local} y={620} /> : null}
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 230, display: 'flex', justifyContent: 'center', gap: 22}}>
          {itens.map((_, i) => (
            <div
              key={i}
              style={{
                width: i === idx ? 70 : 22,
                height: 22,
                borderRadius: 11,
                background: i <= idx ? T.tinta : T.linha,
                opacity: i <= idx ? 1 : 0.7,
              }}
            />
          ))}
        </div>
      </div>
      <AbsoluteFill style={{background: '#fff', opacity: flash * (T.claro ? 1 : 0.4), pointerEvents: 'none'}} />
      <div style={{display: 'none'}}>{dur}</div>
    </AbsoluteFill>
  );
};
export const sonsRajada = (c: CenaSC): Som[] => [
  {src: 'riser', f: -30, vol: 0.4},
  ...(c.rajada ?? []).map((_, i) => ({src: i === (c.rajada?.length ?? 1) - 1 ? 'carimbo' : 'tick', f: i * PASSO_RAJADA, vol: 0.6})),
];

// =====================================================================
// 7) CHECKLIST: três passos marcados por cliques do cursor
// =====================================================================
export const CenaChecklist: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const itens = c.checklist ?? [];
  const topo = 760;
  const alt = 230;
  const quando = (i: number) => 14 + i * 20;
  return (
    <AbsoluteFill>
      <Esfera x={950} y={440} r={340} />
      <Esfera x={100} y={1700} r={300} inicio={4} />
      <Manchete linhas={c.manchete ?? []} top={230} inicio={4} />
      {itens.map((t, i) => {
        const ini = quando(i);
        const e = spring({frame: frame - (ini - 8), fps, config: {damping: 14, stiffness: 120, mass: 0.8}});
        const traco = interpolate(frame, [ini + 3, ini + 15], [0, 1], clamp);
        const mark = frame >= ini + 3;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 70,
              right: 70,
              top: topo + i * alt,
              height: alt - 36,
              borderRadius: 54,
              background: T.cartao,
              boxShadow: sombraObjeto(T, 1),
              display: 'flex',
              alignItems: 'center',
              gap: 44,
              padding: '0 50px',
              opacity: interpolate(e, [0, 0.4], [0, 1], clamp),
              transform: `translateX(${interpolate(e, [0, 1], [-260, 0])}px) scale(${mark ? 1 + 0.03 * Math.exp(-(frame - ini - 3) * 0.3) : 1})`,
            }}
          >
            <svg width={110} height={110} viewBox="0 0 110 110" style={{flexShrink: 0}}>
              <rect x={6} y={6} width={98} height={98} rx={30} fill={mark ? T.acento : 'transparent'} stroke={mark ? T.acento : T.suave} strokeWidth={7} />
              <path d="M 28 56 L 48 76 L 84 34" fill="none" stroke={T.sobreAcento} strokeWidth={13} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - traco} />
            </svg>
            <div style={{fontFamily: FORTE, fontSize: t.length > 12 ? 70 : 88, letterSpacing: -2, textTransform: 'uppercase', color: T.cartaoTinta}}>{t}</div>
          </div>
        );
      })}
      <Cursor
        pontos={itens.map((_, i) => ({f: quando(i), x: 165, y: topo + i * alt + (alt - 36) / 2 + 8, clique: true}))}
        sumirApos={20}
      />
      <Confete inicio={quando(Math.max(0, itens.length - 1)) + 8} x={540} y={topo + itens.length * alt} qtd={30} cores={[T.acento, '#ffffff', '#121212', T.ok]} />
    </AbsoluteFill>
  );
};
export const sonsChecklist = (c: CenaSC): Som[] => [
  ...(c.checklist ?? []).map((_, i) => ({src: 'clique', f: 14 + i * 20, vol: 0.65})),
  {src: 'brilho', f: 14 + ((c.checklist?.length ?? 1) - 1) * 20 + 8, vol: 0.55},
];

// =====================================================================
// 8) FECHO: pergunta minimalista + botão "Seguir" que o cursor clica
// =====================================================================
const Bolha: React.FC<{x: number; y: number; s: number; rot: number; inicio: number}> = ({x, y, s, rot, inicio}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const e = spring({frame: frame - inicio, fps: 30, config: {damping: 18, stiffness: 70, mass: 1.1}});
  return (
    <svg
      width={s}
      height={s}
      viewBox="0 0 200 200"
      style={{
        position: 'absolute',
        left: x - s / 2,
        top: y - s / 2,
        transform: `rotate(${rot + frame * 0.35}deg) scale(${e})`,
        filter: `drop-shadow(0 30px 40px ${T.sombra})`,
        opacity: 0.9,
      }}
    >
      <defs>
        <radialGradient id={`b${inicio}${rot}`} cx="35%" cy="30%" r="80%">
          <stop offset="0" stopColor={T.esfA} />
          <stop offset="0.6" stopColor={T.esfB} />
          <stop offset="1" stopColor={T.esfC} />
        </radialGradient>
      </defs>
      <path
        d="M 100 12 C 150 8 190 50 186 100 C 182 150 140 190 96 186 C 50 182 12 146 16 98 C 20 52 52 16 100 12 Z"
        fill={`url(#b${inicio}${rot})`}
      />
    </svg>
  );
};

export const CenaFecho: React.FC<P> = ({c}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const f = c.fecho ?? {pergunta: 'Você está pronto... para comprar sem cair em golpe?', cta: 'Siga para mais'};
  const palavras = f.pergunta.split(/\s+/);
  const some = interpolate(frame, [46, 58], [1, 0], clamp);
  const ini = 52;
  const eCta = spring({frame: frame - ini, fps, config: {damping: 12, stiffness: 120, mass: 0.8}});
  const clique = 78;
  const seguindo = frame >= clique + 2;
  const apertar = interpolate(frame, [clique, clique + 3, clique + 9], [1, 0.92, 1], clamp);
  return (
    <AbsoluteFill>
      <Bolha x={900} y={330} s={820} rot={20} inicio={0} />
      <Bolha x={150} y={1620} s={900} rot={200} inicio={4} />
      <div
        style={{
          position: 'absolute',
          left: 110,
          right: 110,
          top: 840,
          textAlign: 'center',
          fontFamily: TEXTO,
          fontWeight: 600,
          fontSize: 56,
          letterSpacing: 5,
          textTransform: 'uppercase',
          color: T.tinta,
          opacity: some,
          lineHeight: 1.35,
        }}
      >
        {palavras.map((w, i) => {
          const e = interpolate(frame, [6 + i * 3, 6 + i * 3 + 8], [0, 1], clamp);
          return (
            <span key={i} style={{display: 'inline-block', marginRight: 18, opacity: e, filter: `blur(${(1 - e) * 10}px)`, transform: `translateY(${(1 - e) * 24}px)`}}>
              {w}
            </span>
          );
        })}
      </div>
      {frame >= ini ? (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 860,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 60,
            opacity: interpolate(eCta, [0, 0.4], [0, 1], clamp),
            transform: `translateY(${interpolate(eCta, [0, 1], [60, 0])}px)`,
          }}
        >
          <div style={{fontFamily: SERIFA, fontStyle: 'italic', fontSize: 112, color: T.tinta, textAlign: 'center', lineHeight: 1}}>
            {c.fecho?.cta ?? 'Siga para mais'}
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              padding: '28px 64px',
              borderRadius: 100,
              background: seguindo ? T.ok : T.tinta,
              color: seguindo ? '#fff' : T.bg,
              fontFamily: TEXTO,
              fontWeight: 900,
              fontSize: 58,
              boxShadow: `0 20px 50px ${T.sombra}`,
              transform: `scale(${apertar * (seguindo ? 1 + 0.08 * Math.exp(-(frame - clique) * 0.25) * Math.cos((frame - clique) * 0.7) : 1)})`,
            }}
          >
            {seguindo ? <Lucide.UserCheck size={64} strokeWidth={2.6} /> : <Lucide.UserPlus size={64} strokeWidth={2.4} />}
            <span>{seguindo ? 'Seguindo' : 'Seguir'}</span>
          </div>
        </div>
      ) : null}
      <Cursor pontos={[{f: clique, x: 600, y: 1105 + 44, clique: true}]} sumirApos={24} />
      <Confete inicio={clique + 2} x={540} y={1130} />
    </AbsoluteFill>
  );
};
export const sonsFecho = (): Som[] => [
  {src: 'pop', f: 52, vol: 0.45},
  {src: 'clique', f: 78, vol: 0.7},
  {src: 'brilho', f: 80, vol: 0.65},
];
export {FINA, aberracao};
