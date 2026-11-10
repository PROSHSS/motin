import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Elemento} from './CenasNovas';
import {TituloMask} from './Efeitos';

// Cenas inspiradas em motion graphics de TikTok: fundos de cor chapada, tipografia mista,
// rabiscos desenhados à mão, caixas marca-texto e painéis estilo "bento".

export type CenaEstilo = {
  narracao: string;
  tipo: string;
  destaque: string;
  imagem?: string;
  elementos?: Elemento[];
};
type Props = {cena: CenaEstilo; entradas: number[]; n: number};

const SANS = "'Segoe UI', Arial, sans-serif";
const SERIF = "Georgia, 'Times New Roman', serif";
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// ---------- paleta de fundos chapados (alterna por cena) ----------
export const FUNDOS_FRASE = [
  {bg: '#f7c600', fg: '#17120a', ac: '#c4232b', claro: true},
  {bg: '#e2231a', fg: '#ffffff', ac: '#ffd23c', claro: false},
  {bg: '#fdd5a6', fg: '#1a1210', ac: '#e2231a', claro: true},
  {bg: '#0e0e10', fg: '#f2efe6', ac: '#f7a21b', claro: false},
  {bg: '#2457e6', fg: '#ffffff', ac: '#ffe14a', claro: false},
];
export const fundoDaCena = (n: number) => FUNDOS_FRASE[(n - 1) % FUNDOS_FRASE.length];

const norm = (t: string) =>
  t
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]/g, '');

const numeroDe = (t: string): number => {
  const m = t.replace(/\./g, '').match(/(\d+(?:,\d+)?)/);
  return m ? parseFloat(m[1].replace(',', '.')) : 0;
};

const comNumero = (original: string, atual: number, casas: number) =>
  original.replace(
    /\d[\d.]*(?:,\d+)?/,
    atual.toLocaleString('pt-BR', {minimumFractionDigits: casas, maximumFractionDigits: casas}),
  );

// ---------- decoração: estrela girando nos cantos + anéis concêntricos ----------
const Estrela: React.FC<{cor: string; tam: number; pontas?: number}> = ({cor, tam, pontas = 12}) => {
  const pts: string[] = [];
  for (let i = 0; i < pontas * 2; i++) {
    const r = i % 2 === 0 ? 50 : 30;
    const a = (Math.PI * i) / pontas;
    pts.push(`${50 + r * Math.cos(a)},${50 + r * Math.sin(a)}`);
  }
  return (
    <svg width={tam} height={tam} viewBox="0 0 100 100">
      <polygon points={pts.join(' ')} fill={cor} />
    </svg>
  );
};

export const Decor: React.FC<{cor: string; aneis?: boolean}> = ({cor, aneis = true}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: -150, top: -150, transform: `rotate(${frame * 1.2}deg)`, opacity: 0.35}}>
        <Estrela cor={cor} tam={420} />
      </div>
      <div style={{position: 'absolute', right: -170, bottom: -170, transform: `rotate(${-frame * 0.9}deg)`, opacity: 0.35}}>
        <Estrela cor={cor} tam={480} pontas={9} />
      </div>
      {aneis
        ? [0, 1, 2].map((k) => {
            const f = (frame + k * 22) % 66;
            const r = interpolate(f, [0, 66], [200, 700]);
            return (
              <div
                key={k}
                style={{
                  position: 'absolute',
                  left: 540 - r,
                  top: 960 - r,
                  width: r * 2,
                  height: r * 2,
                  borderRadius: '50%',
                  border: `4px solid ${cor}`,
                  opacity: interpolate(f, [0, 66], [0.28, 0]),
                }}
              />
            );
          })
        : null}
    </AbsoluteFill>
  );
};

