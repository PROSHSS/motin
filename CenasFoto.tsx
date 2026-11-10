import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Cursor} from '../Efeitos';
import {CenaSC, Esfera, FINA, FORTE, Manchete, SERIFA, TEXTO, TemaProvider, clamp, hash, montarTema, sombraObjeto, useTema} from './Base';
import {Lupa} from './Objetos';
import type {Som} from './Cenas';

type P = {c: CenaSC; dur: number};
const ease = Easing.bezier(0.22, 1, 0.36, 1);
const semente = (s?: string) => (s ?? 'x').split('').reduce((a, ch) => a + ch.charCodeAt(0), 0);

// Foto com movimento de camera lento (zoom/pan), direcao diferente por foto
const Foto: React.FC<{src: string; dur: number; zoom?: number; pos?: string; style?: React.CSSProperties}> = ({src, dur, zoom = 0.1, pos = '50% 50%', style}) => {
  const frame = useCurrentFrame();
  const h = hash(semente(src));
  const dir = h > 0.5 ? 1 : -1;
  const p = frame / Math.max(1, dur);
  const dx = (h - 0.5) * 60 * p * dir;
  if (!src) {
    // sem imagem (ex.: a geracao falhou): fundo escuro de documentario em vez de erro
    return <div style={{width: '100%', height: '100%', background: 'radial-gradient(ellipse at 50% 40%, #2a2a30 0%, #0c0c0f 75%)', ...style}} />;
  }
  return (
    <Img
      src={staticFile(src)}
      style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: pos, transform: `scale(${1.04 + zoom * p}) translateX(${dx}px)`, ...style}}
    />
  );
};

const Cena: React.FC<{c: CenaSC; children: React.ReactNode}> = ({c, children}) => {
  const T = useTema();
  // cores da cena vem da foto (acento extraido pelo programa)
  const Tc = c.acento ? montarTema(T.claro ? 'claro' : 'escuro', c.acento, undefined) : T;
  const comTema = c.acento ? {...Tc, bg: T.bg, esfA: T.esfA, esfB: T.esfB, esfC: T.esfC, sombra: T.sombra, linha: T.linha, tinta: T.tinta, suave: T.suave, cartao: T.cartao, cartaoTinta: T.cartaoTinta, fantasma: T.fantasma, claro: T.claro} : T;
  return <TemaProvider value={comTema}>{children}</TemaProvider>;
};
const escuro = (acento: string) => montarTema('escuro', acento);

const Chip: React.FC<{texto: string; valor?: string; x: number; y: number; ini: number; rot?: number; grande?: boolean}> = ({texto, valor, x, y, ini, rot = 0, grande}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const e = spring({frame: frame - ini, fps, config: {damping: 10, stiffness: 170, mass: 0.6}});
  const flutua = Math.sin((frame + x) / 20) * 6;
  return (
    <div style={{position: 'absolute', left: x - 500, top: y + flutua - 60, width: 1000, height: 120, display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 6}}>
      <div
        style={{
          transform: `scale(${Math.max(0, e)}) rotate(${rot}deg)`,
          opacity: interpolate(e, [0, 0.3], [0, 1], clamp),
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: grande ? '20px 40px' : '14px 30px',
          borderRadius: 60,
          background: T.acento,
          color: T.sobreAcento,
          boxShadow: `0 18px 34px ${T.sombra}`,
          whiteSpace: 'nowrap',
          fontFamily: FORTE,
        }}
      >
        {valor ? <span style={{fontSize: grande ? 64 : 48, letterSpacing: -1}}>{valor}</span> : null}
        <span style={{fontFamily: TEXTO, fontWeight: 800, fontSize: grande ? 38 : 32, textTransform: 'uppercase', letterSpacing: 1}}>{texto}</span>
      </div>
    </div>
  );
};

