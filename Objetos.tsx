import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import * as Lucide from 'lucide-react';
import {FINA, FORTE, SERIFA, TEXTO, clamp, sombraObjeto, useTema} from './Base';

export const Icone: React.FC<{nome: string; size: number; color: string; sw?: number}> = ({nome, size, color, sw = 2}) => {
  const C = (Lucide as any)[nome] ?? (Lucide as any).Circle;
  return <C size={size} color={color} strokeWidth={sw} />;
};

// =====================================================================
// ETIQUETA DE PREÇO (pendura num fio, balança como pêndulo, com brilho)
// =====================================================================
export const Etiqueta: React.FC<{texto: string; sub?: string; x: number; y: number; inicio?: number}> = ({
  texto,
  sub,
  x,
  y,
  inicio = 0,
}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const queda = spring({frame: frame - inicio, fps, config: {damping: 11, stiffness: 110, mass: 0.9}});
  const t = Math.max(0, frame - inicio - 6);
  const balanco = 14 * Math.exp(-t * 0.055) * Math.cos(t * 0.3);
  const brilho = interpolate((frame - inicio) % 120, [0, 40], [-60, 160], clamp);
  return (
    <div
      style={{
        position: 'absolute',
        left: x - 230,
        top: y - 40 - interpolate(queda, [0, 1], [1000, 0]),
        width: 460,
        height: 640,
        transformOrigin: '230px 50px',
        transform: `rotate(${balanco}deg)`,
        filter: `drop-shadow(0 40px 40px ${T.sombra})`,
      }}
    >
      <svg width={460} height={640} viewBox="0 0 460 640" style={{overflow: 'visible'}}>
        <defs>
          <linearGradient id="etq" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={T.acentoClaro} />
            <stop offset="0.35" stopColor={T.acento} />
            <stop offset="1" stopColor={T.acentoEscuro} />
          </linearGradient>
          <linearGradient id="etqBrilho" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#fff" stopOpacity="0" />
            <stop offset="0.5" stopColor="#fff" stopOpacity="0.55" />
            <stop offset="1" stopColor="#fff" stopOpacity="0" />
          </linearGradient>
          <clipPath id="etqForma">
            <path d="M 230 110 L 400 190 Q 430 205 430 240 L 430 560 Q 430 610 380 610 L 80 610 Q 30 610 30 560 L 30 240 Q 30 205 60 190 Z" />
          </clipPath>
        </defs>
        {/* fio */}
        <path d="M 230 -900 L 230 70" stroke={T.tinta} strokeWidth={5} opacity={0.75} />
        <path
          d="M 230 110 L 400 190 Q 430 205 430 240 L 430 560 Q 430 610 380 610 L 80 610 Q 30 610 30 560 L 30 240 Q 30 205 60 190 Z"
          fill="url(#etq)"
        />
        <g clipPath="url(#etqForma)">
          <rect x={brilho * 4 - 200} y={0} width={110} height={700} fill="url(#etqBrilho)" transform="skewX(-18)" />
        </g>
        <circle cx={230} cy={150} r={26} fill={T.bg} />
        <circle cx={230} cy={150} r={26} fill="none" stroke="rgba(0,0,0,0.25)" strokeWidth={4} />
        <path d="M 230 70 C 200 70 200 130 230 130" fill="none" stroke={T.tinta} strokeWidth={5} opacity={0.75} />
        <text x={230} y={400} textAnchor="middle" fontFamily={FORTE} fontSize={texto.length > 4 ? 120 : 150} fill={T.sobreAcento} letterSpacing={-4}>
          {texto}
        </text>
        {sub ? (
          <text x={230} y={490} textAnchor="middle" fontFamily={TEXTO} fontWeight={800} fontSize={42} fill={T.sobreAcento} letterSpacing={6} opacity={0.8}>
            {sub}
          </text>
        ) : null}
      </svg>
    </div>
  );
};

