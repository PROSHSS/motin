import type {ConfigMascote} from '../Mascote';
import React, {createContext, useContext} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

// ---------------------------------------------------------------------
// TIPOS DO ROTEIRO (showcase.json)
// ---------------------------------------------------------------------
export type Parte = {t: string; e: 'forte' | 'fina' | 'serifa' | 'mini'; tam?: number};
export type Linha = Parte[];
export type MidiaMotion={arquivo:string;inicio:number;fim:number;duracao:number};
export type BatidaMotion={texto:string;em:number;icone:string};
export type PlanoMotion={intencao?:string;intensidade?:string;foco?:number;densidade?:number;movimento?:number;variante?:number;dominio?:string;acao?:string;acento?:string;corte?:number;camera?:number;velocidade?:number;objetos?:{texto:string;icone:string;em:number}[];layout:string;claro:boolean;indice:number;titulo:string;chaves:string[];icone:string;batidas:BatidaMotion[];duracao:number;legendas?:boolean;versao:string};
export type CenaSC = {
  video?:MidiaMotion;
  motion?:PlanoMotion;
  tipo: 'gancho' | 'celular' | 'lupa' | 'processo' | 'grafico' | 'rajada' | 'checklist' | 'fecho' | 'comparacao' | 'contador' | 'ranking' | 'linha_tempo' | 'alerta' | 'citacao' | 'classica'
    | 'foto_hero' | 'foto_celular' | 'foto_lupa' | 'foto_polaroid' | 'foto_recorte' | 'foto_persianas' | 'foto_card3d' | 'fato_real' | 'fato_documento'
    | 'cartaz' | 'foto_moldura' | 'busca' | 'pilula' | 'glitch' | 'pasta';
  foto?: string; // arquivo da imagem gerada (ex: img_3.jpg)
  chips?: {texto: string; valor?: string}[];
  rotulo?: string;
  titulo?: string; // fato_real: nome/assunto em letra grande
  linhas?: string[]; // fato_real: explicacao linha por linha (vem da narracao)
  palavras?: string[]; realce?: number[]; tags?: string[]; consulta?: string; resultados?: string[]; destaque?: string; palavra?: string; cartoes?: string[];
  objeto?: string; // fato_real: imagem do objeto real (cedula, documento...)
  recorte?: string; // fato_real: PNG do retrato sem fundo (opcional)
  documento?: {fonte: string; data?: string; trecho: string; destaques?: string[]; selo: string};
  numero?: {prefixo?: string; valor: number; decimais?: number; sufixo?: string; rotulo?: string};
  acento?: string; // cor extraida da foto
  fonte?: string; // ex: 'TSE, 26/10/2026'
  credito?: string; // credito da foto (autor/licenca) ou 'Imagem ilustrativa (IA)'
  narracao?: string;
  cena?: any; // cena do estilo classico (tipo 'classica')
  duracao: number; // segundos
  fantasma?: string;
  manchete?: Linha[];
  etiqueta?: {texto: string; sub?: string};
  notificacoes?: {icone: string; titulo: string; texto: string}[];
  lupa?: {preco: string; rotulo?: string};
  processo?: {rotulo: string; campo: string; de: string; para: string; badge: string; final: string; botao: string};
  grafico?: {rotulo: string; valores: number[]; marcadores: {i: number; texto: string}[]; botao: string};
  rajada?: {icone: string; texto: string}[];
  checklist?: string[];
  fecho?: {pergunta: string; cta: string};
  variante?: string; // gancho: etiqueta | carimbo | digitando
  comparacao?: {a: {titulo: string; valor: string; itens: string[]}; b: {titulo: string; valor: string; itens: string[]}; vencedor: 'a' | 'b'};
  contador?: {rotulo: string; de?: number; para: number; prefixo?: string; sufixo?: string; legenda?: string};
  ranking?: {titulo?: string; itens: {nome: string; valor: number; texto?: string}[]};
  linha_tempo?: {ano: string; texto: string}[];
  alerta?: {titulo: string; texto: string; selo?: string};
  citacao?: {texto: string; autor?: string};
};
export type Dados = {
  edicao?:'motion'|'anterior';
  direcao_motion?:{id:string;versao:string;semente:number;dominio:string;cor?:string};
  mascote?: ConfigMascote;
  mostrar_fontes?: boolean; // false (padrao): sem etiquetas de fonte/foto sobre a imagem
  titulo: string;
  fps?: number;
  paleta?: string;
  semente?: number;
  narrado?: boolean;
  aviso?: string; // linha pequena no fim (ex: conteudo informativo)
  acento?: string;
  modo?: 'claro' | 'escuro';
  marca?: string;
  cenas: CenaSC[];
};

