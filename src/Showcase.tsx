import React from 'react';
import {CenaMotion,CorteMotion,LegendaMotion,sonsMotion} from './showcase/Motion';
import {ApresentadorMascote, FundoMascote} from './Mascote';
import {AbsoluteFill, Audio, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {RenderCena, TIPOS_COM_POP, calcularEntradas} from './Video';
import {Dados, CenaSC, PALETAS, PALETAS_ESCURAS, TEXTO, Grao, Marca, TemaProvider, VarProvider, aberracao, clamp, filtroAberracao, hash, resolverTema, useTema} from './showcase/Base';
import {Guarda} from './showcase/Guarda';
import {FundoFotoUI, CenaFotoCard3D, CenaFotoCelular, CenaFotoHero, CenaFotoLupa, CenaFotoPersianas, CenaFotoPolaroid, CenaFotoRecorte, sonsFotoCard3D, sonsFotoCelular, sonsFotoHero, sonsFotoLupa, sonsFotoPersianas, sonsFotoPolaroid, sonsFotoRecorte} from './showcase/CenasFoto';
import {CenaFatoDocumento, CenaFatoReal, sonsFatoDocumento, sonsFatoReal} from './showcase/CenaFato';
import {CenaAlerta, CenaCitacao, CenaComparacao, CenaContador, CenaLinhaTempo, CenaRanking, sonsAlerta, sonsCitacao, sonsComparacao, sonsContador, sonsLinhaTempo, sonsRanking} from './showcase/Cenas2';
import {
  CenaCelular, CenaChecklist, CenaFecho, CenaGancho, CenaGrafico, CenaLupa, CenaProcesso, CenaRajada,
  Som, sonsCelular, sonsChecklist, sonsFecho, sonsGancho, sonsGrafico, sonsLupa, sonsProcesso, sonsRajada,
} from './showcase/Cenas';
import {CenaBusca, CenaCartaz, CenaFotoMoldura, CenaGlitch, CenaPasta, CenaPilula, sonsBusca, sonsCartaz, sonsFotoMoldura, sonsGlitch, sonsPasta, sonsPilula} from './showcase/CenasVar';
import {Acabamento, Camera, LegendaDoc, Progresso, agruparPalavras} from './showcase/Documentario';

export const SOBREPOSICAO = 6;
export type Palavra = {palavra: string; inicio: number; fim: number};
export type Tempo = {cena?: number; inicio: number; fim: number};
export type ShowcaseProps = {dados: Dados; tempos?: Tempo[]; palavras?: Palavra[]; audio?: {musica?: boolean; sfx?: boolean; volumeMusica?: number; volumeSfx?: number; transicao?: boolean; narracao?: boolean; legenda?: string; documentario?: boolean}};

const fps0 = 30;
// Plano das cenas: sem voz usa a duracao do JSON; com voz acompanha o tempo da narracao.
export const planejar = (d: Dados, fps: number, tempos?: Tempo[]) => {
  const blocos: {c: CenaSC; from: number; dur: number}[] = [];
  if (d.narrado && tempos && tempos.length >= d.cenas.length) {
    const n = d.cenas.length;
    const froms = d.cenas.map((_, i) => (i === 0 ? 0 : Math.max(0, Math.round(tempos[i].inicio * fps) - 9)));
    const fimTotal = Math.round((tempos[n - 1].fim + 0.8) * fps);
    d.cenas.forEach((c, i) => {
      const prox = i < n - 1 ? froms[i + 1] + SOBREPOSICAO : fimTotal;
      blocos.push({c, from: froms[i], dur: Math.max(24, prox - froms[i])});
    });
    return blocos;
  }
  let ini = 0;
  d.cenas.forEach((c) => {
    const dur = Math.round(c.duracao * fps);
    blocos.push({c, from: ini, dur});
    ini += dur - SOBREPOSICAO;
  });
  return blocos;
};
export const duracaoTotal = (d: Dados, tempos?: Tempo[], fps = fps0) => {
  const b = planejar(d, fps, tempos);
  const u = b[b.length - 1];
  return u ? u.from + u.dur : fps;
};

const renderCena = (c: CenaSC, dur: number) => {
  if(c.motion && c.motion.layout!=='original')return <CenaMotion c={c} dur={dur}/>;
  switch (c.tipo) {
    case 'gancho': return <CenaGancho c={c} dur={dur} />;
    case 'celular': return <CenaCelular c={c} dur={dur} />;
    case 'lupa': return <CenaLupa c={c} dur={dur} />;
    case 'processo': return <CenaProcesso c={c} dur={dur} />;
    case 'grafico': return <CenaGrafico c={c} dur={dur} />;
    case 'rajada': return <CenaRajada c={c} dur={dur} />;
    case 'checklist': return <CenaChecklist c={c} dur={dur} />;
    case 'comparacao': return <CenaComparacao c={c} dur={dur} />;
    case 'contador': return <CenaContador c={c} dur={dur} />;
    case 'ranking': return <CenaRanking c={c} dur={dur} />;
    case 'linha_tempo': return <CenaLinhaTempo c={c} dur={dur} />;
    case 'alerta': return <CenaAlerta c={c} dur={dur} />;
    case 'citacao': return <CenaCitacao c={c} dur={dur} />;
    case 'foto_hero': return <CenaFotoHero c={c} dur={dur} />;
    case 'foto_celular': return <CenaFotoCelular c={c} dur={dur} />;
    case 'foto_lupa': return <CenaFotoLupa c={c} dur={dur} />;
    case 'foto_polaroid': return <CenaFotoPolaroid c={c} dur={dur} />;
    case 'foto_recorte': return <CenaFotoRecorte c={c} dur={dur} />;
    case 'foto_persianas': return <CenaFotoPersianas c={c} dur={dur} />;
    case 'foto_card3d': return <CenaFotoCard3D c={c} dur={dur} />;
    case 'fato_real': return c.foto || c.recorte ? <CenaFatoReal c={c} dur={dur} /> : <CenaFotoHero c={c} dur={dur} />;
    case 'fato_documento': return <CenaFatoDocumento c={c} dur={dur} />;
    case 'cartaz': return <CenaCartaz c={c} dur={dur} />;
    case 'foto_moldura': return c.foto ? <CenaFotoMoldura c={c} dur={dur} /> : <CenaCartaz c={{...c, palavras: c.tags ?? []}} dur={dur} />;
    case 'busca': return <CenaBusca c={c} dur={dur} />;
    case 'pilula': return <CenaPilula c={c} dur={dur} />;
    case 'glitch': return <CenaGlitch c={c} dur={dur} />;
    case 'pasta': return <CenaPasta c={c} dur={dur} />;
    default: return <CenaFecho c={c} dur={dur} />;
  }
};
const sonsDe = (c: CenaSC, dur = 240): Som[] => {
  if(c.motion && c.motion.layout!=='original')return sonsMotion(c);
  switch (c.tipo) {
    case 'gancho': return sonsGancho();
    case 'celular': return sonsCelular(c);
    case 'lupa': return sonsLupa();
    case 'processo': return sonsProcesso();
    case 'grafico': return sonsGrafico(c);
    case 'rajada': return sonsRajada(c);
    case 'checklist': return sonsChecklist(c);
    case 'comparacao': return sonsComparacao();
    case 'contador': return sonsContador();
    case 'ranking': return sonsRanking(c);
    case 'linha_tempo': return sonsLinhaTempo(c);
    case 'alerta': return sonsAlerta();
    case 'citacao': return sonsCitacao(c);
    case 'foto_hero': return sonsFotoHero(c);
    case 'foto_celular': return sonsFotoCelular(c);
    case 'foto_lupa': return sonsFotoLupa();
    case 'foto_polaroid': return sonsFotoPolaroid();
    case 'foto_recorte': return sonsFotoRecorte();
    case 'foto_persianas': return sonsFotoPersianas();
    case 'foto_card3d': return sonsFotoCard3D(c);
    case 'fato_real': return sonsFatoReal(c, dur);
    case 'fato_documento': return sonsFatoDocumento(c, dur);
    case 'cartaz': return sonsCartaz(c);
    case 'foto_moldura': return sonsFotoMoldura();
    case 'busca': return sonsBusca(c);
    case 'pilula': return sonsPilula();
    case 'glitch': return sonsGlitch();
    case 'pasta': return sonsPasta(c);
    default: return sonsFecho();
  }
};

// Transicao escolhida por REGRA (continuidade e narrativa), nao ao acaso: depende do tipo da cena que entra
// e nunca repete a anterior. No modo documentario so as discretas.
const ehFoto = (t: string) => t.startsWith('foto_') || t === 'fato_real';
export const escolherTransicoes = (tipos: string[], sem: number, doc: boolean): number[] => {
  const out: number[] = [];
  tipos.forEach((cur, i) => {
    if (i === 0) { out.push(0); return; }
    const prev = tipos[i - 1];
    let op: number[];
    if (ehFoto(cur) && ehFoto(prev)) op = [10, 1];            // foto -> foto: dissolve / aproximacao suave
    else if (ehFoto(cur)) op = [1, 9, 10];                      // entra foto: camera se aproxima ou empurra
    else if (['fato_documento', 'citacao', 'fecho', 'alerta'].includes(cur)) op = [10, 0];   // momentos serios: discreto
    else if (['glitch', 'contador', 'pilula'].includes(cur)) op = doc ? [0, 9] : [5, 6, 8]; // impacto: iris / chicote / giro
    else if (['busca', 'pasta', 'cartaz', 'ranking', 'linha_tempo', 'comparacao'].includes(cur)) op = [2, 3, 9, 0];  // interface: desliza
    else op = [0, 2, 3, 4];
    if (doc) op = op.filter((x) => [0, 1, 2, 3, 9, 10].includes(x)) || [0];
    if (!op.length) op = [0];
    const livres = op.filter((x) => x !== out[i - 1]);
    const lista = livres.length ? livres : op;
    out.push(lista[Math.floor(hash(sem + i * 3.1) * lista.length) % lista.length]);
  });
  return out;
};

// envelope de cada cena: entrada com sobe+desfoca, saída com escala e franja RGB
const Envelope: React.FC<{dur: number; primeira: boolean; ultima: boolean; v: number; id: number; children: React.ReactNode}> = ({dur, primeira, ultima, v, id, children}) => {
  const frame = useCurrentFrame();
  const T = useTema();
  const ent = primeira ? 1 : Easing.bezier(0.16, 1, 0.3, 1)(interpolate(frame, [0, v >= 5 ? 16 : 12], [0, 1], clamp));
  const sai = ultima ? 0 : Easing.in(Easing.cubic)(interpolate(frame, [dur - SOBREPOSICAO - 2, dur], [0, 1], clamp));
  const amp = primeira ? 0 : aberracao(frame, dur, 7, ultima ? 1 : 5);
  const q = 1 - ent;
  const tr =
    v === 0 ? `translateY(${q * 90}px) scale(${0.94 + 0.06 * ent})`
    : v === 1 ? `scale(${1.06 - 0.06 * ent})`
    : v === 2 ? `translateX(${-q * 260}px) scale(${0.96 + 0.04 * ent})`
    : v === 3 ? `translateX(${q * 260}px) scale(${0.96 + 0.04 * ent})`
    : v === 4 ? `rotate(${q * -5}deg) scale(${0.9 + 0.1 * ent})`
    : v === 5 ? `scale(${1.03 - 0.03 * ent})`                       // iris: abre um circulo
    : v === 6 ? `translateX(${q * 820}px)`                         // chicote lateral com borrao de movimento
    : v === 8 ? `perspective(1400px) rotateX(${q * 38}deg) translateY(${q * 120}px)`   // giro de cartao
    : v === 9 ? `translateY(${-q * 700}px)`                                       // empurrao vertical
    : v === 10 ? `scale(${1.04 - 0.04 * ent})`                                      // dissolve com desfoque
    : `scale(${1.1 - 0.1 * ent})`;                                // zoom atravessando a cena
  const fx = v === 6 && q > 0.01 ? `url(#wb${id})` : '';
  const blur = v === 6 ? 0 : v === 5 ? q * 3 : v === 7 ? q * 14 : v === 10 ? q * 26 : v === 9 ? q * 5 : q * 8;
  return (
    <AbsoluteFill
      style={{
        opacity: v === 5 ? 1 - sai * 0.9 : interpolate(ent, [0, 0.5], [0, 1], clamp) * (1 - sai * 0.9),
        transform: `${tr} scale(${1 + sai * 0.015})`,
        filter: `${filtroAberracao(amp) ?? ''} ${fx} blur(${blur + sai * 6}px)`.trim(),
        clipPath: v === 5 && q > 0.001 ? `circle(${ent * 78}% at 50% 56%)` : undefined,
      }}
    >
      {v === 6 ? (
        <svg width="0" height="0" style={{position: 'absolute'}}>
          <filter id={`wb${id}`} x="-50%" y="-5%" width="200%" height="110%">
            <feGaussianBlur stdDeviation={`${q * 46} 0`} />
          </filter>
        </svg>
      ) : null}
      {v === 5 && q > 0.02 ? (
        <div style={{position: 'absolute', left: 540 - ent * 1215, top: 1075 - ent * 1215, width: ent * 2430, height: ent * 2430, borderRadius: '50%', border: `10px solid ${T.acento}`, opacity: q, boxSizing: 'border-box', zIndex: 20}} />
      ) : null}
      {children}
    </AbsoluteFill>
  );
};

// faixa colorida que varre a tela em alguns cortes
const Varredura: React.FC<{lado: 1 | -1}> = ({lado}) => {
  const frame = useCurrentFrame();
  const T = useTema();
  const p = Easing.bezier(0.7, 0, 0.3, 1)(interpolate(frame, [0, 16], [0, 1], clamp));
  const x = lado === 1 ? interpolate(p, [0, 1], [-1200, 1300]) : interpolate(p, [0, 1], [1300, -1200]);
  return (
    <AbsoluteFill style={{pointerEvents: 'none', zIndex: 8}}>
      <div style={{position: 'absolute', top: -100, bottom: -100, left: x, width: 1100, background: T.acento, transform: 'skewX(-10deg)', opacity: 0.95}} />
    </AbsoluteFill>
  );
};

// esfera que "floresce" no corte e limpa a tela
const Floracao: React.FC<{em: number}> = ({em}) => {
  const frame = useCurrentFrame();
  const T = useTema();
  const t = frame - em;
  if (t < -4 || t > 16) return null;
  const e = Easing.bezier(0.2, 0.8, 0.2, 1)(interpolate(t, [-4, 8], [0, 1], clamp));
  const o = interpolate(t, [4, 16], [0.38, 0], clamp);
  return (
    <AbsoluteFill style={{pointerEvents: 'none', zIndex: 8, opacity: o}}>
      <div
        style={{
          position: 'absolute', left: 540 - 1500, top: 960 - 1500, width: 3000, height: 3000, borderRadius: '50%',
          background: `radial-gradient(circle at 40% 35%, ${T.esfA}, ${T.esfB} 70%, ${T.esfC})`,
          transform: `scale(${e * 0.5})`,
        }}
      />
    </AbsoluteFill>
  );
};


// ---------- LEGENDA (3 palavras por vez, palavra falada em destaque) ----------
const norm = (t: string) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, '');
const Legenda: React.FC<{palavras: Palavra[]; bottom?: number}> = ({palavras, bottom = 168}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  // frases curtas: ate 4 palavras ou ate a pontuacao; a frase fica na tela ate a proxima comecar
  const grupos = React.useMemo(() => {
    const g: {ini: number; fim: number; idx: number[]}[] = [];
    let cur: number[] = [];
    palavras.forEach((p, i) => {
      cur.push(i);
      const pontua = /[.,;:!?…]$/.test(p.palavra);
      const longa = cur.map((k) => palavras[k].palavra).join(' ').length >= 24;
      if (cur.length >= 4 || longa || (pontua && cur.length >= 2) || (pontua && /[.!?…]$/.test(p.palavra))) {
        g.push({ini: palavras[cur[0]].inicio, fim: p.fim, idx: cur});
        cur = [];
      }
    });
    if (cur.length) g.push({ini: palavras[cur[0]].inicio, fim: palavras[cur[cur.length - 1]].fim, idx: cur});
    return g;
  }, [palavras]);
  if (!grupos.length) return null;
  let gi = grupos.findIndex((g, i) => t >= g.ini - 0.08 && t < (grupos[i + 1]?.ini ?? Infinity) - 0.05);
  if (gi < 0) return null;
  const grp = grupos[gi];
  // permanece legivel (minimo 1.1 s) e some nas pausas longas
  const ate = Math.min(Math.max(grp.fim + 0.6, grp.ini + 1.1), grupos[gi + 1]?.ini ?? Infinity);
  if (t > ate) return null;
  const linha = grp.idx;
  const entrada = interpolate(t - grp.ini, [-0.08, 0.14], [0, 1], clamp);
  const saida = interpolate(t, [ate - 0.12, ate], [1, 0], clamp);
  let atual = -1;
  linha.forEach((k) => { if (t >= palavras[k].inicio) atual = k; });
  return (
    <div style={{position: 'absolute', left: 36, right: 36, bottom, display: 'flex', justifyContent: 'center', zIndex: 15, opacity: entrada * saida}}>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          rowGap: 4,
          columnGap: 8,
          maxWidth: 1000,
          padding: '14px 26px',
          background: 'transparent',
          transform: `translateY(${(1 - entrada) * 16}px)`,
        }}
      >
        {linha.map((k) => {
          const p = palavras[k];
          const dita = t >= p.inicio;
          const ativa = k === atual;
          const pop = ativa ? 1 + 0.1 * Math.exp(-(t - p.inicio) * 10) : 1;
          return (
            <span
              key={k}
              style={{
                fontFamily: TEXTO,
                fontWeight: 800,
                fontSize: 56,
                lineHeight: 1.15,
                padding: '2px 14px',
                background: 'transparent',
                color: ativa ? T.acento : dita ? T.tinta : T.suave,
                WebkitTextStroke: T.claro ? '1px rgba(255,255,255,0.7)' : '1px rgba(0,0,0,0.65)',
                textShadow: T.claro ? '0 2px 4px rgba(255,255,255,0.8)' : '0 2px 4px rgba(0,0,0,0.75)',
                transform: `scale(${pop})`,
                display: 'inline-block',
              }}
            >
              {p.palavra}
            </span>
          );
        })}
      </div>
    </div>
  );
};
void norm;

