import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {FundoFoto, Elemento} from './CenasNovas';
import {Confete, TituloMask} from './Efeitos';

// ---------- TIPOS ----------
export type CenaDado = {
  narracao: string;
  tipo: string;
  destaque: string;
  imagem?: string;
  elementos?: Elemento[];
};
type Props = {
  cena: CenaDado;
  entradas: number[];
  titulo: string;
  foto?: string;
  cor: string;
};

const SANS = "'Segoe UI', Arial, sans-serif";
const SERIF = "Georgia, 'Times New Roman', serif";
const MONO = "Consolas, 'Courier New', monospace";
const FG = '#f2efe6';
const MUDO = '#77777c';
const CREME = '#e9e4d4';
const CORES = ['#c9a24a', '#4aa3c9', '#c9604a', '#6cc98a', '#9a7bd4'];

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// ---------- UTILIDADES ----------
type Item = {rotulo: string; texto: string; valor: number; casas: number};

const numeroDe = (t: string): number => {
  const m = t.replace(/\./g, '').match(/(\d+(?:,\d+)?)/);
  return m ? parseFloat(m[1].replace(',', '.')) : 0;
};

// "Nome|47,03%"  ou  "Nome 47,03%"  ->  {rotulo, texto, valor}
const lerItem = (el: Elemento): Item => {
  let rotulo = el.texto;
  let texto = '';
  if (el.texto.includes('|')) {
    const [a, ...b] = el.texto.split('|');
    rotulo = a.trim();
    texto = b.join('|').trim();
  } else {
    const m = el.texto.match(/^(.*?)\s+([^\s]*\d[^\s]*)$/);
    if (m) {
      rotulo = m[1].trim();
      texto = m[2].trim();
    }
  }
  const casas = (texto.match(/,(\d+)/)?.[1] ?? '').length;
  return {rotulo, texto, valor: numeroDe(texto), casas};
};

// troca o número do texto original pelo valor animado (mantém R$, %, bi etc.)
const comNumero = (original: string, atual: number, casas: number) => {
  const s = atual.toLocaleString('pt-BR', {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  });
  return original.replace(/\d[\d.]*(?:,\d+)?/, s);
};

const useMola = (inicio: number, forte = false) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({
    frame: frame - inicio,
    fps,
    config: forte ? {damping: 10, stiffness: 170, mass: 0.7} : {damping: 22, stiffness: 90, mass: 0.9},
  });
};

const Cabecalho: React.FC<{texto: string}> = ({texto}) => (
  <TituloMask texto={texto} tam={texto.length > 22 ? 72 : 94} top={190} />
);

const Fundo: React.FC<{foto?: string}> = ({foto}) => (
  <>
    <AbsoluteFill style={{background: '#0a0a0c'}} />
    <FundoFoto foto={foto} opacidade={0.55} filtro="brightness(0.9)" />
    <AbsoluteFill
      style={{
        background:
          'linear-gradient(to bottom, rgba(10,10,12,0.5), rgba(10,10,12,0.22) 50%, rgba(10,10,12,0.6))',
      }}
    />
  </>
);