// ---------------------------------------------------------------------
// TEMA
// ---------------------------------------------------------------------
const CLARO = {
  bg: '#f4f3ef',
  tinta: '#121212',
  suave: '#6d6c68',
  fantasma: 'rgba(110,110,104,0.16)',
  cartao: '#ffffff',
  cartaoTinta: '#16161a',
  esfA: '#fbfbf9',
  esfB: '#d6d6d2',
  esfC: '#aeaeaa',
  sombra: 'rgba(20,20,20,0.22)',
  linha: '#dcdbd6',
  claro: true,
};
const ESCURO = {
  bg: '#0d0d0f',
  tinta: '#f4f3ef',
  suave: '#9a9994',
  fantasma: 'rgba(255,255,255,0.07)',
  cartao: '#1b1b1f',
  cartaoTinta: '#f4f3ef',
  esfA: '#34343a',
  esfB: '#1d1d21',
  esfC: '#131316',
  sombra: 'rgba(0,0,0,0.55)',
  linha: '#2c2c31',
  claro: false,
};
export type Tema = typeof CLARO & {acento: string; acentoClaro: string; acentoEscuro: string; sobreAcento: string; alerta: string; ok: string};

const misturar = (hex: string, alvo: string, p: number) => {
  const l = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const a = l(hex);
  const c = l(alvo);
  return '#' + a.map((v, i) => Math.round(v + (c[i] - v) * p).toString(16).padStart(2, '0')).join('');
};
const lum = (hex: string) => {
  const [r, g, bl] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * bl;
};