// =====================================================================
// 1) HERO: foto em tela cheia, camera lenta, manchete em vidro
// =====================================================================
export const CenaFotoHero: React.FC<P> = ({c, dur}) => {
  const frame = useCurrentFrame();
  const ac = c.acento ?? '#c9a24a';
  const chips = c.chips ?? [];
  const brilho = interpolate(frame, [0, 24], [1, 0.0], clamp);
  return (
    <Cena c={c}>
      <AbsoluteFill style={{background: '#000'}}>
        <Foto src={c.foto!} dur={dur} zoom={0.14} />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.62) 0%, rgba(0,0,0,0) 36%, rgba(0,0,0,0) 56%, rgba(0,0,0,0.72) 100%)'}} />
        <AbsoluteFill style={{background: `radial-gradient(circle at 50% 100%, ${ac}55, transparent 55%)`, mixBlendMode: 'screen'}} />
        <TemaProvider value={escuro(ac)}>
          <Manchete linhas={c.manchete ?? []} top={190} inicio={8} />
          {chips.slice(0, 3).map((ch, i) => (
            <Chip key={i} texto={ch.texto} valor={ch.valor} x={i % 2 === 0 ? 300 : 790} y={1250 + i * 150} ini={26 + i * 10} rot={i % 2 === 0 ? -4 : 3} grande={!!ch.valor} />
          ))}
        </TemaProvider>
        <AbsoluteFill style={{background: '#fff', opacity: brilho * 0.5}} />
      </AbsoluteFill>
    </Cena>
  );
};
export const sonsFotoHero = (c: CenaSC): Som[] => [{src: 'impacto', f: 0, vol: 0.55}, ...(c.chips ?? []).slice(0, 3).map((_, i) => ({src: 'pop', f: 26 + i * 10, vol: 0.45}))];

// =====================================================================
// 2) CELULAR com a foto na tela e balões apontando para detalhes
// =====================================================================
export const CenaFotoCelular: React.FC<P> = ({c, dur}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const e = spring({frame: frame - 3, fps, config: {damping: 16, stiffness: 90, mass: 1}});
  const W = 600;
  const H = 1180;
  const X = 540;
  const Y = 1130;
  const chips = c.chips ?? [];
  const pontos = [
    {x: 250, y: 840},
    {x: 820, y: 1060},
    {x: 300, y: 1330},
  ];
  return (
    <Cena c={c}>
      <Esfera x={950} y={400} r={330} />
      <Esfera x={90} y={1750} r={290} inicio={5} />
      <Manchete linhas={c.manchete ?? []} top={190} inicio={6} />
      <div
        style={{
          position: 'absolute',
          left: X - W / 2,
          top: Y - H / 2 + interpolate(e, [0, 1], [900, 0]) + Math.sin(frame / 24) * 8,
          width: W,
          height: H,
          borderRadius: 96,
          background: T.claro ? 'linear-gradient(145deg, #ffffff, #dcdcd8)' : 'linear-gradient(145deg, #3a3a40, #17171a)',
          boxShadow: `${sombraObjeto(T, 1.3)}, inset 0 0 0 6px ${T.claro ? '#cfcfcb' : '#4a4a52'}`,
          padding: 24,
          transform: `rotate(${interpolate(e, [0, 1], [8, -2])}deg)`,
        }}
      >
        <div style={{width: '100%', height: '100%', borderRadius: 74, overflow: 'hidden', position: 'relative', background: '#000'}}>
          <Foto src={c.foto!} dur={dur} zoom={0.12} />
          <div style={{position: 'absolute', top: 22, left: '50%', width: 150, height: 40, marginLeft: -75, borderRadius: 24, background: '#0b0b0d'}} />
          <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 260, background: 'linear-gradient(180deg, transparent, rgba(0,0,0,0.75))'}} />
          <div style={{position: 'absolute', left: 36, right: 36, bottom: 44, color: '#fff', fontFamily: TEXTO, fontWeight: 800, fontSize: 40, lineHeight: 1.1}}>{c.rotulo ?? ''}</div>
        </div>
      </div>
      {chips.slice(0, 3).map((ch, i) => {
        const ini = 24 + i * 12;
        const l = interpolate(frame, [ini, ini + 12], [0, 1], clamp);
        const pt = pontos[i];
        const lado = i % 2 === 0 ? 1 : -1;
        const bx = lado === 1 ? 190 : 890;
        const by = pt.y - 160;
        return (
          <React.Fragment key={i}>
            <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, zIndex: 5, pointerEvents: 'none'}}>
              <line x1={bx} y1={by} x2={bx + (pt.x - bx) * l} y2={by + (pt.y - by) * l} stroke={T.acento} strokeWidth={6} strokeLinecap="round" />
              <circle cx={pt.x} cy={pt.y} r={interpolate(l, [0.8, 1], [0, 16], clamp)} fill={T.acento} stroke="#fff" strokeWidth={5} />
            </svg>
            <Chip texto={ch.texto} valor={ch.valor} x={bx} y={by} ini={ini} rot={lado * -3} />
          </React.Fragment>
        );
      })}
    </Cena>
  );
};
export const sonsFotoCelular = (c: CenaSC): Som[] => [{src: 'whoosh', f: 2, vol: 0.3}, ...(c.chips ?? []).slice(0, 3).map((_, i) => ({src: 'pop', f: 24 + i * 12, vol: 0.5}))];

