import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import * as Lucide from 'lucide-react';

// ---------- TIPOS (os mesmos do Video.tsx) ----------
export type Elemento = {
  tipo: string;
  texto: string;
  icone?: string;
  gatilho?: string;
};
export type CenaDados = {
  narracao: string;
  tipo: string;
  destaque: string;
  imagem?: string;
  elementos?: Elemento[];
};
type Props = {cena: CenaDados; entradas: number[]; titulo: string; foto?: string};

const SANS = "'Segoe UI', Arial, sans-serif";
const SERIF = "Georgia, 'Times New Roman', serif";
const MONO = "Consolas, 'Courier New', monospace";

// ---------- UTILIDADES ----------
const numero = (t: string): number | null => {
  const f = t.match(/(\d+)\s*\/\s*(\d+)/);
  if (f) return (parseInt(f[1], 10) / parseInt(f[2], 10)) * 100;
  const m = t.replace(/\./g, '').match(/(\d+(?:,\d+)?)/);
  return m ? parseFloat(m[1].replace(',', '.')) : null;
};

const useSp = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (inicio: number, tipo: 'suave' | 'mola' | 'forte' = 'mola') =>
    spring({
      frame: frame - inicio,
      fps,
      config:
        tipo === 'suave'
          ? {damping: 200}
          : tipo === 'forte'
            ? {damping: 9, stiffness: 180, mass: 0.6}
            : {damping: 14, stiffness: 120, mass: 0.8},
    });
};

const clamp01 = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Grade: React.FC<{c: string}> = ({c}) => (
  <AbsoluteFill
    style={{
      backgroundImage: `linear-gradient(${c} 1px, transparent 1px), linear-gradient(90deg, ${c} 1px, transparent 1px)`,
      backgroundSize: '90px 90px',
    }}
  />
);

const Barcode: React.FC<{c: string}> = ({c}) => (
  <div style={{display: 'flex', gap: 4, height: 60}}>
    {[6, 2, 4, 2, 8, 3, 2, 5, 2, 7, 3, 2, 4, 6, 2, 3].map((w, i) => (
      <div key={i} style={{width: w, background: c}} />
    ))}
  </div>
);