// Paletas prontas (cada tema pode usar uma diferente)
export const PALETAS: Record<string, {modo: 'claro' | 'escuro'; acento: string; bg: string; esf: [string, string, string]}> = {
  ouro: {modo: 'claro', acento: '#c9a24a', bg: '#f4f3ef', esf: ['#fbfbf9', '#d6d6d2', '#aeaeaa']},
  oceano: {modo: 'claro', acento: '#2f6bff', bg: '#eef2f8', esf: ['#fbfdff', '#d3dbe8', '#a9b6cc']},
  rubi: {modo: 'claro', acento: '#e2342a', bg: '#f7f0ee', esf: ['#fffaf9', '#e6d6d2', '#c9aca6']},
  menta: {modo: 'claro', acento: '#12a37f', bg: '#eef5f2', esf: ['#fbfffd', '#d1e2db', '#a5bdb3']},
  lavanda: {modo: 'claro', acento: '#7a5cff', bg: '#f2f0f8', esf: ['#fdfcff', '#dad5ea', '#b2aacb']},
  laranja: {modo: 'claro', acento: '#ff7a1a', bg: '#f8f1ea', esf: ['#fffbf7', '#ead9c8', '#cdb59c']},
  neon: {modo: 'escuro', acento: '#3df5a0', bg: '#0b0d0c', esf: ['#2f3a35', '#1a201d', '#101412']},
  ambar: {modo: 'escuro', acento: '#ffb020', bg: '#0e0d0b', esf: ['#3a352b', '#1f1c16', '#121110']},
  ciano: {modo: 'escuro', acento: '#35d0ff', bg: '#0a0e12', esf: ['#2a3944', '#161f27', '#0e1419']},
  grafite: {modo: 'escuro', acento: '#f4f3ef', bg: '#0d0d0f', esf: ['#34343a', '#1d1d21', '#131316']},
  // paletas escuras de documentario (cada video sorteia uma: o fundo ganha um tom proprio)
  vermelho: {modo: 'escuro', acento: '#ff4338', bg: '#110a0a', esf: ['#3f2321', '#221312', '#140b0b']},
  verde: {modo: 'escuro', acento: '#2fe38a', bg: '#08100c', esf: ['#1f3a2c', '#12231a', '#0a140f']},
  laranjaesc: {modo: 'escuro', acento: '#ff8a1f', bg: '#100c08', esf: ['#3d2c1a', '#221810', '#140f0a']},
  azul: {modo: 'escuro', acento: '#4a8dff', bg: '#080b12', esf: ['#1f2c46', '#121a2b', '#0a0f19']},
  amarelo: {modo: 'escuro', acento: '#ffd60a', bg: '#0f0e08', esf: ['#3d3a18', '#222010', '#14130a']},
  violeta: {modo: 'escuro', acento: '#a779ff', bg: '#0c0912', esf: ['#2d2347', '#1a1429', '#0f0b18']},
};
export const PALETAS_ESCURAS = ['vermelho', 'verde', 'laranjaesc', 'azul', 'amarelo', 'violeta', 'neon', 'ambar', 'ciano'];
export const montarTema = (modo: 'claro' | 'escuro', acento: string, paleta?: string): Tema => {
  const P = paleta ? PALETAS[paleta] : undefined;
  const base = modo === 'escuro' ? ESCURO : CLARO;
  // acento sempre legivel sobre o fundo (cor extraida de foto escura sumia no fundo escuro)
  let ac = acento;
  if (modo === 'escuro' && lum(ac) < 0.3) ac = misturar(ac, '#ffffff', 0.45);
  if (modo === 'claro' && lum(ac) > 0.78) ac = misturar(ac, '#000000', 0.4);
  return {
    ...base,
    // cores de fundo da paleta SO quando combinam com o modo (paleta clara em modo escuro dava texto claro sobre fundo claro)
    ...(P && P.modo === modo ? {bg: P.bg, esfA: P.esf[0], esfB: P.esf[1], esfC: P.esf[2]} : {}),
    acento: ac,
    acentoClaro: misturar(ac, '#ffffff', 0.78),
    acentoEscuro: misturar(ac, '#000000', 0.55),
    sobreAcento: lum(ac) > 0.5 ? '#16130a' : '#ffffff',
    alerta: '#e2342a',
    ok: '#2fbf6b',
  };
};
export const resolverTema = (d: {paleta?: string; modo?: 'claro' | 'escuro'; acento?: string}): Tema => {
  const P = d.paleta ? PALETAS[d.paleta] : undefined;
  return montarTema(d.modo ?? P?.modo ?? 'claro', d.acento ?? P?.acento ?? '#c9a24a', P ? d.paleta : undefined);
};

// Variação por semente: espelha a posição das esferas, etc.
export type Variacao = {espelho: boolean};
const VarCtx = createContext<Variacao>({espelho: false});
export const VarProvider = VarCtx.Provider;
export const useVar = () => useContext(VarCtx);
export const hash = (n: number) => {
  const v = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return v - Math.floor(v);
};

const Ctx = createContext<Tema>(montarTema('claro', '#c9a24a'));
export const TemaProvider = Ctx.Provider;
export const useTema = () => useContext(Ctx);

export const FORTE = "'Arial Black', 'Segoe UI Black', 'Helvetica Neue', Impact, sans-serif";
export const FINA = "'Segoe UI Light', 'Helvetica Neue', Arial, sans-serif";
export const SERIFA = "Georgia, 'Times New Roman', serif";
export const TEXTO = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif";

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const expoOut = (t: number) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));

export const useMola = (inicio: number, tipo: 'suave' | 'viva' | 'salto' = 'viva') => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({
    frame: frame - inicio,
    fps,
    config:
      tipo === 'suave'
        ? {damping: 22, stiffness: 90, mass: 0.9}
        : tipo === 'salto'
          ? {damping: 9, stiffness: 150, mass: 0.7}
          : {damping: 14, stiffness: 130, mass: 0.8},
  });
};