// =====================================================================
// 1) BARRAS VERTICAIS
// =====================================================================
export const CenaGraficoBarras: React.FC<Props> = ({cena, entradas, foto, cor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const itens = (cena.elementos ?? []).map(lerItem).slice(0, 5);
  const max = Math.max(1, ...itens.map((i) => i.valor));
  const iMax = itens.findIndex((i) => i.valor === max);
  const larguraTotal = 920;
  const gap = 36;
  const n = Math.max(1, itens.length);
  const largura = (larguraTotal - gap * (n - 1)) / n;
  const alturaMax = 700;
  const base = 1330;

  return (
    <AbsoluteFill>
      <Fundo foto={foto} />
      <Cabecalho texto={cena.destaque} />
      {/* linhas de grade */}
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0}}>
        {[0, 0.25, 0.5, 0.75, 1].map((f, k) => (
          <line
            key={k}
            x1={80}
            x2={1000}
            y1={base - alturaMax * f}
            y2={base - alturaMax * f}
            stroke="#ffffff"
            strokeOpacity={k === 0 ? 0.5 : 0.1}
            strokeDasharray={k === 0 ? undefined : '8 12'}
            strokeWidth={2}
          />
        ))}
      </svg>
      {itens.map((it, i) => {
        const ini = entradas[i] ?? 10 + i * 14;
        const e = spring({frame: frame - ini, fps, config: {damping: 16, stiffness: 90, mass: 0.9}});
        const h = (alturaMax * it.valor * Math.min(e, 1.04)) / max;
        const x = 80 + i * (largura + gap);
        const cheia = i === iMax;
        const cc = cheia ? cor : CREME;
        const atual = it.valor * Math.min(1, Math.max(0, e));
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: 'absolute',
                left: x,
                top: base - h,
                width: largura,
                height: h,
                background: `linear-gradient(to top, ${cc}cc, ${cc})`,
                borderRadius: '10px 10px 0 0',
                boxShadow: cheia ? `0 0 50px ${cor}66` : 'none',
              }}
            />
            <div
              style={{
                position: 'absolute',
                left: x - 20,
                width: largura + 40,
                top: base - h - 76,
                textAlign: 'center',
                fontFamily: SERIF,
                fontWeight: 700,
                fontSize: n > 3 ? 54 : 66,
                color: cheia ? cor : FG,
                opacity: interpolate(e, [0, 0.3], [0, 1], clamp),
              }}
            >
              {comNumero(it.texto || String(it.valor), atual, it.casas)}
            </div>
            <div
              style={{
                position: 'absolute',
                left: x - 20,
                width: largura + 40,
                top: base + 22,
                textAlign: 'center',
                fontFamily: SANS,
                fontWeight: 700,
                fontSize: n > 3 ? 34 : 42,
                lineHeight: 1.1,
                color: FG,
                opacity: interpolate(frame, [ini, ini + 8], [0, 1], clamp),
              }}
            >
              {it.rotulo}
            </div>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

// =====================================================================
// 2) LINHA QUE SE DESENHA
// =====================================================================
export const CenaGraficoLinha: React.FC<Props> = ({cena, entradas, foto, cor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const itens = (cena.elementos ?? []).map(lerItem).slice(0, 7);
  const W = 880;
  const H = 640;
  const ox = 100;
  const oy = 520;
  const vals = itens.map((i) => i.valor);
  const mn = Math.min(...vals);
  const mx = Math.max(...vals);
  const folga = (mx - mn || mx || 1) * 0.18;
  const lo = Math.max(0, mn - folga);
  const hi = mx + folga;
  const n = itens.length;
  const pts = itens.map((it, i) => ({
    x: ox + (n === 1 ? W / 2 : (W * i) / (n - 1)),
    y: oy + H - ((it.valor - lo) / (hi - lo || 1)) * H,
  }));
  const ents: number[] = [];
  itens.forEach((_, i) => {
    ents.push(Math.max(i === 0 ? 10 : ents[i - 1] + 10, entradas[i] ?? 0));
  });

  return (
    <AbsoluteFill>
      <Fundo foto={foto} />
      <Cabecalho texto={cena.destaque} />
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0}}>
        {[0, 0.25, 0.5, 0.75, 1].map((f, k) => (
          <line
            key={k}
            x1={ox - 20}
            x2={ox + W + 20}
            y1={oy + H - H * f}
            y2={oy + H - H * f}
            stroke="#fff"
            strokeOpacity={k === 0 ? 0.5 : 0.1}
            strokeDasharray={k === 0 ? undefined : '8 12'}
            strokeWidth={2}
          />
        ))}
        {/* área sob a linha, revelada junto com o traço */}
        {n > 1 ? (
          <>
            <defs>
              <linearGradient id="areaL" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor={cor} stopOpacity={0.35} />
                <stop offset="1" stopColor={cor} stopOpacity={0} />
              </linearGradient>
              <clipPath id="revelaL">
                <rect
                  x={0}
                  y={0}
                  height={1920}
                  width={interpolate(
                    frame,
                    ents.map((e) => e),
                    pts.map((p) => p.x),
                    clamp,
                  )}
                />
              </clipPath>
            </defs>
            <g clipPath="url(#revelaL)">
              <path
                d={`M ${pts[0].x} ${oy + H} L ${pts.map((p) => `${p.x} ${p.y}`).join(' L ')} L ${pts[n - 1].x} ${oy + H} Z`}
                fill="url(#areaL)"
              />
            </g>
          </>
        ) : null}
        {pts.slice(1).map((p, j) => {
          const a = pts[j];
          const prog = interpolate(frame, [ents[j + 1] - 16, ents[j + 1]], [0, 1], clamp);
          return (
            <line
              key={j}
              x1={a.x}
              y1={a.y}
              x2={p.x}
              y2={p.y}
              stroke={cor}
              strokeWidth={10}
              strokeLinecap="round"
              pathLength={1}
              strokeDasharray="1"
              strokeDashoffset={1 - prog}
              style={{filter: `drop-shadow(0 0 12px ${cor}aa)`}}
            />
          );
        })}
        {pts.map((p, i) => {
          const e = spring({frame: frame - ents[i], fps, config: {damping: 9, stiffness: 160, mass: 0.6}});
          return <circle key={i} cx={p.x} cy={p.y} r={18 * Math.max(0, e)} fill="#0a0a0c" stroke={cor} strokeWidth={7} />;
        })}
      </svg>
      {itens.map((it, i) => {
        const e = interpolate(frame, [ents[i], ents[i] + 10], [0, 1], clamp);
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: 'absolute',
                left: pts[i].x - 110,
                width: 220,
                top: pts[i].y - 86,
                textAlign: 'center',
                fontFamily: SERIF,
                fontWeight: 700,
                fontSize: n > 5 ? 44 : 54,
                color: FG,
                opacity: e,
                transform: `translateY(${interpolate(e, [0, 1], [14, 0])}px)`,
              }}
            >
              {it.texto || it.valor}
            </div>
            <div
              style={{
                position: 'absolute',
                left: pts[i].x - 90,
                width: 180,
                top: oy + H + 26,
                textAlign: 'center',
                fontFamily: MONO,
                fontSize: n > 5 ? 28 : 34,
                color: MUDO,
                opacity: e,
              }}
            >
              {it.rotulo}
            </div>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

// =====================================================================
// 3) ROSCA (percentuais)
// =====================================================================
export const CenaRosca: React.FC<Props> = ({cena, entradas, foto}) => {
  const frame = useCurrentFrame();
  const itens = (cena.elementos ?? []).map(lerItem).slice(0, 5);
  const soma = itens.reduce((a, b) => a + b.valor, 0) || 1;
  const R = 270;
  const C = 2 * Math.PI * R;
  const cx = 540;
  const cy = 800;
  const ents = itens.map((_, i) => Math.max(8 + i * 16, entradas[i] ?? 0));
  let acum = 0;
  const segs = itens.map((it, i) => {
    const frac = it.valor / soma;
    const ini = acum;
    acum += frac;
    const prog = interpolate(frame, [ents[i], ents[i] + 22], [0, 1], clamp);
    return {frac, ini, prog};
  });
  const iMax = itens.findIndex((i) => i.valor === Math.max(...itens.map((x) => x.valor)));
  // número no centro: o do último item que já entrou
  const ativo = Math.max(0, ents.filter((e) => frame >= e).length - 1);
  const ca = itens[ativo];
  const pulso = spring({
    frame: frame - (ents[ativo] ?? 0),
    fps: 30,
    config: {damping: 10, stiffness: 160, mass: 0.6},
  });
  const mostrado = ca ? ca.valor * interpolate(frame, [ents[ativo], ents[ativo] + 20], [0, 1], clamp) : 0;

  return (
    <AbsoluteFill>
      <Fundo foto={foto} />
      <Cabecalho texto={cena.destaque} />
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0}}>
        <circle cx={cx} cy={cy} r={R} fill="none" stroke="#ffffff" strokeOpacity={0.08} strokeWidth={110} />
        <g transform={`rotate(-90 ${cx} ${cy})`}>
          {segs.map((s, i) => (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={R}
              fill="none"
              stroke={CORES[i % CORES.length]}
              strokeWidth={i === ativo ? 126 : 110}
              strokeDasharray={`${Math.max(0, C * s.frac * s.prog - 4)} ${C}`}
              strokeDashoffset={-C * s.ini}
              style={{filter: i === iMax ? `drop-shadow(0 0 16px ${CORES[i % CORES.length]}88)` : undefined}}
            />
          ))}
        </g>
      </svg>
      {ca ? (
        <div
          style={{
            position: 'absolute',
            left: cx - 220,
            width: 440,
            top: cy - 105,
            textAlign: 'center',
            fontFamily: SERIF,
            fontWeight: 700,
            fontSize: 128,
            color: FG,
            transform: `scale(${interpolate(pulso, [0, 1], [0.8, 1])})`,
          }}
        >
          {comNumero(ca.texto || String(ca.valor), mostrado, ca.casas)}
          <div style={{fontFamily: SANS, fontSize: 40, fontWeight: 600, color: MUDO, marginTop: 4}}>
            {ca.rotulo}
          </div>
        </div>
      ) : null}
      {/* legenda */}
      <div style={{position: 'absolute', left: 150, right: 150, top: 1180}}>
        {itens.map((it, i) => {
          const e = interpolate(frame, [ents[i], ents[i] + 10], [0, 1], clamp);
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 22,
                marginBottom: 22,
                opacity: e,
                transform: `translateX(${interpolate(e, [0, 1], [-40, 0])}px)`,
              }}
            >
              <div style={{width: 34, height: 34, borderRadius: 8, background: CORES[i % CORES.length]}} />
              <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 46, color: FG, flex: 1}}>{it.rotulo}</div>
              <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 46, color: CORES[i % CORES.length]}}>
                {it.texto}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// =====================================================================
// 4) NÚMERO GIGANTE
// =====================================================================
export const CenaNumeroGigante: React.FC<Props> = ({cena, entradas, foto, cor}) => {
  const frame = useCurrentFrame();
  const alvo = numeroDe(cena.destaque);
  const casas = (cena.destaque.match(/,(\d+)/)?.[1] ?? '').length;
  const t0 = 8;
  const dur = 34;
  const prog = interpolate(frame, [t0, t0 + dur], [0, 1], clamp);
  const suave = 1 - Math.pow(1 - prog, 3);
  const chegou = frame - (t0 + dur);
  const choque = chegou > 0 ? Math.exp(-chegou * 0.28) * Math.sin(chegou * 1.8) * 14 : 0;
  const escala = chegou > 0 ? 1 + 0.12 * Math.exp(-chegou * 0.25) : 0.85 + 0.15 * suave;
  const texto = comNumero(cena.destaque, alvo * suave, casas);
  const eLegenda = interpolate(frame, [entradas[0] ?? 40, (entradas[0] ?? 40) + 12], [0, 1], clamp);
  const eSub = interpolate(frame, [entradas[1] ?? 70, (entradas[1] ?? 70) + 12], [0, 1], clamp);
  const tamanho = cena.destaque.length > 7 ? 230 : 320;

  return (
    <AbsoluteFill>
      <Fundo foto={foto} />
      {/* raios de fundo */}
      <AbsoluteFill
        style={{
          background: `repeating-conic-gradient(from ${frame * 0.4}deg at 50% 46%, ${cor}14 0deg 6deg, transparent 6deg 18deg)`,
          opacity: interpolate(prog, [0, 1], [0, 1]),
          maskImage: 'radial-gradient(circle at 50% 46%, black 10%, transparent 62%)',
          WebkitMaskImage: 'radial-gradient(circle at 50% 46%, black 10%, transparent 62%)',
        }}
      />
      <Confete inicio={t0 + dur} x={540} y={880} cores={[cor, '#ffffff', '#f7c600', '#2fbf6b']} qtd={30} />
      {/* anéis de pulso quando o número chega */}
      {[0, 1, 2].map((k) => {
        const f = chegou - k * 7;
        if (f < 0) return null;
        const r = interpolate(f, [0, 40], [200, 640], clamp);
        return (
          <div
            key={k}
            style={{
              position: 'absolute',
              left: 540 - r,
              top: 880 - r,
              width: r * 2,
              height: r * 2,
              borderRadius: '50%',
              border: `5px solid ${cor}`,
              opacity: interpolate(f, [0, 40], [0.7, 0], clamp),
            }}
          />
        );
      })}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 880 - tamanho * 0.58,
          textAlign: 'center',
          fontFamily: SERIF,
          fontWeight: 800,
          fontSize: tamanho,
          lineHeight: 1,
          color: FG,
          transform: `translateX(${choque}px) scale(${escala})`,
          textShadow: `0 0 70px ${cor}aa, 0 8px 40px rgba(0,0,0,0.7)`,
          letterSpacing: -4,
        }}
      >
        {texto}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 90,
          right: 90,
          top: 1130,
          textAlign: 'center',
          fontFamily: SANS,
          fontWeight: 800,
          fontSize: 66,
          lineHeight: 1.1,
          color: cor,
          opacity: eLegenda,
          transform: `translateY(${interpolate(eLegenda, [0, 1], [30, 0])}px)`,
        }}
      >
        {cena.elementos?.[0]?.texto}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 110,
          right: 110,
          top: 1290,
          textAlign: 'center',
          fontFamily: SANS,
          fontWeight: 500,
          fontSize: 46,
          lineHeight: 1.2,
          color: '#bdbab0',
          opacity: eSub,
          transform: `translateY(${interpolate(eSub, [0, 1], [24, 0])}px)`,
        }}
      >
        {cena.elementos?.[1]?.texto}
      </div>
    </AbsoluteFill>
  );
};

