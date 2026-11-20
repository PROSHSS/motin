import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// =====================================================================
// CURSOR: seta que viaja até os alvos e "clica" (toque com onda)
// =====================================================================
export type PontoCursor = {f: number; x: number; y: number; clique?: boolean};

export const Cursor: React.FC<{pontos: PontoCursor[]; cor?: string; sumirApos?: number}> = ({
  pontos,
  cor = '#ffffff',
  sumirApos = 26,
}) => {
  const frame = useCurrentFrame();
  if (pontos.length === 0) return null;
  const primeiro = pontos[0];
  const ultimo = pontos[pontos.length - 1];
  // ponto de partida fora da tela (chega de baixo/direita)
  const chaves = [{f: primeiro.f - 22, x: primeiro.x + 320, y: primeiro.y + 460}, ...pontos];
  let x = chaves[0].x;
  let y = chaves[0].y;
  for (let i = 0; i < chaves.length - 1; i++) {
    const a = chaves[i];
    const b = chaves[i + 1];
    if (frame >= a.f && frame <= b.f) {
      const p = Easing.bezier(0.3, 0.0, 0.2, 1)(interpolate(frame, [a.f, b.f], [0, 1], clamp));
      x = a.x + (b.x - a.x) * p;
      y = a.y + (b.y - a.y) * p;
    } else if (frame > b.f) {
      x = b.x;
      y = b.y;
    }
  }
  if (frame < chaves[0].f) return null;
  const cliques = pontos.filter((p) => p.clique).map((p) => p.f);
  const ultimoClique = cliques.filter((c) => c <= frame).pop();
  const dt = ultimoClique !== undefined ? frame - ultimoClique : 99;
  const escala = dt < 8 ? interpolate(dt, [0, 3, 8], [1, 0.78, 1]) : 1;
  const opac = interpolate(frame, [ultimo.f + sumirApos, ultimo.f + sumirApos + 10], [1, 0], clamp);
  return (
    <AbsoluteFill style={{pointerEvents: 'none', zIndex: 9, opacity: opac}}>
      {cliques.map((c, k) => {
        const d = frame - c;
        if (d < 0 || d > 18) return null;
        const p = pontos.find((q) => q.f === c)!;
        const r = interpolate(d, [0, 18], [10, 90]);
        return (
          <div
            key={k}
            style={{
              position: 'absolute',
              left: p.x - r,
              top: p.y - r,
              width: r * 2,
              height: r * 2,
              borderRadius: '50%',
              border: `5px solid ${cor}`,
              opacity: interpolate(d, [0, 18], [0.85, 0]),
            }}
          />
        );
      })}
      <svg
        width={74}
        height={92}
        viewBox="0 0 24 30"
        style={{
          position: 'absolute',
          left: x - 2,
          top: y - 2,
          transform: `scale(${escala})`,
          transformOrigin: '2px 2px',
          filter: 'drop-shadow(0 6px 8px rgba(0,0,0,0.55))',
        }}
      >
        <path d="M2 2 L2 24 L8 18.5 L12.2 28 L16 26.4 L11.8 17 L20 17 Z" fill={cor} stroke="#111" strokeWidth={1.6} strokeLinejoin="round" />
      </svg>
    </AbsoluteFill>
  );
};