// ---------------------------------------------------------------------
// ESFERA (círculo grande com luz suave que "floresce" e deriva)
// ---------------------------------------------------------------------
export const Esfera: React.FC<{
  x: number;
  y: number;
  r: number;
  inicio?: number;
  deriva?: number;
  opac?: number;
}> = ({x, y, r, inicio = 0, deriva = 18, opac = 1}) => {
  const T = useTema();
  const V = useVar();
  if (V.espelho) x = 1080 - x;
  const frame = useCurrentFrame();
  const e = spring({frame: frame - inicio, fps: 30, config: {damping: 20, stiffness: 70, mass: 1.1}});
  const dx = Math.sin(frame / 55 + x) * deriva;
  const dy = Math.cos(frame / 61 + y) * deriva;
  return (
    <div
      style={{
        position: 'absolute',
        left: x - r + dx,
        top: y - r + dy,
        width: r * 2,
        height: r * 2,
        borderRadius: '50%',
        background: `radial-gradient(circle at 32% 28%, ${T.esfA} 0%, ${T.esfB} 58%, ${T.esfC} 100%)`,
        transform: `scale(${Math.max(0, e)})`,
        opacity: opac,
        boxShadow: `0 40px 90px ${T.sombra}`,
      }}
    />
  );
};

// pontinhos de órbita (decoração)
export const Pontos: React.FC<{x: number; y: number; inicio?: number}> = ({x, y, inicio = 4}) => {
  const T = useTema();
  const e = useMola(inicio, 'salto');
  return (
    <>
      {[
        {dx: 0, dy: 0, s: 54},
        {dx: 86, dy: 70, s: 34},
        {dx: 150, dy: 18, s: 22},
      ].map((p, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: x + p.dx,
            top: y + p.dy,
            width: p.s,
            height: p.s,
            borderRadius: '50%',
            background: i === 1 ? T.tinta : i === 0 ? T.esfC : T.esfB,
            opacity: 0.8,
            transform: `scale(${Math.max(0, useMolaFixa(e, i))})`,
          }}
        />
      ))}
    </>
  );
};
const useMolaFixa = (e: number, i: number) => Math.min(1.1, Math.max(0, e - i * 0.06));

// ---------------------------------------------------------------------
// PALAVRA FANTASMA (grande, clarinha, atrás do objeto)
// ---------------------------------------------------------------------
export const PalavraFantasma: React.FC<{texto: string; top: number; tam?: number; inicio?: number}> = ({
  texto,
  top,
  tam = 420,
  inicio = 0,
}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  const e = spring({frame: frame - inicio, fps: 30, config: {damping: 24, stiffness: 70, mass: 1}});
  const fator = Math.min(1, 1000 / (texto.length * tam * 0.62));
  const t = tam * fator;
  return (
    <div
      data-guarda="ignorar"
      style={{
        position: 'absolute',
        top,
        left: 0,
        right: 0,
        textAlign: 'center',
        fontFamily: FORTE,
        fontSize: t,
        lineHeight: 1,
        letterSpacing: -t * 0.03,
        color: T.fantasma,
        opacity: e,
        filter: `blur(${interpolate(e, [0, 1], [18, 0])}px)`,
        transform: `translateY(${interpolate(e, [0, 1], [70, 0])}px) scale(${1 + frame * 0.0009})`,
        whiteSpace: 'nowrap',
      }}
    >
      {texto}
    </div>
  );
};