// =====================================================================
// FRASE: tipografia mista, palavra-chave com rabisco/caixa desenhado
//   destaque = a frase (até 10 palavras)
//   elementos[0].texto = palavra-chave (da frase) | gatilho = quando desenhar
//   elementos[1].texto = estilo: caixa | circulo | sublinhado | x
// =====================================================================
export const CenaFrase: React.FC<Props> = ({cena, entradas, n}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const f = fundoDaCena(n);
  const palavras = cena.destaque.split(/\s+/).filter(Boolean);
  const chave = norm(cena.elementos?.[0]?.texto ?? '');
  const estilo = norm(cena.elementos?.[1]?.texto ?? 'caixa') || 'caixa';
  let iChave = palavras.findIndex((p) => chave && norm(p).includes(chave));
  if (iChave < 0) iChave = palavras.reduce((m, p, i) => (p.length > palavras[m].length ? i : m), 0);
  const tChave = Math.max(8 + palavras.length * 5, entradas[0] ?? 0);
  const prog = interpolate(frame, [tChave, tChave + 16], [0, 1], clamp);
  const textoCaixa = f.ac === '#ffd23c' || f.ac === '#f7a21b' || f.ac === '#ffe14a' ? '#17120a' : '#fff';

  const estiloPalavra = (i: number) => {
    if (i === iChave) {
      const tam = Math.min(190, Math.floor(900 / Math.max(1, palavras[i].length * 0.6)));
      return {size: tam, weight: 900, family: SANS, italic: false, spacing: -4};
    }
    const v = i % 4;
    if (v === 0) return {size: 88, weight: 500, family: SANS, italic: false, spacing: 0};
    if (v === 1) return {size: 112, weight: 800, family: SANS, italic: false, spacing: -2};
    if (v === 2) return {size: 92, weight: 400, family: SERIF, italic: true, spacing: 0};
    return {size: 74, weight: 700, family: SANS, italic: false, spacing: 2};
  };

  return (
    <AbsoluteFill style={{background: f.bg}}>
      <Decor cor={f.ac} />
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'row',
          flexWrap: 'wrap',
          alignContent: 'center',
          gap: '10px 26px',
          padding: '0 80px',
          transform: `scale(${interpolate(frame, [0, 150], [1, 1.05], clamp)})`,
        }}
      >
        {palavras.map((p, i) => {
          const e = spring({frame: frame - (6 + i * 5), fps, config: {damping: 13, stiffness: 150, mass: 0.7}});
          const es = estiloPalavra(i);
          const eChave = i === iChave;
          const dir = i % 3;
          const tx = dir === 1 ? interpolate(e, [0, 1], [-180, 0]) : dir === 2 ? interpolate(e, [0, 1], [180, 0]) : 0;
          const ty = dir === 0 ? interpolate(e, [0, 1], [120, 0]) : 0;
          return (
            <span
              key={i}
              style={{
                position: 'relative',
                display: 'inline-block',
                fontFamily: es.family,
                fontWeight: es.weight,
                fontStyle: es.italic ? 'italic' : 'normal',
                fontSize: es.size,
                letterSpacing: es.spacing,
                lineHeight: 1.05,
                color: eChave && estilo === 'caixa' && prog > 0.5 ? textoCaixa : eChave ? f.fg : f.fg,
                opacity: interpolate(e, [0, 0.5], [0, 1], clamp),
                transform: `translate(${tx}px, ${ty}px) scale(${interpolate(e, [0, 1], [0.6, 1])}) rotate(${eChave ? -2 : 0}deg)`,
                padding: eChave ? '0 22px' : 0,
              }}
            >
              {eChave && estilo === 'caixa' ? (
                <span
                  style={{
                    position: 'absolute',
                    inset: '6px 0 4px 0',
                    background: f.ac,
                    borderRadius: 14,
                    transform: `scaleX(${prog})`,
                    transformOrigin: 'left center',
                    zIndex: -1,
                  }}
                />
              ) : null}
              {p}
              {eChave && estilo !== 'caixa' ? (
                <svg
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                  style={{position: 'absolute', left: -14, top: -10, width: 'calc(100% + 28px)', height: 'calc(100% + 24px)', overflow: 'visible'}}
                >
                  {estilo.startsWith('circ') ? (
                    <path
                      d="M 8 52 C 6 14, 60 4, 92 22 C 108 40, 82 92, 40 90 C 4 88, -2 40, 30 14"
                      fill="none"
                      stroke={f.ac}
                      strokeWidth={5}
                      strokeLinecap="round"
                      vectorEffect="non-scaling-stroke"
                      pathLength={1}
                      strokeDasharray="1"
                      strokeDashoffset={1 - prog}
                      style={{strokeWidth: 9}}
                    />
                  ) : estilo === 'x' ? (
                    <>
                      <path d="M 4 10 L 96 92" stroke={f.ac} strokeLinecap="round" vectorEffect="non-scaling-stroke" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - Math.min(1, prog * 2)} style={{strokeWidth: 12}} />
                      <path d="M 96 10 L 4 92" stroke={f.ac} strokeLinecap="round" vectorEffect="non-scaling-stroke" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - Math.max(0, prog * 2 - 1)} style={{strokeWidth: 12}} />
                    </>
                  ) : (
                    <path
                      d="M 0 94 C 20 84, 30 104, 50 92 S 80 84, 100 94"
                      fill="none"
                      stroke={f.ac}
                      strokeLinecap="round"
                      vectorEffect="non-scaling-stroke"
                      pathLength={1}
                      strokeDasharray="1"
                      strokeDashoffset={1 - prog}
                      style={{strokeWidth: 11}}
                    />
                  )}
                </svg>
              ) : null}
            </span>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// =====================================================================
// LISTA EM CAIXAS: palavras empilhadas, cada uma numa tarja marca-texto
//   destaque = título curto (opcional) | elementos = 2 a 4 palavras/expressões curtas
// =====================================================================
export const CenaListaCaixas: React.FC<Props> = ({cena, entradas, n}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const f = fundoDaCena(n);
  const itens = (cena.elementos ?? []).slice(0, 4);
  const textoCaixa = f.ac === '#ffd23c' || f.ac === '#f7a21b' || f.ac === '#ffe14a' ? '#17120a' : '#fff';
  const ents: number[] = [];
  itens.forEach((_, i) => ents.push(Math.max(i === 0 ? 16 : ents[i - 1] + 12, entradas[i] ?? 0)));
  const tit = spring({frame: frame - 2, fps, config: {damping: 18, stiffness: 100, mass: 0.8}});
  const alt = 190;
  const topo = 960 - (itens.length * alt) / 2 + 40;

  return (
    <AbsoluteFill style={{background: f.bg}}>
      <Decor cor={f.ac} aneis={false} />
      <TituloMask texto={cena.destaque} tam={76} top={230} cor={f.fg} fonte={SANS} italico={false} peso={800} brilho={false} />
      {itens.map((el, i) => {
        const e = spring({frame: frame - ents[i], fps, config: {damping: 12, stiffness: 150, mass: 0.7}});
        const marcado = i % 2 === 0;
        const dir = i % 2 === 0 ? -1 : 1;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: topo + i * alt,
              display: 'flex',
              justifyContent: 'center',
              opacity: interpolate(e, [0, 0.4], [0, 1], clamp),
              transform: `translateX(${interpolate(e, [0, 1], [dir * 500, 0])}px) rotate(${(i % 2 === 0 ? -2.2 : 1.8) * e}deg)`,
            }}
          >
            <div
              style={{
                padding: '14px 44px 22px',
                borderRadius: 18,
                background: marcado ? f.ac : f.claro ? '#fff' : f.fg,
                color: marcado ? textoCaixa : f.claro ? '#17120a' : f.bg,
                fontFamily: SANS,
                fontWeight: 900,
                fontSize: el.texto.length > 14 ? 84 : 108,
                lineHeight: 1.05,
                letterSpacing: -2,
                boxShadow: '0 10px 0 rgba(0,0,0,0.18)',
              }}
            >
              {el.texto}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =====================================================================
// PAINEL "bento": cartões brancos/pretos com mini-widgets que se encaixam
//   destaque = título | elementos = 3 a 4 itens "Rótulo|valor" (ex: "Usuários|87%")
// =====================================================================
const Cartao: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  escuro: boolean;
  ini: number;
  i: number;
  children: React.ReactNode;
}> = ({x, y, w, h, escuro, ini, i, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const e = spring({frame: frame - ini, fps, config: {damping: 13, stiffness: 110, mass: 0.9}});
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: w,
        height: h,
        borderRadius: 54,
        background: escuro ? '#0f0f11' : '#ffffff',
        boxShadow: '0 30px 60px rgba(0,0,0,0.22), 0 6px 14px rgba(0,0,0,0.12)',
        padding: 44,
        overflow: 'hidden',
        opacity: interpolate(e, [0, 0.35], [0, 1], clamp),
        transform: `translateY(${interpolate(e, [0, 1], [220, 0])}px) scale(${interpolate(e, [0, 1], [0.7, 1])}) rotate(${interpolate(e, [0, 1], [i % 2 ? 6 : -6, 0])}deg)`,
      }}
    >
      {children}
    </div>
  );
};

export const CenaPainel: React.FC<Props> = ({cena, entradas}) => {
  const frame = useCurrentFrame();
  const itens = (cena.elementos ?? []).slice(0, 4).map((el) => {
    const [a, ...b] = el.texto.split('|');
    const texto = (b.join('|') || '').trim();
    const valor = numeroDe(texto || a);
    const casas = (texto.match(/,(\d+)/)?.[1] ?? '').length;
    return {rotulo: b.length ? a.trim() : '', texto: texto || a.trim(), valor, casas};
  });
  const max = Math.max(1, ...itens.map((i) => i.valor));
  const pct = (v: number, texto: string) => Math.min(100, texto.includes('%') ? v : (v / max) * 100);
  const ents: number[] = [];
  itens.forEach((_, i) => ents.push(Math.max(i === 0 ? 14 : ents[i - 1] + 12, entradas[i] ?? 0)));
  const tit = interpolate(frame, [0, 14], [0, 1], clamp);
  const deriva = interpolate(frame, [0, 180], [1, 1.07], clamp);
  const cont = (i: number, dur = 30) => interpolate(frame, [ents[i] + 6, ents[i] + 6 + dur], [0, 1], clamp);

  const L = 90;
  const W = 900;
  const G = 36;
  const meio = (W - G) / 2;
  const layout = [
    {x: L, y: 440, w: W, h: 390},
    {x: L, y: 440 + 390 + G, w: meio, h: 430},
    {x: L + meio + G, y: 440 + 390 + G, w: meio, h: 430},
    {x: L, y: 440 + 390 + G + 430 + G, w: W, h: 300},
  ];
  const escuros = [false, true, false, true];

  return (
    <AbsoluteFill style={{background: 'linear-gradient(160deg, #e6e7ea, #c9cbd0)'}}>
      <TituloMask texto={cena.destaque} tam={76} top={210} cor="#16161a" fonte={SANS} italico={false} peso={800} brilho={false} />
      <AbsoluteFill style={{transform: `scale(${deriva})`, transformOrigin: '50% 40%'}}>
        {itens.map((it, i) => {
          const L_ = layout[i];
          const c = cont(i);
          const verde = '#b4e11f';
          const cor = escuros[i];
          const txt = comNumero(it.texto, it.valor * c, it.casas);
          return (
            <Cartao key={i} {...L_} escuro={cor} ini={ents[i]} i={i}>
              <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 38, color: cor ? '#9a9aa2' : '#7a7a82', marginBottom: 6}}>
                {it.rotulo}
              </div>
              {i === 0 ? (
                <div style={{fontFamily: SANS, fontWeight: 900, fontSize: it.texto.length > 6 ? 150 : 210, lineHeight: 1, color: '#16161a', letterSpacing: -6}}>
                  {txt}
                </div>
              ) : i === 1 ? (
                <>
                  <div style={{fontFamily: SANS, fontWeight: 900, fontSize: 120, color: '#fff', letterSpacing: -4, marginTop: 20}}>{txt}</div>
                  <div style={{marginTop: 38, height: 34, borderRadius: 17, background: '#2a2a2f', overflow: 'hidden'}}>
                    <div style={{width: `${pct(it.valor, it.texto) * c}%`, height: '100%', background: verde, borderRadius: 17}} />
                  </div>
                </>
              ) : i === 2 ? (
                <div style={{display: 'flex', justifyContent: 'center', marginTop: 10}}>
                  <svg width={250} height={250} viewBox="0 0 250 250">
                    <circle cx={125} cy={125} r={100} fill="none" stroke="#ececf0" strokeWidth={30} />
                    <circle
                      cx={125}
                      cy={125}
                      r={100}
                      fill="none"
                      stroke="#ff6a2b"
                      strokeWidth={30}
                      strokeLinecap="round"
                      transform="rotate(-90 125 125)"
                      strokeDasharray={`${(2 * Math.PI * 100 * pct(it.valor, it.texto) * c) / 100} 1000`}
                    />
                    <text x={125} y={146} textAnchor="middle" fontFamily={SANS} fontWeight={900} fontSize={62} fill="#16161a">
                      {txt}
                    </text>
                  </svg>
                </div>
              ) : (
                <div style={{display: 'flex', alignItems: 'flex-end', gap: 26, height: 190, marginTop: 14}}>
                  {[0.45, 0.7, 0.55, 0.9, 1].map((h, k) => (
                    <div
                      key={k}
                      style={{
                        flex: 1,
                        height: `${h * (0.35 + 0.65 * (pct(it.valor, it.texto) / 100)) * 100 * c}%`,
                        background: k === 4 ? verde : '#3a3a40',
                        borderRadius: 14,
                      }}
                    />
                  ))}
                  <div style={{position: 'absolute', right: 56, top: 40, fontFamily: SANS, fontWeight: 900, fontSize: 84, color: '#fff'}}>{txt}</div>
                </div>
              )}
            </Cartao>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