// aparece com deslize + blur (usado nos textos)
const Entrada: React.FC<{
  inicio: number;
  dy?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({inicio, dy = 50, style, children}) => {
  const sp = useSp();
  const p = sp(inicio, 'suave');
  return (
    <div
      style={{
        opacity: p,
        transform: `translateY(${interpolate(p, [0, 1], [dy, 0])}px)`,
        filter: `blur(${interpolate(p, [0, 1], [14, 0])}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

// ---------- FOTO DE FUNDO (com zoom lento) ----------
export const FundoFoto: React.FC<{
  foto?: string;
  opacidade: number;
  filtro?: string;
  mistura?: React.CSSProperties['mixBlendMode'];
}> = ({foto, opacidade, filtro, mistura}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  if (!foto) return null;
  const zoom = interpolate(frame, [0, durationInFrames], [1.04, 1.18]);
  const dx = interpolate(frame, [0, durationInFrames], [0, -30]);
  return (
    <AbsoluteFill style={{overflow: 'hidden', opacity: opacidade, mixBlendMode: mistura}}>
      <Img
        src={staticFile(foto)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: filtro,
          transform: `scale(${zoom}) translateX(${dx}px)`,
        }}
      />
    </AbsoluteFill>
  );
};

// =====================================================================
// 1 — TIPOGRAFIA CINÉTICA (fundo creme)
//   destaque = palavra gigante | elementos[0] = frase pequena de cima
//   elementos[1..] = linhas de baixo (texto que começa com "~" fica riscado)
// =====================================================================
export const CenaCinetica: React.FC<Props> = ({cena, entradas, titulo, foto}) => {
  const sp = useSp();
  const frame = useCurrentFrame();
  const els = cena.elementos ?? [];
  const lead = els[0]?.texto ?? '';
  const resto = els.slice(1);
  const gigante = cena.destaque.toUpperCase();
  const tam = Math.max(90, Math.min(250, 900 / (0.66 * Math.max(gigante.length, 1))));
  const pg = sp(14, 'forte');

  return (
    <AbsoluteFill style={{background: '#f4efe6'}}>
      <FundoFoto foto={foto} opacidade={0.3} filtro="contrast(1.05) saturate(0.9)" mistura="multiply" />
      <Grade c="rgba(0,0,0,0.05)" />
      <div style={{position: 'absolute', top: 150, left: 80, opacity: sp(2, 'suave')}}>
        <Barcode c="#111" />
      </div>
      <div
        style={{
          position: 'absolute',
          top: 150,
          right: 80,
          fontFamily: MONO,
          fontSize: 26,
          color: '#555',
          textAlign: 'right',
          opacity: sp(4, 'suave'),
          maxWidth: 520,
        }}
      >
        {(titulo.length > 36 ? titulo.slice(0, titulo.lastIndexOf(' ', 36)).replace(/[ ,;:]+$/, '') + '…' : titulo).toUpperCase()}
        <br />
        HD · 4K
      </div>

      <div style={{position: 'absolute', top: Math.max(380, Math.min(720, Math.round(250 + (1200 - ((lead ? 80 : 0) + tam + resto.length * 90)) / 2))), left: 80, right: 80, fontFamily: SANS, color: '#111'}}>
        {lead && (
          <Entrada inicio={6} style={{fontSize: 58, fontWeight: 500, color: '#777'}}>
            {lead}
          </Entrada>
        )}
        <div
          style={{
            fontSize: tam,
            fontWeight: 900,
            fontStyle: 'italic',
            color: '#d3202a',
            lineHeight: 0.98,
            letterSpacing: -6,
            opacity: interpolate(pg, [0, 0.3], [0, 1], clamp01),
            transform: `scale(${interpolate(pg, [0, 1], [1.7, 1])}) rotate(${interpolate(pg, [0, 1], [-4, 0])}deg)`,
            transformOrigin: 'left center',
            whiteSpace: 'nowrap',
          }}
        >
          {gigante}
        </div>
        {resto.map((e, i) => {
          const riscado = e.texto.startsWith('~');
          const txt = riscado ? e.texto.slice(1).trim() : e.texto;
          const ini = Math.max(24 + i * 8, entradas[i + 1] ?? 0);
          const grande = i === resto.length - 1 && resto.length > 1;
          const pl = sp(ini + 8, 'suave');
          return (
            <Entrada
              key={i}
              inicio={ini}
              style={{
                fontSize: grande ? 108 : riscado ? 58 : 86,
                fontWeight: grande ? 900 : riscado ? 500 : 800,
                color: riscado ? '#888' : '#111',
                marginTop: 12,
                position: 'relative',
                display: 'block',
              }}
            >
              <span style={{position: 'relative', display: 'inline-block'}}>
                {txt}
                {riscado && (
                  <span
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: '54%',
                      height: 6,
                      width: `${pl * 100}%`,
                      background: '#d3202a',
                    }}
                  />
                )}
              </span>
            </Entrada>
          );
        })}
      </div>
      <div style={{display: 'none'}}>{frame}</div>
    </AbsoluteFill>
  );
};

// =====================================================================
// 2 — SILHUETAS E LUZ (fundo verde)
//   destaque = frase grande | elementos[0] = frase pequena de cima
// =====================================================================
const Pessoa: React.FC<{
  x: number;
  y: number;
  s: number;
  c: string;
  p: number;
  glow?: boolean;
}> = ({x, y, s, c, p, glow}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y + interpolate(p, [0, 1], [420, 0]),
      width: 80 * s,
      opacity: interpolate(p, [0, 0.3], [0, 1], clamp01),
      filter: glow ? `drop-shadow(0 0 ${40 + 20 * Math.sin(p * 20)}px ${c})` : undefined,
    }}
  >
    <div style={{width: 40 * s, height: 40 * s, borderRadius: '50%', background: c, margin: '0 auto'}} />
    <div
      style={{
        width: 80 * s,
        height: 120 * s,
        borderRadius: `${40 * s}px ${40 * s}px 8px 8px`,
        background: c,
        marginTop: 6 * s,
      }}
    />
  </div>
);

export const CenaSilhuetas: React.FC<Props> = ({cena, foto}) => {
  const sp = useSp();
  const frame = useCurrentFrame();
  const lead = cena.elementos?.[0]?.texto ?? '';
  const palavras = cena.destaque.split(/\s+/).filter(Boolean);
  const pulso = 1 + 0.03 * Math.sin(frame / 6);
  const heroP = sp(26, 'forte');
  const glowFrame = Math.max(0, frame - 26) / 20;

  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 40%, #1fcf5e 0%, #0a8a3a 60%, #064d22 100%)'}}>
      <FundoFoto foto={foto} opacidade={0.45} filtro="saturate(0.9) contrast(1.05)" mistura="overlay" />
      <div
        style={{
          position: 'absolute',
          width: 520,
          height: 520,
          borderRadius: '50%',
          background: '#ffffff18',
          top: 150,
          left: 280,
          transform: `scale(${pulso})`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 220,
          height: 220,
          borderRadius: '50%',
          background: '#ffffff22',
          top: 700 + Math.sin(frame / 20) * 20,
          left: -60,
        }}
      />
      <div style={{position: 'absolute', top: 260, left: 70, right: 70, textAlign: 'center', fontFamily: SANS, color: '#fff'}}>
        {lead && (
          <Entrada inicio={4} style={{fontSize: 60, fontWeight: 400}}>
            {lead}
          </Entrada>
        )}
        <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 22}}>
          {palavras.map((w, i) => {
            const p = sp(10 + i * 5, 'forte');
            return (
              <span
                key={i}
                style={{
                  fontSize: palavras.length > 2 ? 110 : 150,
                  fontWeight: 900,
                  fontStyle: 'italic',
                  lineHeight: 1.05,
                  display: 'inline-block',
                  transform: `scale(${interpolate(p, [0, 1], [0.3, 1])}) rotate(${interpolate(p, [0, 1], [-8, 0])}deg)`,
                  opacity: interpolate(p, [0, 0.4], [0, 1], clamp01),
                }}
              >
                {w}
              </span>
            );
          })}
        </div>
      </div>
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Pessoa key={i} x={-20 + i * 190} y={1010 + (i % 2) * 40} s={1.6} c="#04301a" p={sp(i * 3)} />
      ))}
      {[0, 1, 2, 3, 4].map((i) => (
        <Pessoa key={'b' + i} x={70 + i * 200} y={1130 + (i % 2) * 30} s={1.9} c="#021a0e" p={sp(6 + i * 3)} />
      ))}
      <Pessoa x={420} y={760} s={3.2} c="#ffe14a" p={heroP} glow />
      <div style={{display: 'none'}}>{glowFrame}</div>
    </AbsoluteFill>
  );
};

// =====================================================================
// 3 — DOCUMENTO COM MARCA-TEXTO E CARIMBO
//   destaque = texto do carimbo | elementos[0] = cabeçalho do papel
//   elementos[1] = frase do documento | elementos[2] = trecho a marcar
// =====================================================================
export const CenaDocumento: React.FC<Props> = ({cena, entradas, foto}) => {
  const sp = useSp();
  const frame = useCurrentFrame();
  const els = cena.elementos ?? [];
  const cab = els[0]?.texto ?? 'DOCUMENTO OFICIAL';
  const frase = els[1]?.texto ?? cena.narracao;
  const marcado = els[2]?.texto ?? '';
  let idx = marcado ? frase.toLowerCase().indexOf(marcado.toLowerCase()) : -1;
  let len = marcado.length;
  if (idx < 0) {
    const ws = frase.split(' ');
    const ult = ws.slice(-3).join(' ');
    idx = frase.length - ult.length;
    len = ult.length;
  }
  const antes = frase.slice(0, idx);
  const mark = frase.slice(idx, idx + len);
  const depois = frase.slice(idx + len);

  const queda = sp(2, 'mola');
  const tMarca = Math.max(22, entradas[2] ?? entradas[1] ?? 0);
  const marca = interpolate(frame, [tMarca, tMarca + 22], [0, 100], clamp01);
  const tCarimbo = Math.max(tMarca + 24, entradas[2] ?? 0);
  const pc = sp(tCarimbo, 'forte');
  const sacode = frame >= tCarimbo && frame < tCarimbo + 8 ? (frame % 2 ? 9 : -9) : 0;

  const grifo: React.CSSProperties = {
    backgroundImage: 'linear-gradient(transparent 20%, #ffd84a 20%, #ffd84a 90%, transparent 90%)',
    backgroundRepeat: 'no-repeat',
    backgroundSize: `${marca}% 100%`,
    padding: '0 6px',
    WebkitBoxDecorationBreak: 'clone',
    boxDecorationBreak: 'clone',
  };

  return (
    <AbsoluteFill style={{background: '#101014', transform: `translateX(${sacode}px)`}}>
      <FundoFoto foto={foto} opacidade={0.6} filtro="grayscale(0.1) brightness(0.9)" />
      <Grade c="rgba(255,255,255,0.04)" />
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 150,
          width: 780,
          height: 920,
          background: '#efe9d8',
          transform: `translateY(${interpolate(queda, [0, 1], [-1100, 0])}px) rotate(${interpolate(queda, [0, 1], [-14, -3])}deg)`,
          boxShadow: '0 40px 90px #000a',
          padding: 70,
          fontFamily: SERIF,
          color: '#222',
        }}
      >
        <div style={{fontFamily: MONO, fontSize: 24, color: '#888', letterSpacing: 3}}>{cab.toUpperCase()}</div>
        <div style={{fontSize: 58, fontWeight: 700, marginTop: 34, lineHeight: 1.28}}>
          {antes}
          <span style={grifo}>{mark}</span>
          {depois}
        </div>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              height: 12,
              background: '#cfc8b4',
              marginTop: 28,
              width: `${interpolate(sp(18 + i * 4, 'suave'), [0, 1], [0, 90 - i * 12])}%`,
            }}
          />
        ))}
      </div>
      <div
        style={{
          position: 'absolute',
          top: 1090,
          left: 500,
          transform: `rotate(-12deg) scale(${interpolate(pc, [0, 1], [3.2, 1])})`,
          opacity: interpolate(pc, [0, 0.25], [0, 0.93], clamp01),
          border: '10px solid #d3202a',
          color: '#d3202a',
          fontFamily: SANS,
          fontWeight: 900,
          fontSize: cena.destaque.length > 9 ? 70 : 100,
          padding: '4px 30px',
          borderRadius: 12,
          whiteSpace: 'nowrap',
        }}
      >
        {cena.destaque.toUpperCase()}
      </div>
    </AbsoluteFill>
  );
};

// =====================================================================
// 4 — VERSUS (tela dividida)   elementos[0] e [1] = "Nome 47,03%"
// =====================================================================
const parteVersus = (t: string) => {
  const valor = numero(t);
  const nome = t.replace(/\d+(?:[.,]\d+)?\s*(%|\/\d+)?/g, '').replace(/[|:–\-]+\s*$/g, '').replace(/^[|:–\-]+\s*/g, '').trim();
  return {valor, nome: nome || '—', original: t};
};

export const CenaVersus: React.FC<Props> = ({cena, entradas, foto}) => {
  const sp = useSp();
  const frame = useCurrentFrame();
  const els = cena.elementos ?? [];
  const a = parteVersus(els[0]?.texto ?? 'A');
  const b = parteVersus(els[1]?.texto ?? 'B');
  const maxV = Math.max(a.valor ?? 1, b.valor ?? 1, 1);
  const alturaMax = 860;
  const hA = ((a.valor ?? maxV) / maxV) * alturaMax;
  const hB = ((b.valor ?? maxV) / maxV) * alturaMax;
  const pPainel = sp(0, 'suave');
  const tA = Math.max(14, entradas[0] ?? 0);
  const tB = Math.max(tA + 10, entradas[1] ?? 0);
  const gA = sp(tA, 'suave');
  const gB = sp(tB, 'suave');
  const pVS = sp(Math.max(tB + 8, 30), 'forte');

  const fmt = (v: number | null, p: number, txt: string) => {
    if (v === null) return '';
    const casas = (txt.match(/,(\d+)/)?.[1] ?? '').length;
    const atual = (v * p).toFixed(casas).replace('.', ',');
    return txt.includes('%') ? `${atual}%` : atual;
  };

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: interpolate(pPainel, [0, 1], [-540, 0]),
          top: 0,
          width: 540,
          height: 1920,
          background: '#14161c',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 540 + interpolate(pPainel, [0, 1], [540, 0]),
          top: 0,
          width: 540,
          height: 1920,
          background: '#f1ece0',
        }}
      />
      <FundoFoto foto={foto} opacidade={0.38} filtro="saturate(0.9) contrast(1.05)" mistura="overlay" />
      <div style={{position: 'absolute', top: 210, left: 0, width: 540, textAlign: 'center', fontFamily: MONO, color: '#8a8f9c', fontSize: 36, letterSpacing: 3, opacity: pPainel, padding: '0 20px', boxSizing: 'border-box'}}>
        {a.nome.toUpperCase()}
      </div>
      <div style={{position: 'absolute', top: 210, left: 540, width: 540, textAlign: 'center', fontFamily: MONO, color: '#777', fontSize: 36, letterSpacing: 3, opacity: pPainel, padding: '0 20px', boxSizing: 'border-box'}}>
        {b.nome.toUpperCase()}
      </div>

      <div style={{position: 'absolute', left: 150, bottom: 520, width: 240, height: hA * gA, background: '#d3202a'}} />
      <div style={{position: 'absolute', left: 690, bottom: 520, width: 240, height: hB * gB, background: '#14161c'}} />
      <div style={{position: 'absolute', left: 0, width: 540, bottom: 520 + hA * gA + 24, textAlign: 'center', fontFamily: SERIF, fontWeight: 700, fontSize: 104, color: '#fff', opacity: gA}}>
        {fmt(a.valor, gA, a.original)}
      </div>
      <div style={{position: 'absolute', left: 540, width: 540, bottom: 520 + hB * gB + 24, textAlign: 'center', fontFamily: SERIF, fontWeight: 700, fontSize: 104, color: '#14161c', opacity: gB}}>
        {fmt(b.valor, gB, b.original)}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 450,
          top: 860,
          width: 180,
          height: 180,
          borderRadius: '50%',
          background: '#ffd84a',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: SANS,
          fontWeight: 900,
          fontSize: 76,
          boxShadow: '0 0 60px #ffd84a88',
          transform: `scale(${interpolate(pVS, [0, 1], [0, 1])}) rotate(${interpolate(pVS, [0, 1], [-90, 0])}deg)`,
        }}
      >
        VS
      </div>
      <div style={{display: 'none'}}>{frame}</div>
    </AbsoluteFill>
  );
};

// =====================================================================
// 5 — LINHA DO TEMPO   destaque = título | elementos = "04 OUT|1º turno"
// =====================================================================
export const CenaLinhaTempo: React.FC<Props> = ({cena, entradas, foto}) => {
  const sp = useSp();
  const frame = useCurrentFrame();
  const els = (cena.elementos ?? []).slice(0, 5);
  const passo = els.length > 4 ? 190 : 215;
  const topo = 420;
  const ys = els.map((_, i) => topo + i * passo);
  const ents = els.map((_, i) => Math.max(10 + i * 14, entradas[i] ?? 0));
  const ativo = ents.filter((e) => frame >= e).length - 1;
  const alvoY = ativo >= 0 ? ys[ativo] : topo;
  const prog = interpolate(frame, [ents[Math.max(ativo, 0)] ?? 0, (ents[Math.max(ativo, 0)] ?? 0) + 14], [0, 1], clamp01);
  const anterior = ativo > 0 ? ys[ativo - 1] : topo;
  const fim = ativo > 0 ? anterior + (alvoY - anterior) * prog : topo;
  const pt = sp(2, 'suave');

  return (
    <AbsoluteFill style={{background: '#0b1220'}}>
      <FundoFoto foto={foto} opacidade={0.55} filtro="saturate(1) brightness(0.88)" />
      <Grade c="rgba(120,160,255,0.06)" />
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 70,
          right: 70,
          textAlign: 'center',
          fontFamily: SERIF,
          fontStyle: 'italic',
          fontSize: cena.destaque.length > 22 ? 70 : 92,
          color: '#f2efe6',
          opacity: pt,
          transform: `translateY(${interpolate(pt, [0, 1], [-30, 0])}px)`,
        }}
      >
        {cena.destaque}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 258,
          top: topo + 65,
          width: 8,
          height: Math.max(0, fim - topo),
          background: 'linear-gradient(#4aa3ff, #4aa3ffaa)',
          borderRadius: 4,
        }}
      />
      {els.map((e, i) => {
        if (frame < ents[i] - 1) return null;
        const Ic = (Lucide as any)[e.icone ?? 'Flag'] ?? (Lucide as any).Flag;
        const [d, t] = e.texto.includes('|') ? e.texto.split('|') : ['', e.texto];
        const p = sp(ents[i], 'mola');
        const atual = i === ativo;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 130,
              top: ys[i],
              display: 'flex',
              alignItems: 'center',
              gap: 56,
              opacity: interpolate(p, [0, 0.4], [0, atual ? 1 : 0.55], clamp01),
              transform: `translateX(${interpolate(p, [0, 1], [-120, 0])}px)`,
            }}
          >
            <div
              style={{
                width: 130,
                height: 130,
                borderRadius: '50%',
                border: `6px solid ${atual ? '#4aa3ff' : '#667'}`,
                background: atual ? '#4aa3ff22' : '#ffffff08',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: atual ? `0 0 ${50 + 20 * Math.sin(frame / 5)}px #4aa3ffaa` : undefined,
                transform: `scale(${interpolate(p, [0, 1], [0.4, 1])})`,
                flexShrink: 0,
              }}
            >
              <Ic size={64} color={atual ? '#4aa3ff' : '#889'} strokeWidth={1.8} />
            </div>
            <div style={{fontFamily: SANS}}>
              {d && <div style={{fontFamily: MONO, fontSize: 32, letterSpacing: 4, color: '#8aa'}}>{d.trim().toUpperCase()}</div>}
              <div style={{fontSize: 62, fontWeight: 800, color: '#fff', lineHeight: 1.1}}>{t.trim()}</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
