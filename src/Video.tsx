import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

import {percentage} from './data';

type Cena = {narracao: string; tipo: string; destaque: string; imagem?: string};
type Tempo = {cena: number; inicio: number; fim: number};
type Palavra = {palavra: string; inicio: number; fim: number};
export type VideoProps = {
  roteiro: {titulo: string; cenas: Cena[]};
  tempos: Tempo[];
  palavras: Palavra[];
};

// ---------- ESTILO ----------
const BG = '#0a0a0c';
const FG = '#f2efe6';
const MUDO = '#a0a0aa';
const ACENTO = '#c9a24a';
const SERIF = "Georgia, 'Times New Roman', serif";
const MONO = "Consolas, 'Courier New', monospace";

const numero = percentage;

const useEntrada = (atraso = 0) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - atraso, fps, config: {damping: 200}});
};

// ---------- CENAS ----------
const Rotulo: React.FC<{n: number; total: number; tipo: string}> = ({n, total, tipo}) => (
  <div
    style={{
      position: 'absolute',
      top: 90,
      left: 70,
      right: 70,
      display: 'flex',
      justifyContent: 'space-between',
      fontFamily: MONO,
      fontSize: 28,
      letterSpacing: 3,
      color: MUDO,
      textTransform: 'uppercase',
    }}
  >
    <span>
      {String(n).padStart(2, '0')} / {tipo}
    </span>
    <span>
      {n}/{total}
    </span>
  </div>
);

const CenaTexto: React.FC<{destaque: string}> = ({destaque}) => {
  const e = useEntrada();
  const y = interpolate(e, [0, 1], [40, 0]);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: 80}}>
      <div
        style={{
          fontFamily: SERIF,
          fontStyle: 'italic',
          fontSize: destaque.length > 90 ? 58 : destaque.length > 48 ? 76 : destaque.length > 24 ? 92 : 130,
          overflowWrap: 'anywhere',
          lineHeight: 1.1,
          textAlign: 'center',
          color: FG,
          opacity: e,
          transform: `translateY(${y}px)`,
        }}
      >
        {destaque}
      </div>
      <div
        style={{
          marginTop: 50,
          height: 4,
          width: interpolate(e, [0, 1], [0, 260]),
          background: ACENTO,
        }}
      />
    </AbsoluteFill>
  );
};

const CenaBarras: React.FC<{destaque: string}> = ({destaque}) => {
  const e = useEntrada(4);
  const valor = Math.min(numero(destaque) ?? 50, 100);
  const alturaMax = 760;
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div style={{position: 'relative', width: 760, height: alturaMax + 120}}>
        <div
          style={{
            position: 'absolute',
            bottom: alturaMax * 0.5,
            left: 0,
            right: 0,
            borderTop: `3px dashed ${MUDO}`,
            opacity: 0.7,
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 200,
            width: 360,
            height: (alturaMax * valor * e) / 100,
            background: `linear-gradient(0deg, #806020, ${ACENTO})`,
            borderRadius: '18px 18px 0 0',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: (alturaMax * valor * e) / 100 + 24,
            textAlign: 'center',
            fontFamily: SERIF,
            fontWeight: 700,
            fontSize: 100,
            color: FG,
            opacity: e,
          }}
        >
          {destaque}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const CenaHemiciclo: React.FC<{destaque: string}> = ({destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const frac = Math.min((numero(destaque) ?? 50) / 100, 1);
  const linhas = 9;
  const pontos: {x: number; y: number; ang: number}[] = [];
  for (let r = 0; r < linhas; r++) {
    const raio = 120 + r * 42;
    const n = Math.round((Math.PI * raio) / 26);
    for (let i = 0; i < n; i++) {
      const ang = Math.PI * (i / (n - 1));
      pontos.push({x: -Math.cos(ang) * raio, y: -Math.sin(ang) * raio, ang});
    }
  }
  const prog = spring({frame: frame - 3, fps, config: {damping: 200}, durationInFrames: 40});
  const limite = (Math.PI * frac) * prog;
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <svg width={1000} height={540} viewBox="-500 -480 1000 540">
        {pontos.map((p, i) => (
          <rect
            key={i}
            x={p.x - 8}
            y={p.y - 8}
            width={16}
            height={16}
            rx={3}
            fill={p.ang <= limite ? ACENTO : '#2c2c31'}
          />
        ))}
        <text
          x={0}
          y={-40}
          textAnchor="middle"
          fontFamily={SERIF}
          fontWeight={700}
          fontSize={110}
          fill={FG}
        >
          {destaque}
        </text>
      </svg>
    </AbsoluteFill>
  );
};

const NomeTipo: Record<string, string> = {
  texto: 'Contexto',
  barras: 'Números',
  hemiciclo: 'Distribuição',
  imagem: 'Contexto',
};

const RenderCena: React.FC<{cena: Cena; n: number; total: number; duration: number}> = ({cena, n, total, duration}) => {
  const frame = useCurrentFrame();
  const saida = interpolate(frame, [Math.max(0, duration - 6), duration], [1, 0], {
    extrapolateRight: 'clamp',
    extrapolateLeft: 'clamp',
  });
  return (
    <AbsoluteFill style={{opacity: saida}}>
      {cena.tipo === 'imagem' && cena.imagem ? <>
        <Img src={staticFile(cena.imagem)} style={{width: '100%', height: '100%', objectFit: 'cover', position: 'absolute', transform: `scale(${1 + frame * 0.0003})`}} />
        <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(10,10,12,.95), rgba(10,10,12,.35) 60%, rgba(10,10,12,.8))'}} />
      </> : null}
      <Rotulo n={n} total={total} tipo={NomeTipo[cena.tipo] ?? 'Cena'} />
      {cena.tipo === 'barras' ? (
        <CenaBarras destaque={cena.destaque} />
      ) : cena.tipo === 'hemiciclo' ? (
        <CenaHemiciclo destaque={cena.destaque} />
      ) : (
        <CenaTexto destaque={cena.destaque} />
      )}
    </AbsoluteFill>
  );
};