const dataBR = (t: string) => t.replace(/(\d{4})-(\d{2})-(\d{2})/g, '$3/$2/$1');
// terco inferior de documentario: barra de cor + "FONTE" + nome e data
const FonteTag: React.FC<{texto: string}> = ({texto}) => {
  const frame = useCurrentFrame();
  const T = useTema();
  const o = interpolate(frame, [0, 12], [0, 1], clamp);
  const limpo = dataBR(texto).replace(/^fonte:\s*/i, '');
  return (
    <div style={{position: 'absolute', bottom: 520, left: 48, zIndex: 30, opacity: o, transform: `translateX(${(1 - o) * -40}px)`, display: 'flex', alignItems: 'stretch', maxWidth: 900}}>
      <div style={{width: 8, background: T.acento, borderRadius: 4}} />
      <div style={{padding: '8px 22px 10px', background: 'rgba(8,8,10,0.78)', borderRadius: '0 10px 10px 0'}}>
        <div style={{fontFamily: TEXTO, fontWeight: 800, fontSize: 19, letterSpacing: 4, color: T.acento, textTransform: 'uppercase'}}>Fonte</div>
        <div style={{fontFamily: TEXTO, fontWeight: 700, fontSize: 28, color: '#fff', lineHeight: 1.2}}>{limpo}</div>
      </div>
    </div>
  );
};
const CreditoFoto: React.FC<{texto: string; abaixo: boolean}> = ({texto, abaixo}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 10], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', bottom: abaixo ? 650 : 520, left: 48, zIndex: 30, opacity: o}}>
      <div style={{padding: '6px 18px', borderRadius: 8, background: 'rgba(8,8,10,0.72)', color: '#e8e8e4', fontFamily: TEXTO, fontWeight: 600, fontSize: 22, maxWidth: 900, lineHeight: 1.2}}>
        {texto}
      </div>
    </div>
  );
};
const AvisoRodape: React.FC<{texto: string}> = ({texto}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 12], [0, 0.85], clamp);
  return (
    <div style={{position: 'absolute', bottom: 250, left: 80, right: 150, textAlign: 'center', zIndex: 30, opacity: o, fontFamily: TEXTO, fontWeight: 600, fontSize: 24, color: '#b8b8b4', lineHeight: 1.25}}>
      {texto}
    </div>
  );
};