// =====================================================================
// CONFETE: explosão de formas coloridas com gravidade
// =====================================================================
export const Confete: React.FC<{inicio: number; x: number; y: number; cores?: string[]; qtd?: number}> = ({
  inicio,
  x,
  y,
  cores = ['#f7c600', '#e2231a', '#2457e6', '#2fbf6b', '#ffffff', '#ff7a3c'],
  qtd = 34,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = (frame - inicio) / fps;
  if (t < 0 || t > 1.7) return null;
  const rnd = (i: number, k: number) => {
    const v = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453;
    return v - Math.floor(v);
  };
  return (
    <AbsoluteFill style={{pointerEvents: 'none', zIndex: 10}}>
      {Array.from({length: qtd}, (_, i) => {
        const ang = rnd(i, 1) * Math.PI * 2;
        const vel = 380 + rnd(i, 2) * 620;
        const px = x + Math.cos(ang) * vel * t;
        const py = y + Math.sin(ang) * vel * t + 0.5 * 1500 * t * t - 150 * t;
        const tam = 14 + rnd(i, 3) * 22;
        const rot = rnd(i, 4) * 360 + t * (rnd(i, 5) - 0.5) * 900;
        const redondo = rnd(i, 6) > 0.6;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: px,
              top: py,
              width: tam,
              height: redondo ? tam : tam * 0.5,
              borderRadius: redondo ? '50%' : 4,
              background: cores[i % cores.length],
              transform: `rotate(${rot}deg)`,
              opacity: interpolate(t, [0.9, 1.7], [1, 0], clamp),
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// =====================================================================
// TÍTULO COM MÁSCARA: cada palavra sobe de dentro de uma "janela" + brilho passando
// =====================================================================
export const TituloMask: React.FC<{
  texto: string;
  tam: number;
  cor?: string;
  top: number;
  fonte?: string;
  italico?: boolean;
  peso?: number;
  inicio?: number;
  brilho?: boolean;
}> = ({texto, tam, cor = '#f2efe6', top, fonte = "Georgia, 'Times New Roman', serif", italico = true, peso = 400, inicio = 2, brilho = true}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const palavras = texto.split(/\s+/).filter(Boolean);
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: 60,
        right: 60,
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: `0 ${tam * 0.25}px`,
        zIndex: 3,
        textShadow: '0 4px 24px rgba(0,0,0,0.55)',
      }}
    >
      {palavras.map((p, i) => {
        const ini = inicio + i * 4;
        const e = spring({frame: frame - ini, fps, config: {damping: 13, stiffness: 150, mass: 0.7}});
        const passa = interpolate(frame, [ini + 14, ini + 44], [130, -30], clamp);
        return (
          <span key={i} style={{display: 'inline-block', overflow: 'hidden', paddingBottom: tam * 0.18, marginBottom: -tam * 0.18, paddingTop: tam * 0.1, marginTop: -tam * 0.1}}>
            <span
              style={{
                display: 'inline-block',
                fontFamily: fonte,
                fontStyle: italico ? 'italic' : 'normal',
                fontWeight: peso,
                fontSize: tam,
                lineHeight: 1.08,
                transform: `translateY(${interpolate(e, [0, 1], [118, 0])}%) rotate(${interpolate(e, [0, 1], [5, 0])}deg)`,
                transformOrigin: 'left bottom',
                color: brilho ? 'transparent' : cor,
                backgroundImage: brilho
                  ? `linear-gradient(105deg, ${cor} 0%, ${cor} 40%, #ffffff 50%, ${cor} 60%, ${cor} 100%)`
                  : undefined,
                backgroundSize: '300% 100%',
                backgroundPositionX: `${passa}%`,
                WebkitBackgroundClip: brilho ? 'text' : undefined,
                backgroundClip: brilho ? 'text' : undefined,
              }}
            >
              {p}
            </span>
          </span>
        );
      })}
    </div>
  );
};

// =====================================================================
// BARRA DE PROGRESSO EM SEGMENTOS (estilo stories)
// =====================================================================
export const Segmentos: React.FC<{tempos: {inicio: number; fim: number}[]; cor: string}> = ({tempos, cor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const n = tempos.length;
  if (!n) return null;
  const gap = 8;
  const larg = (940 - gap * (n - 1)) / n;
  return (
    <div style={{position: 'absolute', top: 46, left: 70, right: 70, display: 'flex', gap, zIndex: 7}}>
      {tempos.map((tp, i) => {
        const p = interpolate(t, [tp.inicio, tp.fim], [0, 1], clamp);
        const ativo = p > 0 && p < 1;
        return (
          <div
            key={i}
            style={{
              width: larg,
              height: ativo ? 10 : 8,
              marginTop: ativo ? -1 : 0,
              borderRadius: 6,
              background: 'rgba(255,255,255,0.28)',
              boxShadow: '0 1px 6px rgba(0,0,0,0.35)',
              overflow: 'hidden',
            }}
          >
            <div style={{width: `${p * 100}%`, height: '100%', background: cor}} />
          </div>
        );
      })}
    </div>
  );
};

// =====================================================================
// FORMAS FLUTUANTES com profundidade (parallax): cruzes, anéis e quadrados
// =====================================================================
export const Flutuantes: React.FC = () => {
  const frame = useCurrentFrame();
  const rnd = (i: number, k: number) => {
    const v = Math.sin(i * 91.3458 + k * 47.233) * 24634.6345;
    return v - Math.floor(v);
  };
  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', mixBlendMode: 'soft-light'}}>
      {Array.from({length: 12}, (_, i) => {
        const prof = 0.4 + rnd(i, 1) * 1.2; // quanto maior, mais perto
        const x0 = rnd(i, 2) * 1080;
        const y0 = rnd(i, 3) * 1920;
        const x = (x0 + Math.sin(frame / (40 + i * 7) + i) * 40 * prof + frame * 0.35 * prof + 1200) % 1180 - 50;
        const y = (y0 - frame * 0.9 * prof + 4000) % 2020 - 50;
        const tam = 26 + prof * 34;
        const forma = i % 3;
        const rot = frame * (0.5 + rnd(i, 4)) * (i % 2 ? 1 : -1);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: tam,
              height: tam,
              opacity: 0.35,
              transform: `rotate(${rot}deg)`,
              filter: prof < 0.8 ? 'blur(2px)' : undefined,
            }}
          >
            {forma === 0 ? (
              <svg viewBox="0 0 40 40" width={tam} height={tam}>
                <path d="M20 4 V36 M4 20 H36" stroke="#fff" strokeWidth={5} strokeLinecap="round" />
              </svg>
            ) : forma === 1 ? (
              <div style={{width: '100%', height: '100%', borderRadius: '50%', border: '5px solid #fff'}} />
            ) : (
              <div style={{width: '70%', height: '70%', borderRadius: 6, background: '#fff', margin: '15%'}} />
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
