import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import * as Lucide from 'lucide-react';
import {FundoFoto, Elemento} from './CenasNovas';
import {Cursor, Confete, TituloMask} from './Efeitos';

export type CenaExtra = {
  narracao: string;
  tipo: string;
  destaque: string;
  imagem?: string;
  elementos?: Elemento[];
};
type Props = {cena: CenaExtra; entradas: number[]; titulo: string; foto?: string; cor: string};

const SANS = "'Segoe UI', Arial, sans-serif";
const SERIF = "Georgia, 'Times New Roman', serif";
const FG = '#f2efe6';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const useMola = (inicio: number, forte = false) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({
    frame: frame - inicio,
    fps,
    config: forte ? {damping: 9, stiffness: 180, mass: 0.6} : {damping: 18, stiffness: 100, mass: 0.8},
  });
};

const FundoClaro: React.FC<{foto?: string; escuro?: number}> = ({foto, escuro = 0.45}) => (
  <>
    <AbsoluteFill style={{background: '#0a0a0c'}} />
    <FundoFoto foto={foto} opacidade={0.6} filtro="brightness(0.9)" />
    <AbsoluteFill
      style={{
        background: `linear-gradient(to bottom, rgba(10,10,12,${escuro}), rgba(10,10,12,${escuro * 0.5}) 50%, rgba(10,10,12,${escuro + 0.1}))`,
      }}
    />
  </>
);

// =====================================================================
// CITAÇÃO: frase entre aspas revelada palavra por palavra + fonte
// =====================================================================
export const CenaCitacao: React.FC<Props> = ({cena, entradas, foto, cor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const palavras = cena.destaque.split(/\s+/).filter(Boolean);
  const aspas = useMola(0, true);
  const fonte = cena.elementos?.[0]?.texto ?? '';
  const iniFonte = Math.max(30, entradas[0] ?? 0, 10 + palavras.length * 4);
  const eFonte = interpolate(frame, [iniFonte, iniFonte + 14], [0, 1], clamp);
  const tam = palavras.length > 10 ? 70 : palavras.length > 6 ? 84 : 100;

  return (
    <AbsoluteFill>
      <FundoClaro foto={foto} escuro={0.5} />
      <AbsoluteFill
        style={{background: `radial-gradient(circle at 50% 40%, ${cor}2e 0%, transparent 60%)`}}
      />
      <div
        style={{
          position: 'absolute',
          left: 70,
          top: 300,
          fontFamily: SERIF,
          fontWeight: 800,
          fontSize: 420,
          lineHeight: 1,
          color: cor,
          opacity: 0.9,
          transform: `scale(${interpolate(aspas, [0, 1], [0.3, 1])}) rotate(${interpolate(aspas, [0, 1], [-20, 0])}deg)`,
          transformOrigin: 'left top',
          textShadow: `0 0 60px ${cor}88`,
        }}
      >
        “
      </div>
      <div
        style={{
          position: 'absolute',
          left: 90,
          right: 90,
          top: 640,
          fontFamily: SERIF,
          fontStyle: 'italic',
          fontSize: tam,
          lineHeight: 1.18,
          color: FG,
          textShadow: '0 4px 28px rgba(0,0,0,0.8)',
        }}
      >
        {palavras.map((p, i) => {
          const e = spring({frame: frame - (10 + i * 4), fps, config: {damping: 16, stiffness: 140, mass: 0.7}});
          return (
            <span
              key={i}
              style={{
                display: 'inline-block',
                marginRight: 22,
                opacity: interpolate(e, [0, 0.6], [0, 1], clamp),
                transform: `translateY(${interpolate(e, [0, 1], [34, 0])}px)`,
                filter: `blur(${interpolate(e, [0, 1], [8, 0])}px)`,
              }}
            >
              {p}
            </span>
          );
        })}
      </div>
      {fonte ? (
        <div
          style={{
            position: 'absolute',
            left: 90,
            right: 90,
            top: 1290,
            opacity: eFonte,
            transform: `translateX(${interpolate(eFonte, [0, 1], [-40, 0])}px)`,
          }}
        >
          <div style={{width: interpolate(eFonte, [0, 1], [0, 140]), height: 6, background: cor, marginBottom: 22}} />
          <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 48, color: cor, letterSpacing: 1}}>— {fonte}</div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

// =====================================================================
// CHECKLIST: itens com caixinha que se marca (✓ verde) ou cruz (✗ vermelha com "!")
// =====================================================================
export const CenaChecklist: React.FC<Props> = ({cena, entradas, foto, cor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const itens = (cena.elementos ?? []).slice(0, 5);
  const topo = 520;
  const alt = Math.min(210, 1000 / Math.max(1, itens.length));
  const ents: number[] = [];
  itens.forEach((_, i) => ents.push(Math.max(i === 0 ? 14 : ents[i - 1] + 12, entradas[i] ?? 0)));

  return (
    <AbsoluteFill>
      <FundoClaro foto={foto} escuro={0.5} />
      <TituloMask texto={cena.destaque} tam={cena.destaque.length > 22 ? 72 : 94} top={190} />
      {itens.map((el, i) => {
        const nao = el.texto.trim().startsWith('!');
        const texto = el.texto.replace(/^[!~]\s*/, '');
        const cc = nao ? '#e2574c' : '#5ccf85';
        const e = spring({frame: frame - ents[i], fps, config: {damping: 14, stiffness: 120, mass: 0.8}});
        const traco = interpolate(frame, [ents[i] + 6, ents[i] + 20], [0, 1], clamp);
        const y = topo + i * alt;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 80,
              right: 80,
              top: y,
              height: alt - 24,
              display: 'flex',
              alignItems: 'center',
              gap: 36,
              padding: '0 36px',
              borderRadius: 28,
              background: 'rgba(10,10,12,0.55)',
              border: `3px solid ${cc}66`,
              opacity: interpolate(e, [0, 0.4], [0, 1], clamp),
              transform: `translateX(${interpolate(e, [0, 1], [-140, 0])}px)`,
              boxShadow: `0 10px 40px rgba(0,0,0,0.4), 0 0 40px ${cc}22`,
            }}
          >
            <svg width={96} height={96} viewBox="0 0 96 96" style={{flexShrink: 0}}>
              <rect x={6} y={6} width={84} height={84} rx={20} fill={`${cc}22`} stroke={cc} strokeWidth={6} />
              {nao ? (
                <>
                  <path d="M 30 30 L 66 66" stroke={cc} strokeWidth={10} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - Math.min(1, traco * 2)} />
                  <path d="M 66 30 L 30 66" stroke={cc} strokeWidth={10} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - Math.max(0, traco * 2 - 1)} />
                </>
              ) : (
                <path d="M 24 50 L 42 68 L 74 30" fill="none" stroke={cc} strokeWidth={11} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - traco} />
              )}
            </svg>
            <div style={{fontFamily: SANS, fontWeight: 700, fontSize: texto.length > 34 ? 46 : 54, lineHeight: 1.12, color: FG}}>
              {texto}
            </div>
          </div>
        );
      })}
      <Cursor
        pontos={itens.map((_, i) => ({
          f: ents[i] + 2,
          x: 176,
          y: topo + i * alt + (alt - 24) / 2 + 6,
          clique: true,
        }))}
      />
      {itens.length ? <Confete inicio={ents[itens.length - 1] + 22} x={540} y={topo + itens.length * alt} qtd={24} /> : null}
    </AbsoluteFill>
  );
};

