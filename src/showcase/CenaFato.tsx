import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {CenaSC, TEXTO, TemaProvider, clamp, montarTema, useTema} from './Base';
import type {Som} from './Cenas';

// =====================================================================
// FATO REAL (perfil documental): parede de papel, objeto real que entra em 3D e sai com borrao,
// retrato que sobe dentro de um circulo, nome digitado, explicacao linha por linha e,
// no final, escurece e um numero brilhante conta ate o valor. Tudo vem da narracao e das fontes.
// =====================================================================
type P = {c: CenaSC; dur: number};
const sai = Easing.bezier(0.16, 1, 0.3, 1);
const entra = Easing.bezier(0.7, 0, 0.3, 1);

export const tempoNumero = (c: CenaSC, dur: number) => {
  if (!c.numero) return Infinity;
  const t = dur - Math.max(78, Math.round(dur * 0.34));
  return t >= 130 ? t : Infinity;
};

const fmt = (v: number, dec: number) => v.toLocaleString('pt-BR', {minimumFractionDigits: dec, maximumFractionDigits: dec});

export const Papel: React.FC = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse at 30% 12%, #eceeee 0%, #d6d9da 55%, #bfc3c5 100%)'}}>
    <svg width="1080" height="1920" viewBox="0 0 540 960" preserveAspectRatio="none" style={{position: 'absolute', inset: 0, opacity: 0.32, mixBlendMode: 'multiply'}}>
      <filter id="papel">
        <feTurbulence type="fractalNoise" baseFrequency="0.035 0.05" numOctaves="4" seed="7" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="540" height="960" filter="url(#papel)" />
    </svg>
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 50%, transparent 55%, rgba(0,0,0,0.18) 100%)'}} />
  </AbsoluteFill>
);