// =====================================================================
// 3) LUPA passeando pela foto e ampliando detalhes
// =====================================================================
export const CenaFotoLupa: React.FC<P> = ({c, dur}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const W = 900;
  const H = 1000;
  const CX = 540;
  const CY = 1070;
  const caminho = [
    {x: 380, y: 880},
    {x: 740, y: 1180},
    {x: 520, y: 1000},
  ];
  const t = ease(interpolate(frame, [12, Math.max(40, dur - 14)], [0, 1], clamp));
  const seg = t * (caminho.length - 1);
  const i = Math.min(caminho.length - 2, Math.floor(seg));
  const f = seg - i;
  const lx = caminho[i].x + (caminho[i + 1].x - caminho[i].x) * f;
  const ly = caminho[i].y + (caminho[i + 1].y - caminho[i].y) * f;
  const apar = interpolate(frame, [10, 22], [0, 1], clamp);
  const conteudo = (
    <div style={{position: 'absolute', left: CX - W / 2, top: CY - H / 2, width: W, height: H, borderRadius: 64, overflow: 'hidden', boxShadow: sombraObjeto(T, 1.2)}}>
      <Foto src={c.foto!} dur={dur} zoom={0.04} />
    </div>
  );
  const ch = (c.chips ?? [])[0];
  return (
    <Cena c={c}>
      <Esfera x={120} y={380} r={330} />
      <Esfera x={990} y={1740} r={320} inicio={4} />
      <Manchete linhas={c.manchete ?? []} top={190} inicio={6} />
      {conteudo}
      <Lupa lx={lx} ly={ly} r={185} zoom={2.1} opac={apar}>
        {conteudo}
      </Lupa>
      {ch ? <Chip texto={ch.texto} valor={ch.valor} x={540} y={1660} ini={34} grande /> : null}
    </Cena>
  );
};
export const sonsFotoLupa = (): Som[] => [{src: 'pop', f: 8, vol: 0.45}, {src: 'whoosh', f: 14, vol: 0.3}, {src: 'tick', f: 34, vol: 0.5}];

// =====================================================================
// 4) POLAROIDS jogadas na mesa (recortes diferentes da mesma foto)
// =====================================================================
export const CenaFotoPolaroid: React.FC<P> = ({c, dur}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const chips = c.chips ?? [];
  const cartoes = [
    {x: 310, y: 830, rot: -9, pos: '20% 40%', z: 1},
    {x: 770, y: 1050, rot: 7, pos: '80% 60%', z: 2},
    {x: 330, y: 1430, rot: -3, pos: '50% 50%', z: 3},
  ];
  return (
    <Cena c={c}>
      <Esfera x={930} y={420} r={330} />
      <Esfera x={100} y={1700} r={300} inicio={5} />
      <Manchete linhas={c.manchete ?? []} top={190} inicio={6} />
      {cartoes.map((k, i) => {
        const ini = 8 + i * 12;
        const e = spring({frame: frame - ini, fps, config: {damping: 11, stiffness: 120, mass: 0.8}});
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: k.x - 220,
              top: k.y - 260 + interpolate(e, [0, 1], [-1400, 0]),
              width: 440,
              height: 520,
              padding: '20px 20px 84px',
              background: '#fff',
              borderRadius: 14,
              boxShadow: `0 30px 60px ${T.sombra}`,
              transform: `rotate(${k.rot + interpolate(e, [0, 1], [-25, 0])}deg)`,
              zIndex: k.z,
            }}
          >
            <div style={{width: '100%', height: '100%', overflow: 'hidden', background: '#111'}}>
              <div style={{width: '100%', height: '100%', transform: 'scale(1.9)', transformOrigin: k.pos}}><Foto src={c.foto!} dur={dur} zoom={0.12} pos={k.pos} style={{transform: undefined}} /></div>
            </div>
            <div style={{position: 'absolute', left: 22, right: 22, bottom: 22, height: 56, textAlign: 'center', fontFamily: SERIFA, fontStyle: 'italic', fontSize: 38, color: '#222'}}>
              {chips[i]?.texto ?? ''}
            </div>
          </div>
        );
      })}
    </Cena>
  );
};
export const sonsFotoPolaroid = (): Som[] => [0, 1, 2].map((i) => ({src: 'carimbo', f: 8 + i * 12 + 6, vol: 0.5}));