// =====================================================================
// ALERTA: faixas de perigo, triângulo pulsando, texto que treme e pisca
// =====================================================================
export const CenaAlerta: React.FC<Props> = ({cena, entradas, foto}) => {
  const frame = useCurrentFrame();
  const vermelho = '#e2342a';
  const e = useMola(2, true);
  const piscar = frame < 40 ? (Math.floor(frame / 4) % 2 === 0 ? 1 : 0.55) : 1;
  const tremor = frame < 22 ? Math.sin(frame * 3.1) * (22 - frame) * 0.9 : 0;
  const sub = cena.elementos?.[0]?.texto ?? '';
  const tamTitulo = cena.destaque.length > 16 ? 76 : cena.destaque.length > 10 ? 92 : 128;
  const linhasTitulo = Math.ceil((cena.destaque.length * tamTitulo * 0.68) / 980) || 1;
  const topoSub = 700 + linhasTitulo * tamTitulo * 1.05 + 24;
  const linhas = (cena.elementos ?? []).slice(1, 4);
  const faixa = (pos: 'top' | 'bottom') => (
    <div
      style={{
        position: 'absolute',
        left: -200,
        right: -200,
        [pos]: pos === 'top' ? 150 : 330,
        height: 56,
        transform: 'rotate(-3deg)',
        backgroundImage: `repeating-linear-gradient(45deg, ${vermelho} 0 40px, #14080a 40px 80px)`,
        backgroundPositionX: (pos === 'top' ? 1 : -1) * frame * 3,
        opacity: interpolate(e, [0, 1], [0, 1]),
        boxShadow: `0 0 40px ${vermelho}88`,
      }}
    />
  );
  return (
    <AbsoluteFill>
      <FundoClaro foto={foto} escuro={0.62} />
      <AbsoluteFill
        style={{background: `radial-gradient(circle at 50% 42%, ${vermelho}44 0%, transparent 62%)`, opacity: 0.7 + 0.3 * Math.sin(frame / 5)}}
      />
      {faixa('top')}
      {faixa('bottom')}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 400,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${interpolate(e, [0, 1], [0.2, 1]) * (1 + 0.05 * Math.sin(frame / 4))})`,
        }}
      >
        <Lucide.TriangleAlert size={250} color={vermelho} strokeWidth={1.6} style={{filter: `drop-shadow(0 0 40px ${vermelho})`}} />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 50,
          right: 50,
          top: 700,
          textAlign: 'center',
          fontFamily: SANS,
          fontWeight: 900,
          fontSize: tamTitulo,
          lineHeight: 1,
          letterSpacing: 2,
          textTransform: 'uppercase',
          color: '#fff',
          opacity: piscar,
          transform: `translateX(${tremor}px)`,
          textShadow: `0 0 30px ${vermelho}, 0 6px 30px rgba(0,0,0,0.8)`,
        }}
      >
        {cena.destaque}
      </div>
      {sub ? (
        <div
          style={{
            position: 'absolute',
            left: 90,
            right: 90,
            top: topoSub,
            textAlign: 'center',
            fontFamily: SANS,
            fontWeight: 700,
            fontSize: 58,
            lineHeight: 1.12,
            color: '#ffd6d2',
            opacity: interpolate(frame, [18, 30], [0, 1], clamp),
          }}
        >
          {sub}
        </div>
      ) : null}
      {linhas.map((l, i) => {
        const ini = Math.max(34 + i * 14, entradas[i + 1] ?? 0);
        const o = interpolate(frame, [ini, ini + 10], [0, 1], clamp);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 120,
              right: 120,
              top: topoSub + 150 + i * 105,
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              opacity: o,
              transform: `translateX(${interpolate(o, [0, 1], [60, 0])}px)`,
              fontFamily: SANS,
              fontWeight: 700,
              fontSize: 48,
              color: FG,
            }}
          >
            <div style={{width: 18, height: 18, borderRadius: 9, background: vermelho, boxShadow: `0 0 16px ${vermelho}`, flexShrink: 0}} />
            {l.texto}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =====================================================================
// EXTRAS GLOBAIS: partículas de poeira e chamada final
// =====================================================================
export const Particulas: React.FC = () => {
  const frame = useCurrentFrame();
  const bolhas = Array.from({length: 34}, (_, i) => {
    const a = (i * 9301 + 49297) % 233280;
    const x = (a / 233280) * 1080;
    const v = 0.25 + ((i * 37) % 10) / 14;
    const tam = 3 + ((i * 53) % 7);
    const y = (1920 + 100 - ((frame * v * 2.2 + (i * 211) % 1920) % 2020));
    const bal = Math.sin(frame / 25 + i) * 18;
    return {x: x + bal, y, tam, o: 0.12 + ((i * 17) % 10) / 70};
  });
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'screen'}}>
      {bolhas.map((b, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: b.x,
            top: b.y,
            width: b.tam,
            height: b.tam,
            borderRadius: '50%',
            background: '#fff8e0',
            opacity: b.o,
            filter: 'blur(1px)',
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

export const ChamadaFinal: React.FC<{texto: string; marca?: string; inicio: number}> = ({texto, marca, inicio}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const e = spring({frame: frame - inicio, fps, config: {damping: 13, stiffness: 120, mass: 0.8}});
  if (frame < inicio) return null;
  const topo = 1290;
  const tClique = inicio + 34;
  const seguindo = frame >= tClique + 2;
  const apertado = interpolate(frame, [tClique, tClique + 3, tClique + 9], [1, 0.93, 1], clamp);
  const pulo = seguindo ? 1 + 0.1 * Math.exp(-(frame - tClique) * 0.25) * Math.cos((frame - tClique) * 0.7) : 1 + 0.02 * Math.sin((frame - inicio) / 6);
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: topo,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 8,
          opacity: interpolate(e, [0, 0.5], [0, 1], clamp),
          transform: `translateY(${interpolate(e, [0, 1], [80, 0])}px) scale(${pulo * apertado})`,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 22,
            padding: '26px 52px',
            whiteSpace: 'nowrap',
            borderRadius: 100,
            background: seguindo ? '#2fbf6b' : '#c9a24a',
            color: seguindo ? '#fff' : '#111',
            fontFamily: SANS,
            fontWeight: 900,
            fontSize: 52,
            boxShadow: seguindo ? '0 12px 50px rgba(47,191,107,0.55)' : '0 12px 50px rgba(201,162,74,0.55)',
          }}
        >
          {seguindo ? (
            <Lucide.UserCheck size={58} color="#fff" strokeWidth={2.6} />
          ) : (
            <Lucide.UserPlus size={58} color="#111" strokeWidth={2.4} />
          )}
          <span>
            {seguindo ? 'Seguindo' : texto}
            {marca ? <span style={{fontWeight: 700, opacity: 0.8}}> {marca}</span> : null}
          </span>
        </div>
      </div>
      <Cursor pontos={[{f: tClique, x: 575, y: topo + 62, clique: true}]} sumirApos={30} />
      <Confete inicio={tClique + 2} x={540} y={topo + 60} />
    </>
  );
};