// =====================================================================
// 5) RANKING (barras horizontais, do maior ao menor)
// =====================================================================
export const CenaRanking: React.FC<Props> = ({cena, entradas, foto, cor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const itens = (cena.elementos ?? []).map(lerItem).slice(0, 5);
  const max = Math.max(1, ...itens.map((i) => i.valor));
  const topo = 400;
  const alt = 190;
  const barraX = 190;
  const barraMax = 560;

  return (
    <AbsoluteFill>
      <Fundo foto={foto} />
      <Cabecalho texto={cena.destaque} />
      {itens.map((it, i) => {
        const ini = Math.max(8 + i * 14, entradas[i] ?? 0);
        const e = spring({frame: frame - ini, fps, config: {damping: 16, stiffness: 90, mass: 0.9}});
        const op = interpolate(frame, [ini, ini + 8], [0, 1], clamp);
        const y = topo + i * alt;
        const lider = i === 0;
        const cc = lider ? cor : CREME;
        const atual = it.valor * Math.min(1, Math.max(0, e));
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: 'absolute',
                left: 60,
                top: y + 18,
                width: 110,
                fontFamily: SERIF,
                fontWeight: 800,
                fontSize: 100,
                lineHeight: 1,
                color: lider ? cor : '#55555a',
                opacity: op,
              }}
            >
              {i + 1}
            </div>
            <div
              style={{
                position: 'absolute',
                left: barraX,
                top: y,
                fontFamily: SANS,
                fontWeight: 700,
                fontSize: 44,
                color: FG,
                opacity: op,
              }}
            >
              {it.rotulo}
            </div>
            <div
              style={{
                position: 'absolute',
                left: barraX,
                top: y + 70,
                height: 62,
                width: Math.max(0, (barraMax * it.valor * Math.min(e, 1.03)) / max),
                background: `linear-gradient(to right, ${cc}99, ${cc})`,
                borderRadius: 10,
                boxShadow: lider ? `0 0 40px ${cor}66` : 'none',
              }}
            />
            <div
              style={{
                position: 'absolute',
                left: barraX + (barraMax * it.valor * Math.min(e, 1.03)) / max + 20,
                top: y + 66,
                fontFamily: SERIF,
                fontWeight: 700,
                fontSize: 54,
                color: lider ? cor : FG,
                opacity: op,
                whiteSpace: 'nowrap',
              }}
            >
              {comNumero(it.texto || String(it.valor), atual, it.casas)}
            </div>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};