// =====================================================================
// 5) RECORTE: a foto aparece DENTRO das letras gigantes
// =====================================================================
export const CenaFotoRecorte: React.FC<P> = ({c, dur}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const palavra = (c.fantasma ?? 'AGORA').toUpperCase();
  const e = spring({frame: frame - 4, fps, config: {damping: 14, stiffness: 90, mass: 1}});
  const pan = interpolate(frame, [0, dur], [30, 70], clamp);
  const tam = Math.min(420, 980 / (palavra.length * 0.66));
  return (
    <Cena c={c}>
      <Esfera x={100} y={300} r={300} />
      <Esfera x={1000} y={1650} r={330} inicio={5} />
      <div
        style={{
          position: 'absolute',
          left: 40,
          right: 40,
          top: 700,
          textAlign: 'center',
          fontFamily: FORTE,
          fontSize: tam,
          lineHeight: 1,
          letterSpacing: -tam * 0.04,
          color: 'transparent',
          backgroundImage: c.foto ? `url(${staticFile(c.foto)})` : 'linear-gradient(135deg,#8a8a90,#d8d8dc)',
          backgroundSize: '260% auto',
          backgroundPosition: `${pan}% 50%`,
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          transform: `scale(${interpolate(e, [0, 1], [0.7, 1])})`,
          opacity: interpolate(e, [0, 0.3], [0, 1], clamp),
          filter: `drop-shadow(0 24px 30px ${T.sombra})`,
          whiteSpace: 'nowrap',
        }}
      >
        {palavra}
      </div>
      <Manchete linhas={c.manchete ?? []} top={190} inicio={10} />
      <div style={{position: 'absolute', left: 70, right: 70, top: 1080 + tam * 0.4, textAlign: 'center', fontFamily: SERIFA, fontStyle: 'italic', fontSize: 62, color: T.suave, opacity: interpolate(frame, [26, 40], [0, 1], clamp)}}>
        {c.rotulo ?? ''}
      </div>
    </Cena>
  );
};
export const sonsFotoRecorte = (): Som[] => [{src: 'impacto', f: 4, vol: 0.7}, {src: 'brilho', f: 24, vol: 0.4}];

// =====================================================================
// 6) PERSIANAS: faixas verticais revelam a foto
// =====================================================================
export const CenaFotoPersianas: React.FC<P> = ({c, dur}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const N = 6;
  const ac = c.acento ?? T.acento;
  return (
    <Cena c={c}>
      <AbsoluteFill style={{background: '#000'}}>
        {Array.from({length: N}, (_, i) => {
          const ini = 2 + i * 3;
          const p = ease(interpolate(frame, [ini, ini + 18], [0, 1], clamp));
          return (
            <div key={i} style={{position: 'absolute', left: (1080 / N) * i, top: 0, width: 1080 / N + 1, height: 1920, overflow: 'hidden', transform: `translateY(${(i % 2 ? -1 : 1) * (1 - p) * 1920}px)`}}>
              <div style={{position: 'absolute', left: -(1080 / N) * i, top: 0, width: 1080, height: 1920}}>
                <Foto src={c.foto!} dur={dur} zoom={0.1} />
              </div>
            </div>
          );
        })}
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.0) 40%, rgba(0,0,0,0.78) 100%)'}} />
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 360,
            height: 6,
            background: ac,
            width: `${interpolate(frame, [20, 40], [0, 100], clamp)}%`,
          }}
        />
        <TemaProvider value={escuro(ac)}>
          <Manchete linhas={c.manchete ?? []} top={1300} inicio={24} />
        </TemaProvider>
        {(c.chips ?? [])[0] ? <Chip texto={c.chips![0].texto} valor={c.chips![0].valor} x={300} y={260} ini={30} grande /> : null}
      </AbsoluteFill>
    </Cena>
  );
};
export const sonsFotoPersianas = (): Som[] => [{src: 'whoosh', f: 0, vol: 0.45}, {src: 'impacto', f: 20, vol: 0.5}, {src: 'pop', f: 30, vol: 0.45}];