export const Showcase: React.FC<ShowcaseProps> = ({dados, audio, tempos, palavras}) => {
  const {fps} = useVideoConfig();
  const doc = (audio ?? {}).documentario !== false;
  const motionNovo=dados.edicao==='motion';
  // documentario: sempre escuro, mas cada video sorteia uma paleta escura (cor de destaque e tom de fundo proprios)
  const sementeP = dados.semente ?? 1;
  const paletaDoc = PALETAS[dados.paleta ?? '']?.modo === 'escuro' ? dados.paleta : PALETAS_ESCURAS[Math.floor(hash(sementeP * 2.3) * PALETAS_ESCURAS.length)];
  const T = resolverTema(doc ? {...dados, modo: 'escuro', paleta: paletaDoc, acento: undefined} : dados);
  const sem = dados.semente ?? 1;
  const variacao = {espelho: hash(sem * 1.7) > 0.5};
  const cfg = audio ?? {};
  const blocos = planejar(dados, fps, tempos);
  const total = duracaoTotal(dados, tempos, fps);
  const trans = escolherTransicoes(blocos.map((b) => b.c.tipo), sem, doc);
  const falando = !!dados.narrado && !!audio?.narracao;
  const bottomLegenda = dados.mascote?.ativo ? dados.mascote.rodape + (1080 * dados.mascote.tamanho / 100 * 450 / 360) + 35 : undefined;
  const pal = palavras ?? [];
  const grupos = React.useMemo(() => agruparPalavras(pal), [pal]);
  const falas: {ini: number; fim: number}[] = [];
  pal.forEach((p) => {
    const u = falas[falas.length - 1];
    if (u && p.inicio - u.fim < 0.4) u.fim = Math.max(u.fim, p.fim);
    else falas.push({ini: p.inicio, fim: p.fim});
  });
  const sons: {src: string; f: number; vol: number}[] = [];
  const entradasClassicas: number[][] = blocos.map((b, i) => {
    if (b.c.tipo !== 'classica') return [];
    const tp = tempos?.[i];
    const ini = tp ? tp.inicio : b.from / fps;
    const fim = tp ? tp.fim : (b.from + b.dur) / fps;
    return calcularEntradas(b.c.cena, ini, fim, pal, fps);
  });
  blocos.forEach((b, i) => {
    if (i > 0 && cfg.transicao !== false) sons.push({src: 'whoosh', f: b.from - 3, vol: 0.32});
    if (i === 0) { sons.push({src: 'drone', f: 0, vol: 0.5}); sons.push({src: 'subhit', f: 8, vol: 0.7}); }
    if (i > 0) sons.push({src: 'projetor', f: b.from - 1, vol: 0.22});
    if (b.dur > 135) sons.push({src: 'tick', f: b.from + Math.round(b.dur * 0.52), vol: 0.18});
    if (['fato_real', 'fato_documento', 'foto_polaroid', 'foto_card3d'].includes(b.c.tipo)) sons.push({src: b.c.tipo === 'fato_real' ? 'subhit' : 'papel', f: b.from + 4, vol: b.c.tipo === 'fato_real' ? 0.45 : 0.4});
    if (b.c.tipo === 'classica') {
      const cl = b.c.cena;
      const ent = entradasClassicas[i];
      if (TIPOS_COM_POP.includes(cl.tipo)) {
        (cl.elementos ?? []).forEach((el: {tipo: string}, k: number) =>
          sons.push({src: el.tipo === 'numero' ? 'tick' : 'pop', f: b.from + (ent[k] ?? 0), vol: 0.4}),
        );
      }
      if (cl.tipo === 'documento') sons.push({src: 'carimbo', f: b.from + Math.max(46, ent[2] ?? 0), vol: 0.85});
      if (cl.tipo === 'frase') sons.push({src: 'tick', f: b.from + Math.max(38, ent[0] ?? 0), vol: 0.5});
      if (cl.tipo === 'numero_gigante') {
        sons.push({src: 'impacto', f: b.from + 42, vol: 0.85});
        sons.push({src: 'brilho', f: b.from + 43, vol: 0.5});
      }
      return;
    }
    sonsDe(b.c, b.dur).forEach((s) => sons.push({src: s.src, f: b.from + s.f, vol: s.vol}));
  });
  const volMus = (f: number) => {
    const t = f / fps;
    let duck = 0;
    if (falando) {
      for (const b of falas) {
        if (t < b.ini - 0.3 || t > b.fim + 0.6) continue;
        duck = Math.max(duck, interpolate(t, [b.ini - 0.3, b.ini, b.fim, b.fim + 0.6], [0, 1, 1, 0], clamp));
      }
    }
    return (cfg.volumeMusica ?? 1) * (1 - 0.66 * duck) * interpolate(f, [0, 30, total - 36, total], [0, 1, 1, 0], clamp);
  };
  return (
    <TemaProvider value={T}>
      <VarProvider value={variacao}>
      <AbsoluteFill style={{background: T.bg, overflow: 'hidden'}}>
        {cfg.musica ? <Audio src={staticFile('musica.mp3')} loop volume={volMus} /> : null}
        {falando ? <Audio src={staticFile('narracao.wav')} volume={1} /> : null}
        {cfg.sfx !== false && !(dados.mascote?.ativo && dados.mascote.fundo === 'video')
          ? sons.map((s, i) => {
              const from = Math.max(0, s.f);
              return (
                <Sequence key={i} from={from} durationInFrames={90}>
                  <Audio src={staticFile(`sfx/${s.src}.wav`)} volume={Math.min(1, s.vol * (cfg.volumeSfx ?? 1) * (motionNovo ? .38 : 1))} />
                </Sequence>
              );
            })
          : null}
        {!(dados.mascote?.ativo && dados.mascote.fundo === 'video') ? <>
        <Camera grupos={grupos} ativo={doc && !motionNovo} batidas={blocos.filter((b) => b.dur > 135).map((b) => b.from + Math.round(b.dur * 0.52))}>
        {blocos.map((b, i) => (
          <Sequence key={i} from={b.from} durationInFrames={b.dur}>
            {b.c.tipo === 'classica' && !b.c.motion ? (
              <Guarda>
                <RenderCena cena={b.c.cena} n={i + 1} total={blocos.length} entradas={entradasClassicas[i] ?? []} titulo_={dados.titulo} />
              </Guarda>
            ) : (
              motionNovo ? <CorteMotion dur={b.dur} first={i===0} last={i===blocos.length-1} variant={b.c.motion?.corte??(i%4)}><Guarda>{b.c.motion?.layout==='original' && b.c.tipo==='classica'?<RenderCena cena={b.c.cena} n={i+1} total={blocos.length} entradas={entradasClassicas[i]??[]} titulo_={dados.titulo}/>:renderCena(b.c,b.dur)}</Guarda></CorteMotion> : <Envelope dur={b.dur} primeira={i === 0} ultima={i === blocos.length - 1} id={i} v={trans[i]}>
                <Guarda>{b.c.foto && !b.c.tipo.startsWith('foto_') && b.c.tipo !== 'fato_real' ? <FundoFotoUI c={b.c} dur={b.dur}>{renderCena(b.c, b.dur)}</FundoFotoUI> : renderCena(b.c, b.dur)}</Guarda>
              </Envelope>
            )}
          </Sequence>
        ))}
        {blocos.slice(1).map((b, i) =>
          !motionNovo && [0, 2, 3, 4].includes(trans[i + 1]) ? (
            <Sequence key={`f${i}`} from={b.from - 4} durationInFrames={24}>
              <Floracao em={4} />
            </Sequence>
          ) : null,
        )}
        {blocos.slice(1).map((b, i) =>
          !motionNovo && hash(sem + i * 7.7) > 0.9 && !doc ? (
            <Sequence key={`v${i}`} from={b.from - 6} durationInFrames={18}>
              <Varredura lado={i % 2 === 0 ? 1 : -1} />
            </Sequence>
          ) : null,
        )}
        </Camera>
        </> : null}
        {dados.mascote?.ativo ? <FundoMascote cfg={dados.mascote} blocos={blocos} total={total} /> : null}
        {blocos.map((b, i) =>
          dados.mostrar_fontes && b.c.fonte ? (
            <Sequence key={`fo${i}`} from={b.from + 14} durationInFrames={Math.max(10, b.dur - 20)}>
              <FonteTag texto={b.c.fonte} />
            </Sequence>
          ) : null,
        )}
        {blocos.map((b, i) =>
          dados.mostrar_fontes && b.c.credito ? (
            <Sequence key={`cr${i}`} from={b.from + 8} durationInFrames={Math.max(10, b.dur - 12)}>
              <CreditoFoto texto={b.c.credito} abaixo={!!b.c.fonte} />
            </Sequence>
          ) : null,
        )}
        {dados.aviso && blocos.length ? (
          <Sequence from={blocos[blocos.length - 1].from + 10} durationInFrames={blocos[blocos.length - 1].dur}>
            <AvisoRodape texto={dados.aviso} />
          </Sequence>
        ) : null}
        {dados.mascote?.ativo ? <ApresentadorMascote cfg={dados.mascote} blocos={blocos} palavras={pal} tempos={tempos} /> : null}
        {falando ? (motionNovo && !dados.mascote?.ativo ? <LegendaMotion palavras={pal} grupos={grupos} cor={dados.direcao_motion?.cor||dados.cenas[0]?.motion?.acento}/> : cfg.legenda === 'pilula' ? <Legenda palavras={pal} bottom={bottomLegenda} /> : <LegendaDoc palavras={pal} grupos={grupos} bottom={bottomLegenda} />) : null}
        <Marca texto={dados.marca} />
        {motionNovo ? null : doc && !dados.mascote?.ativo ? <Acabamento cortes={blocos.slice(1).map((b) => b.from)} serio={(dados.modo as string) === 'serio'} /> : <Grao />}
        {doc ? <Progresso total={total} cortes={blocos.slice(1).map((b) => b.from)} /> : null}
      </AbsoluteFill>
    </VarProvider>
    </TemaProvider>
  );
};