// =====================================================================
// CELULAR (corpo branco/escuro, ilha, tela com cartões de notificação)
// =====================================================================
export const Celular: React.FC<{
  x: number;
  y: number;
  inicio?: number;
  notificacoes: {icone: string; titulo: string; texto: string}[];
  escala?: number;
}> = ({x, y, inicio = 0, notificacoes, escala = 1}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const e = spring({frame: frame - inicio, fps, config: {damping: 15, stiffness: 90, mass: 1}});
  const flutua = Math.sin(frame / 22) * 9;
  const W = 560;
  const H = 1080;
  return (
    <div
      style={{
        position: 'absolute',
        left: x - W / 2,
        top: y - H / 2 + interpolate(e, [0, 1], [900, 0]) + flutua,
        width: W,
        height: H,
        transform: `rotate(${interpolate(e, [0, 1], [10, -3])}deg) scale(${escala})`,
        transformOrigin: '50% 80%',
      }}
    >
      <div
        style={{
          width: W,
          height: H,
          borderRadius: 96,
          background: T.claro ? 'linear-gradient(145deg, #ffffff, #dcdcd8)' : 'linear-gradient(145deg, #3a3a40, #17171a)',
          boxShadow: `${sombraObjeto(T, 1.3)}, inset 0 0 0 6px ${T.claro ? '#cfcfcb' : '#4a4a52'}`,
          padding: 26,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: 72,
            background: T.claro ? '#f6f6f4' : '#0f0f12',
            position: 'relative',
            overflow: 'hidden',
            boxShadow: 'inset 0 0 40px rgba(0,0,0,0.12)',
          }}
        >
          <div style={{position: 'absolute', top: 24, left: '50%', width: 150, height: 40, marginLeft: -75, borderRadius: 24, background: '#0b0b0d'}} />
          <div
            style={{
              position: 'absolute',
              top: 100,
              left: 0,
              right: 0,
              textAlign: 'center',
              fontFamily: FINA,
              fontSize: 120,
              color: T.tinta,
              opacity: 0.9,
            }}
          >
            09:41
          </div>
          {notificacoes.slice(0, 4).map((n, i) => {
            const ini = inicio + 20 + i * 12;
            const s = spring({frame: frame - ini, fps, config: {damping: 13, stiffness: 140, mass: 0.7}});
            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: 26,
                  right: 26,
                  top: 270 + i * 170,
                  height: 150,
                  borderRadius: 38,
                  background: T.cartao,
                  boxShadow: `0 16px 30px ${T.sombra}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 22,
                  padding: '0 24px',
                  opacity: interpolate(s, [0, 0.5], [0, 1], clamp),
                  transform: `translateY(${interpolate(s, [0, 1], [-260, 0])}px) scale(${interpolate(s, [0, 1], [0.9, 1])})`,
                }}
              >
                <div
                  style={{
                    width: 84,
                    height: 84,
                    borderRadius: 24,
                    flexShrink: 0,
                    background: i === 0 ? `linear-gradient(145deg, ${T.acento}, ${T.acentoEscuro})` : T.claro ? 'linear-gradient(145deg,#2a2a2e,#0e0e10)' : '#33333a',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 8px 14px rgba(0,0,0,0.25)',
                  }}
                >
                  <Icone nome={n.icone} size={46} color="#fff" sw={2.2} />
                </div>
                <div style={{minWidth: 0}}>
                  <div style={{fontFamily: TEXTO, fontWeight: 800, fontSize: 36, color: T.cartaoTinta, whiteSpace: 'nowrap'}}>{n.titulo}</div>
                  <div style={{fontFamily: TEXTO, fontSize: 30, color: T.suave, whiteSpace: 'nowrap'}}>{n.texto}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// =====================================================================
// CARTÃO BASE + CARTÃO DE PREÇO (usado também dentro da lupa)
// =====================================================================
export const Cartao: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  inicio?: number;
  children?: React.ReactNode;
  raio?: number;
}> = ({x, y, w, h, inicio = 0, children, raio = 58}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const e = spring({frame: frame - inicio, fps, config: {damping: 15, stiffness: 100, mass: 0.9}});
  return (
    <div
      style={{
        position: 'absolute',
        left: x - w / 2,
        top: y - h / 2,
        width: w,
        height: h,
        borderRadius: raio,
        background: T.cartao,
        boxShadow: sombraObjeto(T, 1.1),
        opacity: interpolate(e, [0, 0.4], [0, 1], clamp),
        transform: `translateY(${interpolate(e, [0, 1], [180, 0])}px) scale(${interpolate(e, [0, 1], [0.86, 1])}) rotate(${interpolate(e, [0, 1], [-4, 0])}deg)`,
        overflow: 'hidden',
      }}
    >
      {children}
    </div>
  );
};

export const ConteudoPreco: React.FC<{preco: string; rotulo: string; riscar: number}> = ({preco, rotulo, riscar}) => {
  const T = useTema();
  return (
    <div style={{padding: '46px 56px'}}>
      <div style={{fontFamily: TEXTO, fontWeight: 800, fontSize: 38, letterSpacing: 4, textTransform: 'uppercase', color: T.suave}}>{rotulo}</div>
      <div style={{position: 'relative', display: 'inline-block', marginTop: 8}}>
        <div style={{fontFamily: FORTE, fontSize: 168, letterSpacing: -6, color: T.cartaoTinta, lineHeight: 1.15}}>{preco}</div>
        <div
          style={{
            position: 'absolute',
            left: -16,
            top: '54%',
            height: 14,
            width: `calc(${riscar * 100}% + 32px)`,
            borderRadius: 8,
            background: T.alerta,
            transform: 'rotate(-4deg)',
            transformOrigin: 'left center',
            boxShadow: '0 4px 14px rgba(226,52,42,0.55)',
          }}
        />
      </div>
    </div>
  );
};

// =====================================================================
// LUPA: lente que amplia o que está embaixo (clone do conteúdo escalado)
// =====================================================================
export const Lupa: React.FC<{
  lx: number;
  ly: number;
  r: number;
  zoom?: number;
  opac?: number;
  children: React.ReactNode; // conteúdo no espaço 1080x1920 (o mesmo que está embaixo)
}> = ({lx, ly, r, zoom = 1.7, opac = 1, children}) => {
  const T = useTema();
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 1920, opacity: opac, pointerEvents: 'none'}}>
      {/* cabo */}
      <div
        style={{
          position: 'absolute',
          left: lx + r * 0.62,
          top: ly + r * 0.62,
          width: 120,
          height: 340,
          borderRadius: 60,
          background: `linear-gradient(90deg, ${T.claro ? '#2a2a2e' : '#d8d8d4'}, ${T.claro ? '#0c0c0e' : '#8d8d89'})`,
          transform: 'rotate(-45deg)',
          transformOrigin: '60px 0',
          boxShadow: '0 30px 40px rgba(0,0,0,0.28)',
        }}
      />
      {/* lente */}
      <div
        style={{
          position: 'absolute',
          left: lx - r,
          top: ly - r,
          width: r * 2,
          height: r * 2,
          borderRadius: '50%',
          overflow: 'hidden',
          background: T.cartao,
          border: `22px solid ${T.claro ? '#1b1b1f' : '#e6e6e2'}`,
          boxShadow: '0 40px 60px rgba(0,0,0,0.3), inset 0 0 40px rgba(0,0,0,0.18)',
          boxSizing: 'border-box',
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: 1080,
            height: 1920,
            transformOrigin: '0 0',
            transform: `translate(${r - 22}px, ${r - 22}px) scale(${zoom}) translate(${-lx}px, ${-ly}px)`,
          }}
        >
          {children}
        </div>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(circle at 28% 24%, rgba(255,255,255,0.55), rgba(255,255,255,0) 38%)',
          }}
        />
      </div>
    </div>
  );
};

// =====================================================================
// TILE DE ÍCONE (3D macio) + label
// =====================================================================
export const TileIcone: React.FC<{icone: string; texto: string; destaque?: boolean; local: number; y: number}> = ({
  icone,
  texto,
  destaque,
  local,
  y,
}) => {
  const T = useTema();
  const {fps} = useVideoConfig();
  const e = spring({frame: local, fps, config: {damping: 10, stiffness: 190, mass: 0.6}});
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: y,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 54,
        transform: `scale(${interpolate(e, [0, 1], [0.55, 1])}) rotate(${interpolate(e, [0, 1], [-14, 0])}deg)`,
        opacity: interpolate(e, [0, 0.35], [0, 1], clamp),
      }}
    >
      <div
        style={{
          width: 520,
          height: 520,
          borderRadius: 140,
          background: destaque
            ? `linear-gradient(150deg, ${T.acentoClaro} 0%, ${T.acento} 45%, ${T.acentoEscuro} 100%)`
            : T.claro
              ? 'linear-gradient(150deg, #ffffff 0%, #e4e4e0 60%, #c6c6c2 100%)'
              : 'linear-gradient(150deg, #44444c, #1d1d21)',
          boxShadow: `${sombraObjeto(T, 1.5)}, inset 0 -14px 24px rgba(0,0,0,0.12), inset 0 10px 18px rgba(255,255,255,0.8)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Icone nome={icone} size={270} color={destaque ? T.sobreAcento : T.cartaoTinta} sw={1.7} />
      </div>
      <div style={{fontFamily: FORTE, fontSize: 84, letterSpacing: -2, textTransform: 'uppercase', color: T.tinta, textAlign: 'center'}}>
        {texto}
      </div>
    </div>
  );
};

// =====================================================================
// BOTÃO (pílula de ação, usada com o cursor)
// =====================================================================
export const Botao: React.FC<{texto: string; x: number; y: number; w?: number; h?: number; apertar?: number; escuro?: boolean}> = ({
  texto,
  x,
  y,
  w = 300,
  h = 110,
  apertar = 1,
  escuro,
}) => {
  const T = useTema();
  return (
    <div
      style={{
        position: 'absolute',
        left: x - w / 2,
        top: y - h / 2,
        width: w,
        height: h,
        borderRadius: h / 2,
        background: escuro ? T.tinta : T.acento,
        color: escuro ? T.bg : T.sobreAcento,
        fontFamily: TEXTO,
        fontWeight: 900,
        fontSize: 44,
        letterSpacing: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: `0 14px 30px ${T.sombra}, inset 0 6px 10px rgba(255,255,255,0.35)`,
        transform: `scale(${apertar})`,
      }}
    >
      {texto}
    </div>
  );
};

export {SERIFA};