// =====================================================================
// 7) CARTAO 3D: a foto num cartao que gira em perspectiva, com reflexo
// =====================================================================
export const CenaFotoCard3D: React.FC<P> = ({c, dur}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const e = spring({frame: frame - 3, fps, config: {damping: 16, stiffness: 80, mass: 1.1}});
  const ry = interpolate(e, [0, 1], [70, -14]) + Math.sin(frame / 36) * 6;
  const rx = 8 + Math.cos(frame / 44) * 3;
  const chips = c.chips ?? [];
  return (
    <Cena c={c}>
      <Esfera x={150} y={430} r={320} />
      <Esfera x={970} y={1650} r={340} inicio={4} />
      <Manchete linhas={c.manchete ?? []} top={190} inicio={6} />
      <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 1920, perspective: 1800}}>
        <div
          style={{
            position: 'absolute',
            left: 540 - 420,
            top: 1020 - 520,
            width: 840,
            height: 1040,
            borderRadius: 64,
            overflow: 'hidden',
            transform: `rotateY(${ry}deg) rotateX(${rx}deg)`,
            boxShadow: `${-ry * 1.2}px 50px 90px ${T.sombra}`,
            opacity: interpolate(e, [0, 0.3], [0, 1], clamp),
            border: `10px solid ${T.cartao}`,
          }}
        >
          <Foto src={c.foto!} dur={dur} zoom={0.08} />
          <div style={{position: 'absolute', inset: 0, background: `linear-gradient(${115 + ry}deg, rgba(255,255,255,0.35) 0%, rgba(255,255,255,0) 40%)`}} />
        </div>
      </div>
      {chips.slice(0, 2).map((ch, i) => (
        <Chip key={i} texto={ch.texto} valor={ch.valor} x={i === 0 ? 250 : 830} y={i === 0 ? 1580 : 560} ini={28 + i * 12} rot={i === 0 ? -5 : 5} grande={!!ch.valor} />
      ))}
    </Cena>
  );
};
export const sonsFotoCard3D = (c: CenaSC): Som[] => [{src: 'whoosh', f: 2, vol: 0.35}, ...(c.chips ?? []).slice(0, 2).map((_, i) => ({src: 'pop', f: 28 + i * 12, vol: 0.5}))];

export {FINA, Cursor};


// Imagem de IA como FUNDO de uma cena animada (graficos, listas, citacoes...): movimento de camera + escurecimento
// para o texto continuar legivel. Mistura o motion do Showcase com a cara de foto real.
export const FundoFotoUI: React.FC<{c: CenaSC; dur: number; children: React.ReactNode}> = ({c, dur, children}) => {
  const f = useCurrentFrame();
  const T = useTema();
  const Te = montarTema('escuro', c.acento ?? T.acento);
  const respira = 1 + 0.02 * Math.sin(f / 40);
  return (
    <TemaProvider value={Te}>
      <AbsoluteFill style={{background: '#000'}}>
        <div style={{position: 'absolute', inset: 0, transform: `scale(${respira})`, filter: 'contrast(1.05) saturate(1.04)'}}>
          <Foto src={c.foto!} dur={dur} zoom={0.16} />
        </div>
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.58) 0%, rgba(0,0,0,0.30) 38%, rgba(0,0,0,0.34) 62%, rgba(0,0,0,0.66) 100%)'}} />
        <AbsoluteFill style={{background: `radial-gradient(circle at 50% 100%, ${(c.acento ?? Te.acento)}40, transparent 55%)`, mixBlendMode: 'screen'}} />
        {children}
      </AbsoluteFill>
    </TemaProvider>
  );
};