export const CenaFatoReal: React.FC<P> = ({c, dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const T = useTema();
  const ac = c.acento ?? '#3ddc84';
  const Tc = montarTema('escuro', ac);
  const tNum = Number.isFinite(tempoNumero(c, dur)) ? tempoNumero(c, dur) : 100000;
  const escuro = interpolate(f, [tNum, tNum + 14], [0, 1], clamp);
  const linhas = (c.linhas ?? []).slice(0, 4);
  const titulo = (c.titulo ?? '').trim();
  const temObj = !!c.objeto;
  const recorte = !!c.recorte;

  // --- circulo + retrato ---
  const subida = sai(interpolate(f, [4, 34], [0, 1], clamp));
  const encolhe = entra(interpolate(f, [44, 72], [0, 1], clamp));
  const R0 = 600;
  const R = recorte ? R0 * subida * (1 - encolhe) : R0 * subida - (R0 - 430) * encolhe * subida;
  const cx = 540;
  const cy = recorte ? 1380 : 1330 + 40 * encolhe;
  const subidaRetrato = (1 - subida) * 620;
  const imgRetrato = recorte ? c.recorte! : c.foto!;
  const gris = `grayscale(1) contrast(1.08) brightness(${1 - escuro * 0.42})`;

  // --- objeto 3D (cedula, documento, produto...) ---
  const objEnt = sai(interpolate(f, [0, 26], [0, 1], clamp));
  const objSai = entra(interpolate(f, [40, 56], [0, 1], clamp));
  const objX = (1 - objEnt) * -1300;
  const objY = 330 - objSai * 1500;

  // --- titulo digitado + linhas ---
  const ini = 52;
  const n = Math.max(0, Math.floor((f - ini) / 1.7));
  const shown = titulo.slice(0, n);
  const tam = Math.max(84, Math.min(150, Math.floor(930 / (Math.max(1, titulo.length) * 0.58))));
  const fimTexto = Math.min(tNum - 22, dur - 30);
  const passo = Math.max(10, (fimTexto - (ini + titulo.length * 1.7 + 14)) / Math.max(1, linhas.length));
  const iniLinhas = ini + titulo.length * 1.7 + 10;
  const saiTexto = entra(interpolate(f, [tNum - 4, tNum + 12], [0, 1], clamp));
  const caret = Math.floor(f / 8) % 2 === 0 && n < titulo.length + 6;

  // --- numero final ---
  const num = c.numero;
  let numTxt = '';
  let numEsc = 1;
  const tn = f - (tNum + 6);
  if (num) {
    const cont = Easing.out(Easing.cubic)(interpolate(tn, [0, 46], [0, 1], clamp));
    numTxt = `${num.prefixo ?? ''}${fmt(num.valor * cont, num.decimais ?? 0)}${num.sufixo ?? ''}`;
    numEsc = Math.min(230, 980 / Math.max(5, ((num.prefixo ?? '').length + fmt(num.valor, num.decimais ?? 0).length + (num.sufixo ?? '').length) * 0.62));
  }
  const numEnt = sai(interpolate(tn, [0, 18], [0, 1], clamp));
  const brilho = 0.75 + 0.25 * Math.sin(f / 7);

  return (
    <TemaProvider value={{...T, ...(c.acento ? {acento: Tc.acento, sobreAcento: Tc.sobreAcento} : {})}}>
      <AbsoluteFill style={{background: '#d6d9da'}}>
        <Papel />
        {/* fundo escuro do numero */}
        <AbsoluteFill style={{opacity: escuro, background: `radial-gradient(ellipse at 50% 42%, ${ac}33 0%, #07110c 52%, #030504 100%)`}} />

        {/* retrato */}
        <div style={{position: 'absolute', left: cx - R, top: cy - R, width: R * 2, height: R * 2, borderRadius: '50%', background: '#0b0b0c', overflow: recorte ? 'visible' : 'hidden', boxShadow: recorte ? 'none' : '0 40px 90px rgba(0,0,0,0.38)'}}>
          {!recorte && R > 4 ? (
            <Img src={staticFile(imgRetrato)} style={{position: 'absolute', left: R - 560, top: R - 700 + subidaRetrato * 0.4, width: 1120, height: 1400, objectFit: 'cover', filter: gris, transform: `scale(${1 + f / dur * 0.06})`}} />
          ) : null}
        </div>
        {recorte ? (
          <Img src={staticFile(imgRetrato)} style={{position: 'absolute', left: cx - 470, bottom: -30 - subidaRetrato, width: 940, height: 1190, zIndex: 3, objectFit: 'contain', objectPosition: '50% 100%', filter: `${gris} drop-shadow(26px 34px 34px rgba(0,0,0,0.38))`, opacity: interpolate(f, [2, 14], [0, 1], clamp)}} />
        ) : null}

        {/* objeto */}
        {temObj && objSai < 1 ? (
          <div style={{position: 'absolute', left: 90 + objX, top: objY, width: 900, perspective: 1600, zIndex: 3, filter: `blur(${objSai * 16}px)`, opacity: 1 - objSai * 0.4}}>
            <Img src={staticFile(c.objeto!)} style={{width: 900, height: 520, objectFit: 'cover', borderRadius: 10, transform: `rotateY(${-18 + objEnt * 8}deg) rotateX(5deg) rotateZ(-2deg) scaleY(${1 + objSai * 0.5})`, boxShadow: '30px 40px 60px rgba(0,0,0,0.4)'}} />
          </div>
        ) : null}

        {/* texto */}
        <div data-guarda="ignorar" style={{position: 'absolute', left: 74, right: 74, top: 230, transform: `translateX(${-saiTexto * 1300}px) scaleX(${1 + saiTexto * 0.25})`, filter: `blur(${saiTexto * 20}px)`, opacity: 1 - saiTexto, zIndex: 4}}>
          <div style={{fontFamily: TEXTO, fontWeight: 900, fontSize: tam, lineHeight: 1.02, letterSpacing: -3, color: '#0d0d0f', minHeight: tam * 1.05, wordBreak: 'normal', overflowWrap: 'break-word'}}>
            {shown}
            {caret ? <span style={{display: 'inline-block', width: 8, height: tam * 0.8, marginLeft: 6, background: '#0d0d0f', verticalAlign: 'baseline'}} /> : null}
          </div>
          <div style={{marginTop: 34}}>
            {linhas.map((l, k) => {
              const t0 = iniLinhas + k * passo;
              const e = sai(interpolate(f, [t0, t0 + 14], [0, 1], clamp));
              return (
                <div key={k} style={{fontFamily: TEXTO, fontWeight: 700, fontSize: 52, lineHeight: 1.22, color: e > 0.98 ? '#15151a' : `rgba(21,21,26,${0.18 + 0.82 * e})`, opacity: e, transform: `translateY(${(1 - e) * 22}px)`, filter: `blur(${(1 - e) * 5}px)`, marginBottom: 10}}>
                  {l.split(/(\d[\d.,º%]*)/).map((pt, j) =>
                    j % 2 === 1 ? (
                      <span key={j} style={{backgroundImage: 'linear-gradient(#ffe45c, #ffe45c)', backgroundRepeat: 'no-repeat', backgroundSize: `${Easing.out(Easing.cubic)(interpolate(f, [t0 + 10, t0 + 24], [0, 1], clamp)) * 100}% 78%`, backgroundPosition: '0 85%', padding: '0 4px', margin: '0 -4px'}}>{pt}</span>
                    ) : (
                      <span key={j}>{pt}</span>
                    ),
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* numero */}
        {num && f >= tNum && tNum < 100000 ? (
          <div data-guarda="ignorar" style={{position: 'absolute', left: 0, right: 0, top: 520, display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: recorte ? 2 : 5, opacity: numEnt}}>
            <div style={{fontFamily: TEXTO, fontWeight: 900, fontSize: numEsc, letterSpacing: -4, color: '#eafff1', whiteSpace: 'nowrap', transform: `translateX(${(1 - numEnt) * 900}px) scaleX(${1 + (1 - numEnt) * 0.8})`, filter: `blur(${(1 - numEnt) * 22}px)`, textShadow: `0 0 36px ${ac}, 0 0 ${80 * brilho}px ${ac}, 0 0 140px ${ac}88`}}>
              {numTxt}
            </div>
            {num.rotulo ? (
              <div style={{marginTop: 18, fontFamily: TEXTO, fontWeight: 800, fontSize: 40, letterSpacing: 6, textTransform: 'uppercase', color: 'rgba(234,255,241,0.78)', opacity: interpolate(tn, [14, 30], [0, 1], clamp)}}>
                {num.rotulo}
              </div>
            ) : null}
          </div>
        ) : null}
      </AbsoluteFill>
    </TemaProvider>
  );
};

export const sonsFatoReal = (c: CenaSC, dur = 240): Som[] => {
  const tNum = tempoNumero(c, dur);
  const s: Som[] = [{src: 'whoosh', f: 2, vol: 0.55}, {src: 'whoosh', f: 42, vol: 0.5}];
  [56, 62, 68, 74].forEach((k) => s.push({src: 'tick', f: k, vol: 0.28}));
  (c.linhas ?? []).slice(0, 4).forEach((_, k) => s.push({src: 'pop', f: 70 + k * 26, vol: 0.2}));
  if (tNum !== Infinity) {
    s.push({src: 'whoosh', f: tNum, vol: 0.6});
    s.push({src: 'impacto', f: tNum + 22, vol: 0.7});
    s.push({src: 'brilho', f: tNum + 24, vol: 0.5});
  }
  return s;
};


// =====================================================================
// DOCUMENTO: folha de papel com o que diz a fonte, marca-texto nos numeros/nomes e carimbo
// =====================================================================
const escapar = (t: string) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export const CenaFatoDocumento: React.FC<P> = ({c, dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const d = c.documento!;
  const trecho = d.trecho;
  const ent = sai(interpolate(f, [0, 24], [0, 1], clamp));
  const taxa = Math.min(3, Math.max(1.2, trecho.length / Math.max(60, dur * 0.5)));
  const n = Math.max(0, Math.floor((f - 18) * taxa));
  const tFim = 18 + trecho.length / taxa;
  // segmentos (normal / destaque)
  const hls = (d.destaques ?? []).filter((x) => x && trecho.includes(x));
  const re = hls.length ? new RegExp('(' + hls.map(escapar).join('|') + ')', 'g') : null;
  const partes = re ? trecho.split(re).filter((x) => x !== '') : [trecho];
  let off = 0;
  let k = 0;
  const tCar = Math.min(dur - 20, tFim + 14 + hls.length * 11 + 10);
  const car = spring({frame: f - tCar, fps, config: {damping: 9, stiffness: 190, mass: 0.7}});
  const tremor = f >= tCar && f < tCar + 8 ? Math.sin(f * 3) * 5 : 0;
  return (
    <AbsoluteFill style={{background: '#d6d9da'}}>
      <Papel />
      <div style={{position: 'absolute', left: 90, top: 300, width: 900, transform: `perspective(1800px) translateY(${(1 - ent) * 1200}px) rotateX(${(1 - ent) * 24}deg) rotateZ(-1.4deg) translateX(${tremor}px)`, opacity: Math.min(1, ent * 2)}}>
        <div style={{position: 'absolute', left: 330, top: -26, width: 240, height: 54, background: 'rgba(236,214,120,0.78)', transform: 'rotate(-2deg)', boxShadow: '0 4px 10px rgba(0,0,0,0.15)', zIndex: 3}} />
        <div style={{background: 'repeating-linear-gradient(180deg, #fbfaf5 0px, #fbfaf5 61px, #ecebe3 62px)', padding: '70px 64px 80px', borderRadius: 6, boxShadow: '26px 34px 60px rgba(0,0,0,0.32)', minHeight: 760, position: 'relative'}}>
          <div style={{fontFamily: TEXTO, fontWeight: 800, fontSize: 26, letterSpacing: 6, color: '#7c7c76', textTransform: 'uppercase'}}>O que diz a fonte</div>
          <div style={{fontFamily: TEXTO, fontWeight: 900, fontSize: 44, color: '#15151a', marginTop: 10}}>{d.fonte}</div>
          {d.data ? <div style={{fontFamily: TEXTO, fontWeight: 600, fontSize: 28, color: '#7c7c76', marginTop: 2}}>{d.data}</div> : null}
          <div style={{height: 3, background: '#15151a', margin: '26px 0 34px', width: Math.max(0, Math.min(1, (f - 8) / 20)) * 100 + '%'}} />
          <div data-guarda="ignorar" style={{fontFamily: "Georgia, 'Times New Roman', serif", fontSize: 50, lineHeight: 1.34, color: '#1b1b20'}}>
            {partes.map((t, i) => {
              const ehHl = hls.includes(t);
              const ini = off;
              off += t.length;
              const vis = Math.max(0, Math.min(t.length, n - ini));
              if (ehHl) {
                const idx = k++;
                const p0 = tFim + 6 + idx * 11;
                const w = Easing.out(Easing.cubic)(interpolate(f, [p0, p0 + 12], [0, 1], clamp));
                return (
                  <span key={i} style={{backgroundImage: 'linear-gradient(#ffe45c, #ffe45c)', backgroundRepeat: 'no-repeat', backgroundSize: `${w * 100}% 82%`, backgroundPosition: '0 78%', fontWeight: 700, padding: '0 4px', margin: '0 -4px'}}>
                    {t.slice(0, vis)}
                  </span>
                );
              }
              return <span key={i}>{t.slice(0, vis)}</span>;
            })}
          </div>
          {f >= tCar ? (
            <div style={{position: 'absolute', right: 36, bottom: 46, transform: `rotate(-9deg) scale(${3 - 2 * Math.min(1.12, car)})`, opacity: Math.min(1, car * 2), border: '9px solid #c4261d', color: '#c4261d', borderRadius: 14, padding: '8px 26px', fontFamily: TEXTO, fontWeight: 900, fontSize: 64, letterSpacing: 5, mixBlendMode: 'multiply'}}>
              {d.selo}
            </div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const sonsFatoDocumento = (c: CenaSC, dur = 200): Som[] => {
  const d = c.documento;
  const len = d?.trecho.length ?? 80;
  const taxa = Math.min(3, Math.max(1.2, len / Math.max(60, dur * 0.5)));
  const tFim = 18 + len / taxa;
  const nh = (d?.destaques ?? []).length;
  const s: Som[] = [{src: 'whoosh', f: 2, vol: 0.5}];
  [24, 34, 44].forEach((k) => s.push({src: 'tick', f: Math.round(k), vol: 0.25}));
  for (let i = 0; i < nh; i++) s.push({src: 'pop', f: Math.round(tFim + 6 + i * 11), vol: 0.3});
  s.push({src: 'carimbo', f: Math.round(Math.min(dur - 20, tFim + 14 + nh * 11 + 10)), vol: 0.9});
  return s;
};