// ---------------------------------------------------------------------
// MANCHETE: linhas com estilos misturados (forte / fina / serifa / mini)
// ---------------------------------------------------------------------
export const Manchete: React.FC<{linhas: Linha[]; top: number; inicio?: number; alinhar?: 'centro' | 'esquerda'}> = ({
  linhas,
  top,
  inicio = 6,
  alinhar = 'centro',
}) => {
  const T = useTema();
  const frame = useCurrentFrame();
  let contador = 0;
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: 70,
        right: 70,
        display: 'flex',
        flexDirection: 'column',
        alignItems: alinhar === 'centro' ? 'center' : 'flex-start',
        gap: 4,
        zIndex: 4,
      }}
    >
      {linhas.map((linha, li) => (
        <div key={li} style={{display: 'flex', alignItems: 'baseline', justifyContent: alinhar === 'centro' ? 'center' : 'flex-start', gap: '0 18px', flexWrap: 'wrap', maxWidth: 940}}>
          {linha.map((p, pi) => {
            const ini = inicio + contador * 4;
            contador += 1;
            const e = spring({frame: frame - ini, fps: 30, config: {damping: 14, stiffness: 120, mass: 0.8}});
            const op = interpolate(e, [0, 0.6], [0, 1], clamp);
            const estilo: React.CSSProperties =
              p.e === 'forte'
                ? {fontFamily: FORTE, fontWeight: 900, fontSize: p.tam ?? 112, letterSpacing: -2, textTransform: 'uppercase', color: T.tinta}
                : p.e === 'fina'
                  ? {fontFamily: FINA, fontWeight: 300, fontSize: p.tam ?? 84, color: T.tinta}
                  : p.e === 'serifa'
                    ? {fontFamily: SERIFA, fontStyle: 'italic', fontWeight: 400, fontSize: p.tam ?? 96, color: T.tinta}
                    : {fontFamily: TEXTO, fontWeight: 800, fontSize: p.tam ?? 40, letterSpacing: 5, textTransform: 'uppercase', color: T.suave};
            // largura estimada: palavra que nao cabe numa linha pode quebrar; as demais NUNCA quebram no meio (ordem de leitura fica certa)
            const tamF = Number(estilo.fontSize ?? 60);
            const larg = p.t.length * tamF * (p.e === 'forte' ? 0.66 : 0.52);
            return (
              <span
                key={pi}
                style={{
                  display: 'inline-block',
                  whiteSpace: larg > 930 ? 'normal' : 'nowrap',
                  maxWidth: 940,
                  textAlign: alinhar === 'centro' ? 'center' : 'left',
                  lineHeight: 1.04,
                  opacity: op,
                  transform: `translateY(${interpolate(e, [0, 1], [46, 0])}px) scale(${interpolate(e, [0, 1], [0.94, 1])})`,
                  filter: `blur(${interpolate(e, [0, 1], [12, 0], clamp)}px)`,
                  ...estilo,
                }}
              >
                {p.t}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// ---------------------------------------------------------------------
// MARCA (pílula no canto inferior esquerdo, como a referência)
// ---------------------------------------------------------------------
export const Marca: React.FC<{texto?: string}> = ({texto}) => {
  const T = useTema();
  if (!texto) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 48,
        bottom: 70,
        zIndex: 20,
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '10px 26px 10px 10px',
        borderRadius: 60,
        background: T.claro ? 'rgba(120,120,116,0.72)' : 'rgba(255,255,255,0.14)',
        backdropFilter: 'blur(6px)',
      }}
    >
      <div style={{width: 52, height: 52, borderRadius: '50%', background: `linear-gradient(135deg, ${T.acento}, #1d2a55)`}} />
      <div style={{fontFamily: TEXTO, fontWeight: 700, fontSize: 26, color: '#fff', letterSpacing: 0.5}}>{texto}</div>
    </div>
  );
};

// ---------------------------------------------------------------------
// GRÃO suave
// ---------------------------------------------------------------------
export const Grao: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity: 0.05, pointerEvents: 'none', mixBlendMode: 'multiply'}}>
      <svg width="1080" height="1920" viewBox="0 0 360 640" preserveAspectRatio="none">
        <filter id="g">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="1" seed={Math.floor(frame / 2) % 40} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="360" height="640" filter="url(#g)" />
      </svg>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------
// ABERRAÇÃO CROMÁTICA nos cortes (franjas vermelha/azul por poucos quadros)
// ---------------------------------------------------------------------
export const aberracao = (frame: number, dur: number, entrada = 7, saida = 5) => {
  const a = interpolate(frame, [0, entrada], [9, 0], clamp);
  const b = interpolate(frame, [dur - saida, dur], [0, 7], clamp);
  return Math.max(a, b);
};
export const filtroAberracao = (amp: number) =>
  amp > 0.35
    ? `drop-shadow(${amp}px 0 0 rgba(255,40,90,0.55)) drop-shadow(${-amp}px 0 0 rgba(0,190,255,0.55))`
    : undefined;

// sombra suave padrão dos objetos
export const sombraObjeto = (T: Tema, alt = 1) =>
  `0 ${30 * alt}px ${60 * alt}px ${T.sombra}, 0 ${6 * alt}px ${14 * alt}px rgba(0,0,0,0.12)`;