// ---------- LEGENDA PALAVRA POR PALAVRA ----------
const Legenda: React.FC<{palavras: Palavra[]}> = ({palavras}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const POR_LINHA = 4;
  if (!palavras.length || t < palavras[0].inicio || t >= palavras[palavras.length - 1].fim) return null;

  // índice da palavra atual
  let atual = palavras.findIndex((p) => t >= p.inicio && t < p.fim);
  if (atual < 0) {
    const passadas = palavras.filter((p) => p.fim <= t).length;
    atual = Math.max(0, passadas - 1);
    if (t - palavras[atual].fim > 0.35) return null;
  }
  const grupo = Math.floor(atual / POR_LINHA);
  const linha = palavras.slice(grupo * POR_LINHA, grupo * POR_LINHA + POR_LINHA);

  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        right: 60,
        bottom: 260,
        padding: '24px 30px',
        borderRadius: 24,
        background: 'rgba(10,10,12,.85)',
        textShadow: '0 2px 8px #000',
        textAlign: 'center',
        fontFamily: "'Segoe UI', Arial, sans-serif",
        fontWeight: 700,
        fontSize: 66,
        lineHeight: 1.2,
      }}
    >
      {linha.map((p, i) => {
        const idx = grupo * POR_LINHA + i;
        const dita = t >= p.inicio;
        return (
          <span
            key={idx}
            style={{
              color: idx === atual && t < p.fim ? ACENTO : dita ? FG : MUDO,
              overflowWrap: 'anywhere',
              maxWidth: '100%',
              marginRight: 18,
              display: 'inline-block',
            }}
          >
            {p.palavra}
          </span>
        );
      })}
    </div>
  );
};

// ---------- VÍDEO ----------
export const Video: React.FC<VideoProps> = ({roteiro, tempos, palavras}) => {
  const {fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const total = roteiro.cenas.length;

  // texto certo do roteiro com o tempo do Whisper (se a contagem bater)
  const textoRoteiro = roteiro.cenas
    .map((c) => c.narracao)
    .join(' ')
    .split(/\s+/)
    .filter(Boolean);
  const palavrasFinais =
    textoRoteiro.length === palavras.length
      ? palavras.map((p, i) => ({...p, palavra: textoRoteiro[i]}))
      : palavras;

  return (
    <AbsoluteFill style={{backgroundColor: BG, backgroundImage: 'radial-gradient(ellipse at 50% 35%, #24202a 0%, #0a0a0c 75%)'}}>
      <Audio src={staticFile('narracao.wav')} />
      {roteiro.cenas.map((cena, i) => {
        const t = tempos[i];
        if (!t) return null;
        const from = Math.round(t.inicio * fps);
        const dur = Math.max(1, Math.round(t.fim * fps) - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            <RenderCena cena={cena} n={i + 1} total={total} duration={dur} />
          </Sequence>
        );
      })}
      <Legenda palavras={palavrasFinais} />
      <div
        style={{
          position: 'absolute',
          bottom: 90,
          left: 70,
          right: 70,
          fontFamily: MONO,
          fontSize: 24,
          color: MUDO,
          letterSpacing: 2,
        }}
      >
        {roteiro.titulo}
      </div>
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          height: 6,
          width: `${Math.min(100, (frame / (tempos.length ? tempos[tempos.length - 1].fim * fps : 1)) * 100)}%`,
          background: ACENTO,
        }}
      />
    </AbsoluteFill>
  );
};
