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
import * as Lucide from 'lucide-react';
import {
  CenaCinetica,
  CenaSilhuetas,
  CenaDocumento,
  CenaVersus,
  CenaLinhaTempo,
  FundoFoto,
} from './CenasNovas';
import {
  CenaGraficoBarras,
  CenaGraficoLinha,
  CenaRosca,
  CenaNumeroGigante,
  CenaRanking,
} from './CenasDados';
import {Segmentos, Flutuantes} from './Efeitos';
import {CenaFrase, CenaListaCaixas, CenaPainel, fundoDaCena} from './CenasEstilo';
import {CenaCitacao, CenaChecklist, CenaAlerta, Particulas, ChamadaFinal} from './CenasExtras';

// ---------- TIPOS ----------
type Elemento = {
  tipo: string; // icone | numero | lista
  texto: string;
  icone?: string;
  gatilho?: string; // palavra da narração que faz o elemento aparecer
};
export type Cena = {
  narracao: string;
  tipo: string;
  destaque: string;
  imagem?: string;
  elementos?: Elemento[];
};
type Tempo = {cena: number; inicio: number; fim: number};
type Palavra = {palavra: string; inicio: number; fim: number};
export type ConfigAudio = {
  musica: boolean;
  sfx: boolean;
  volumeMusica: number;
  volumeSfx?: number;
  transicao?: boolean;
};
export type ConfigVisual = {cta?: string; marca?: string};
export type VideoProps = {
  roteiro: {titulo: string; cenas: Cena[]};
  tempos: Tempo[];
  palavras: Palavra[];
  audio?: ConfigAudio;
  visual?: ConfigVisual;
};

// ---------- ESTILO ----------
const BG = '#0a0a0c';
const FG = '#f2efe6';
const MUDO = '#6b6b70';
const ACENTO = '#c9a24a';
const SERIF = "Georgia, 'Times New Roman', serif";
const MONO = "Consolas, 'Courier New', monospace";
const SANS = "'Segoe UI', Arial, sans-serif";

// cores de acento que alternam por cena (dá a sensação de blocos de cor)
const PALETA = ['#c9a24a', '#4aa3c9', '#c9604a', '#6cc98a'];

// ---------- UTILIDADES ----------
const norm = (t: string) =>
  t
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]/g, '');

// extrai o primeiro número de um texto ("47,03%" -> 47.03; "3/5" -> 60)
const numero = (t: string): number | null => {
  const f = t.match(/(\d+)\s*\/\s*(\d+)/);
  if (f) return (parseInt(f[1], 10) / parseInt(f[2], 10)) * 100;
  const m = t.replace(/\./g, '').match(/(\d+(?:,\d+)?)/);
  return m ? parseFloat(m[1].replace(',', '.')) : null;
};

const useEntrada = (atraso = 0) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - atraso, fps, config: {damping: 200}});
};

const IconeLucide: React.FC<{nome?: string; size: number; color: string}> = ({
  nome,
  size,
  color,
}) => {
  const Comp = (Lucide as any)[nome ?? ''] ?? (Lucide as any).Circle;
  return <Comp size={size} color={color} strokeWidth={1.8} />;
};

// ---------- CENAS ----------
const Rotulo: React.FC<{n: number; total: number; tipo: string; claro?: boolean}> = ({
  n,
  total,
  tipo,
  claro,
}) => (
  <div
    style={{
      position: 'absolute',
      zIndex: 5,
      top: 90,
      left: 70,
      right: 70,
      display: 'flex',
      justifyContent: 'space-between',
      fontFamily: MONO,
      fontSize: 28,
      letterSpacing: 3,
      color: claro ? '#77736a' : MUDO,
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

const CenaTexto: React.FC<{destaque: string; cor: string}> = ({destaque, cor}) => {
  const e = useEntrada();
  const y = interpolate(e, [0, 1], [40, 0]);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: 80}}>
      <div
        style={{
          fontFamily: SERIF,
          fontStyle: 'italic',
          fontSize: destaque.length > 24 ? 92 : 130,
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
          background: cor,
        }}
      />
    </AbsoluteFill>
  );
};

const CenaBarras: React.FC<{destaque: string; cor: string}> = ({destaque, cor}) => {
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
            background: '#e9e4d4',
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

const CenaHemiciclo: React.FC<{destaque: string; cor: string}> = ({destaque, cor}) => {
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
  const limite = Math.PI * frac * prog;
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
            fill={p.ang <= limite ? cor : '#2c2c31'}
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

const CenaImagem: React.FC<{destaque: string; imagem: string; gancho?: boolean; n?: number}> = ({
  destaque,
  imagem,
  gancho,
  n = 1,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const e = useEntrada(6);
  const dir = n % 2 === 0 ? -1 : 1;
  const zoom = interpolate(frame, [0, durationInFrames], dir > 0 ? [1.0, 1.18] : [1.18, 1.0]);
  const deslocaX = interpolate(frame, [0, durationInFrames], [0, -24 * dir]);
  const giro = interpolate(frame, [0, durationInFrames], [-0.9 * dir, 0.9 * dir]);
  // texto digitado letra por letra (no gancho, mais rápido e com soco de escala)
  const letras = Math.min(destaque.length, Math.floor(Math.max(0, frame - 4) * (gancho ? 1.6 : 1.1)));
  const textoVisivel = destaque.slice(0, letras);
  const soco = gancho ? 1 + 0.16 * Math.exp(-Math.max(0, frame - 3) * 0.2) : 1;
  const flash = gancho ? interpolate(frame, [0, 7], [0.7, 0], {extrapolateRight: 'clamp'}) : 0;
  const tremeX = Math.sin(frame / 7.3) * 4 + Math.sin(frame / 3.1) * 1.5;
  const tremeY = Math.cos(frame / 8.9) * 4 + Math.cos(frame / 3.7) * 1.5;
  const vazaX = interpolate(frame, [0, durationInFrames], [-40, 140]);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile(imagem)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${zoom * 1.03}) translate(${deslocaX + tremeX}px, ${tremeY}px) rotate(${giro}deg)`,
          }}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(to bottom, rgba(10,10,12,0.5) 0%, rgba(10,10,12,0.05) 35%, rgba(10,10,12,0.12) 60%, rgba(10,10,12,0.78) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 230,
          left: 70,
          right: 70,
          textAlign: 'center',
          fontFamily: SERIF,
          fontStyle: 'italic',
          fontSize: (destaque.length > 24 ? 84 : 118) * (gancho ? 1.12 : 1),
          lineHeight: 1.1,
          color: FG,
          opacity: e,
          transform: `scale(${soco})`,
          textShadow: '0 4px 24px rgba(0,0,0,0.7)',
        }}
      >
        {textoVisivel}
        <span style={{opacity: letras < destaque.length ? 0.9 : 0, color: ACENTO}}>|</span>
      </div>
      <AbsoluteFill
        style={{
          background: `linear-gradient(105deg, transparent ${vazaX - 30}%, rgba(255,170,90,0.28) ${vazaX}%, transparent ${vazaX + 30}%)`,
          mixBlendMode: 'screen',
          pointerEvents: 'none',
        }}
      />
      {gancho ? (
        <AbsoluteFill style={{background: '#fff', opacity: flash, pointerEvents: 'none'}} />
      ) : null}
    </AbsoluteFill>
  );
};

// ---------- CENA EXPLICATIVA (ícones, números e listas que aparecem na fala) ----------
type Slot = {el: Elemento; entra: number; x: number; y: number; raio: number};

const AREA_TOPO = 330;
const AREA_ALTURA = 1020;

const CenaExplicativa: React.FC<{
  destaque: string;
  elementos: Elemento[];
  entradas: number[]; // frame (dentro da cena) em que cada elemento aparece
  cor: string;
}> = ({destaque, elementos, entradas, cor}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const n = Math.max(1, elementos.length);
  const slotH = AREA_ALTURA / n;
  const slots: Slot[] = elementos.map((el, i) => {
    const y = AREA_TOPO + slotH * (i + 0.5);
    if (el.tipo === 'icone') {
      return {el, entra: entradas[i], x: i % 2 === 0 ? 290 : 790, y, raio: 105};
    }
    if (el.tipo === 'numero') return {el, entra: entradas[i], x: 540, y, raio: 90};
    return {el, entra: entradas[i], x: 540, y, raio: 60};
  });

  const titulo = useEntrada(2);

  return (
    <AbsoluteFill>
      {/* título da cena */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 70,
          right: 70,
          textAlign: 'center',
          fontFamily: SERIF,
          fontStyle: 'italic',
          fontSize: destaque.length > 22 ? 70 : 92,
          color: FG,
          opacity: titulo,
          transform: `translateY(${interpolate(titulo, [0, 1], [-30, 0])}px)`,
        }}
      >
        {destaque}
      </div>

      {/* linhas que ligam um elemento ao próximo */}
      <svg
        width={1080}
        height={1920}
        style={{position: 'absolute', left: 0, top: 0}}
        viewBox="0 0 1080 1920"
      >
        {slots.slice(1).map((s, i) => {
          const a = slots[i];
          const x1 = a.x;
          const y1 = a.y + a.raio + 8;
          const x2 = s.x;
          const y2 = s.y - s.raio - 8;
          const p = interpolate(frame, [s.entra - 8, s.entra + 10], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <path
              key={i}
              d={`M ${x1} ${y1} C ${x1} ${y1 + 90}, ${x2} ${y2 - 90}, ${x2} ${y2}`}
              fill="none"
              stroke={cor}
              strokeOpacity={0.55}
              strokeWidth={4}
              strokeLinecap="round"
              strokeDasharray="1"
              strokeDashoffset={1 - p}
              pathLength={1}
            />
          );
        })}
      </svg>

      {/* elementos */}
      {slots.map((s, i) => {
        const e = spring({
          frame: frame - s.entra,
          fps,
          config: {damping: 14, stiffness: 140, mass: 0.7},
        });
        const op = interpolate(frame, [s.entra, s.entra + 6], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        if (frame < s.entra - 1) return null;
        const el = s.el;

        if (el.tipo === 'numero') {
          const alvo = numero(el.texto) ?? 0;
          const casas = (el.texto.match(/,(\d+)/)?.[1] ?? '').length;
          const prog = interpolate(frame, [s.entra, s.entra + 28], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const atual = (alvo * prog).toFixed(casas).replace('.', ',');
          const texto = el.texto.replace(/\d+(?:,\d+)?/, atual);
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: 0,
                right: 0,
                top: s.y - 90,
                textAlign: 'center',
                fontFamily: SERIF,
                fontWeight: 700,
                fontSize: 150,
                color: FG,
                opacity: op,
                transform: `scale(${interpolate(e, [0, 1], [0.6, 1])})`,
              }}
            >
              <span style={{borderBottom: `6px solid ${cor}`, paddingBottom: 6}}>{texto}</span>
            </div>
          );
        }

        if (el.tipo === 'lista') {
          const dx = interpolate(e, [0, 1], [-120, 0]);
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: 110,
                right: 90,
                top: s.y - 55,
                height: 110,
                display: 'flex',
                alignItems: 'center',
                gap: 28,
                opacity: op,
                transform: `translateX(${dx}px)`,
              }}
            >
              <div
                style={{
                  width: 84,
                  height: 84,
                  borderRadius: 18,
                  background: cor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <IconeLucide nome={el.icone ?? 'Check'} size={52} color={BG} />
              </div>
              <div
                style={{
                  fontFamily: SANS,
                  fontWeight: 700,
                  fontSize: 58,
                  lineHeight: 1.1,
                  color: FG,
                }}
              >
                {el.texto}
              </div>
            </div>
          );
        }

        // ícone com rótulo (zig-zag esquerda/direita)
        const esquerda = s.x < 540;
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: 'absolute',
                left: s.x - s.raio,
                top: s.y - s.raio,
                width: s.raio * 2,
                height: s.raio * 2,
                borderRadius: '50%',
                border: `5px solid ${cor}`,
                background: `${cor}22`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: op,
                transform: `scale(${interpolate(e, [0, 1], [0.2, 1])}) rotate(${interpolate(e, [0, 1], [-25, 0])}deg)`,
                boxShadow: `0 0 60px ${cor}44`,
              }}
            >
              <IconeLucide nome={el.icone} size={110} color={cor} />
            </div>
            <div
              style={{
                position: 'absolute',
                top: s.y - 70,
                height: 140,
                display: 'flex',
                alignItems: 'center',
                justifyContent: esquerda ? 'flex-start' : 'flex-end',
                left: esquerda ? s.x + s.raio + 40 : 60,
                right: esquerda ? 60 : 1080 - (s.x - s.raio - 40),
                textAlign: esquerda ? 'left' : 'right',
                fontFamily: SANS,
                fontWeight: 700,
                fontSize: 58,
                lineHeight: 1.1,
                color: FG,
                opacity: op,
                transform: `translateX(${interpolate(e, [0, 1], [esquerda ? -50 : 50, 0])}px)`,
              }}
            >
              {el.texto}
            </div>
          </React.Fragment>
        );
      })}
      <div style={{display: 'none'}}>{durationInFrames}</div>
    </AbsoluteFill>
  );
};

const NomeTipo: Record<string, string> = {
  texto: 'Contexto',
  barras: 'Números',
  hemiciclo: 'Distribuição',
  imagem: 'Contexto',
  explicativa: 'Entenda',
  cinetica: 'Destaque',
  silhuetas: 'Pessoas',
  documento: 'Regra',
  versus: 'Comparação',
  linha_tempo: 'Cronologia',
  grafico_barras: 'Dados',
  grafico_linha: 'Evolução',
  rosca: 'Proporção',
  numero_gigante: 'Número',
  ranking: 'Ranking',
  citacao: 'Citação',
  checklist: 'Checklist',
  alerta: 'Alerta',
  frase: 'Ideia',
  lista_caixas: 'Lista',
  painel: 'Painel',
};

// estilos que desenham o próprio fundo (sem a bolha de cor padrão)
const clamp01 = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const TIPOS_DADOS = ['grafico_barras', 'grafico_linha', 'rosca', 'numero_gigante', 'ranking'];
const TIPOS_EXTRAS = ['citacao', 'checklist', 'alerta', 'frase', 'lista_caixas', 'painel'];
const ESTILOS_PROPRIOS = ['cinetica', 'silhuetas', 'documento', 'versus', 'linha_tempo', ...TIPOS_DADOS, ...TIPOS_EXTRAS];
const ROTULO_CLARO = ['cinetica', 'versus'];

// ---------- TRANSIÇÃO + FUNDO DE CADA CENA ----------
export const RenderCena: React.FC<{
  cena: Cena;
  n: number;
  total: number;
  entradas: number[];
  titulo_: string;
}> = ({cena, n, total, entradas, titulo_}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const cor = PALETA[(n - 1) % PALETA.length];

  const T = 8; // duração da transição em frames
  const variante = n % 8; // 0 desfoque | 1 zoom | 2 deslize | 3 flash | 4 glitch | 5 íris | 6 cortina | 7 onda de cor
  const pEnt = interpolate(frame, [0, T], [0, 1], {extrapolateRight: 'clamp'});
  let transf = '';
  if (variante === 1) transf = `scale(${interpolate(pEnt, [0, 1], [1.4, 1])})`;
  if (variante === 2) transf = `translateX(${interpolate(pEnt, [0, 1], [220, 0])}px)`;
  if (variante === 4 && frame < 10)
    transf = `translateX(${Math.sin(frame * 7.3) * 30}px) skewX(${Math.sin(frame * 5.1) * 4}deg)`;
  let recorte: string | undefined;
  if (variante === 5) {
    const r = interpolate(frame, [0, 16], [0, 80], {extrapolateRight: 'clamp'});
    recorte = `circle(${r}% at 50% 50%)`;
  }
  if (variante === 6) {
    const r = interpolate(frame, [0, 14], [100, 0], {extrapolateRight: 'clamp'});
    recorte = `inset(0 ${r}% 0 0)`;
  }
  const push = interpolate(frame, [0, durationInFrames], n % 2 ? [1, 1.045] : [1.045, 1], {extrapolateRight: 'clamp'});
  transf = `${transf} scale(${push})`.trim();
  const opEntrada = variante === 5 || variante === 6 ? Math.min(1, pEnt * 3) : interpolate(frame, [0, T], [0, 1], {extrapolateRight: 'clamp'});
  const opSaida = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
  });
  const blur =
    interpolate(frame, [0, T], [16, 0], {extrapolateRight: 'clamp'}) +
    interpolate(frame, [durationInFrames - 6, durationInFrames], [0, 10], {
      extrapolateLeft: 'clamp',
    });

  // faixa de luz que varre a tela no começo da cena
  const varreduraX = interpolate(frame, [0, 12], [-300, 1380], {
    extrapolateRight: 'clamp',
  });

  // bolha de cor de fundo (muda de lugar a cada cena)
  const bx = [20, 80, 30, 75][(n - 1) % 4];
  const by = [25, 70, 80, 20][(n - 1) % 4];

  const eFundo =
    cena.tipo === 'imagem' || cena.imagem || ESTILOS_PROPRIOS.includes(cena.tipo);
  const titulo = titulo_;

  return (
    <AbsoluteFill
      style={{
        opacity: Math.min(opEntrada, opSaida),
        filter: `blur(${variante === 1 || variante === 2 ? blur * 0.5 : blur}px)`,
        transform: transf || undefined,
        clipPath: recorte,
      }}
    >
      {!eFundo && (
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at ${bx}% ${by}%, ${cor}33 0%, transparent 45%)`,
          }}
        />
      )}
      {cena.tipo === 'cinetica' ? (
        <CenaCinetica cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} />
      ) : cena.tipo === 'silhuetas' ? (
        <CenaSilhuetas cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} />
      ) : cena.tipo === 'documento' ? (
        <CenaDocumento cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} />
      ) : cena.tipo === 'versus' ? (
        <CenaVersus cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} />
      ) : cena.tipo === 'linha_tempo' ? (
        <CenaLinhaTempo cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} />
      ) : cena.tipo === 'grafico_barras' ? (
        <CenaGraficoBarras cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} cor={cor} />
      ) : cena.tipo === 'grafico_linha' ? (
        <CenaGraficoLinha cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} cor={cor} />
      ) : cena.tipo === 'rosca' ? (
        <CenaRosca cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} cor={cor} />
      ) : cena.tipo === 'numero_gigante' ? (
        <CenaNumeroGigante cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} cor={cor} />
      ) : cena.tipo === 'ranking' ? (
        <CenaRanking cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} cor={cor} />
      ) : cena.tipo === 'citacao' ? (
        <CenaCitacao cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} cor={cor} />
      ) : cena.tipo === 'checklist' ? (
        <CenaChecklist cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} cor={cor} />
      ) : cena.tipo === 'alerta' ? (
        <CenaAlerta cena={cena} entradas={entradas} titulo={titulo} foto={cena.imagem} cor={cor} />
      ) : cena.tipo === 'frase' ? (
        <CenaFrase cena={cena} entradas={entradas} n={n} />
      ) : cena.tipo === 'lista_caixas' ? (
        <CenaListaCaixas cena={cena} entradas={entradas} n={n} />
      ) : cena.tipo === 'painel' ? (
        <CenaPainel cena={cena} entradas={entradas} n={n} />
      ) : null}
      {cena.tipo === 'explicativa' && cena.imagem ? (
        <FundoFoto foto={cena.imagem} opacidade={0.55} filtro="grayscale(0.1) brightness(0.88)" />
      ) : null}
      <Rotulo
        n={n}
        total={total}
        tipo={NomeTipo[cena.tipo] ?? 'Cena'}
        claro={
          ROTULO_CLARO.includes(cena.tipo) ||
          cena.tipo === 'painel' ||
          ((cena.tipo === 'frase' || cena.tipo === 'lista_caixas') && fundoDaCena(n).claro)
        }
      />
      {ESTILOS_PROPRIOS.includes(cena.tipo) ? null : cena.tipo === 'explicativa' &&
        cena.elementos &&
        cena.elementos.length > 0 ? (
        <CenaExplicativa
          destaque={cena.destaque}
          elementos={cena.elementos}
          entradas={entradas}
          cor={cor}
        />
      ) : cena.tipo === 'barras' ? (
        <CenaBarras destaque={cena.destaque} cor={cor} />
      ) : cena.tipo === 'hemiciclo' ? (
        <CenaHemiciclo destaque={cena.destaque} cor={cor} />
      ) : cena.imagem ? (
        <CenaImagem destaque={cena.destaque} imagem={cena.imagem} gancho={n === 1} n={n} />
      ) : (
        <CenaTexto destaque={cena.destaque} cor={cor} />
      )}
      {variante === 7 ? (
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at 50% 50%, transparent ${interpolate(frame, [0, 16], [0, 75], {extrapolateRight: 'clamp'})}%, ${cor} ${interpolate(frame, [0, 16], [2, 77], {extrapolateRight: 'clamp'})}%)`,
            opacity: interpolate(frame, [10, 18], [1, 0], clamp01),
            pointerEvents: 'none',
          }}
        />
      ) : null}
      {variante === 3 ? (
        <AbsoluteFill
          style={{
            background: '#fff',
            opacity: interpolate(frame, [0, 6], [0.8, 0], {extrapolateRight: 'clamp'}),
            pointerEvents: 'none',
          }}
        />
      ) : null}
      <div
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: varreduraX,
          width: 140,
          background: `linear-gradient(90deg, transparent, ${cor}55, transparent)`,
          opacity: frame < 14 ? 1 : 0,
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};

// ---------- LEGENDA PALAVRA POR PALAVRA (com palavras-chave em destaque) ----------
const Legenda: React.FC<{
  palavras: Palavra[];
  chaves: Set<string>;
  tema: 'escuro' | 'claro' | 'borda';
}> = ({palavras, chaves, tema}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const POR_LINHA = 3;

  let atual = palavras.findIndex((p) => t >= p.inicio && t < p.fim);
  if (atual < 0) {
    const passadas = palavras.filter((p) => p.fim <= t).length;
    atual = Math.max(0, passadas - 1);
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
        textAlign: 'center',
        fontFamily: SANS,
        fontWeight: 700,
        fontSize: 66,
        lineHeight: 1.2,
        zIndex: 6,
        background: 'transparent',
      }}
    >
      {linha.map((p, i) => {
        const idx = grupo * POR_LINHA + i;
        const dita = t >= p.inicio;
        const ativa = idx === atual && dita;
        const chave = chaves.has(norm(p.palavra));
        const claro = tema === 'claro';
        const cor = ativa
          ? claro ? '#b81522' : ACENTO
          : dita
            ? claro
              ? '#333'
              : '#f2efe6'
            : claro
              ? '#9a958a'
              : tema === 'borda'
                ? '#c8c8c8'
                : '#7b7b80';
        const pop = ativa ? 1 + 0.16 * Math.exp(-(t - p.inicio) * 12) : 1;
        return (
          <span
            key={idx}
            style={{
              color: cor,
              marginRight: 10,
              marginLeft: 10,
              padding: '2px 18px 6px',
              background: 'transparent',
              display: 'inline-block',
              fontSize: chave ? 74 : 66,
              transform: `scale(${pop}) rotate(${ativa ? Math.sin(idx * 2.1) * 1.2 : 0}deg)`,
              WebkitTextStroke: claro ? '1px rgba(255,255,255,0.7)' : '1px rgba(0,0,0,0.65)',
              textShadow: claro ? '0 2px 4px rgba(255,255,255,0.8)' : '0 2px 4px rgba(0,0,0,0.75)',
            }}
          >
            {p.palavra}
          </span>
        );
      })}
    </div>
  );
};

// ---------- CAMADAS GLOBAIS: grade, grão de filme, vinheta ----------
const Camadas: React.FC<{fraca?: boolean}> = ({fraca}) => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 50;
  return (
    <>
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
          backgroundSize: '90px 90px',
          pointerEvents: 'none',
        }}
      />
      <AbsoluteFill style={{opacity: 0.07, pointerEvents: 'none', overflow: 'hidden'}}>
        <svg width="1080" height="1920" viewBox="0 0 360 640" preserveAspectRatio="none">
          <filter id="ruido">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed={seed} />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="360" height="640" filter="url(#ruido)" />
        </svg>
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,${fraca ? 0.1 : 0.32}) 100%)`,
          pointerEvents: 'none',
        }}
      />
    </>
  );
};

// ---------- SOM: música com "ducking" (abaixa quando a voz fala) + efeitos sonoros ----------
type InfoCena = {from: number; dur: number; entradas: number[]} | null;

export const TIPOS_COM_POP = [
  'explicativa',
  'linha_tempo',
  'versus',
  'grafico_barras',
  'grafico_linha',
  'rosca',
  'ranking',
  'lista_caixas',
  'painel',
];

const Trilha: React.FC<{
  palavras: Palavra[];
  config?: ConfigAudio;
  cenas: Cena[];
  info: InfoCena[];
  fimSeg: number;
}> = ({palavras, config, cenas, info, fimSeg}) => {
  const {fps} = useVideoConfig();
  const cfg = config ?? {musica: false, sfx: false, volumeMusica: 1};

  // blocos de fala (junta palavras com pausa menor que 0,4 s)
  const blocos: {ini: number; fim: number}[] = [];
  palavras.forEach((p) => {
    const ult = blocos[blocos.length - 1];
    if (ult && p.inicio - ult.fim < 0.4) ult.fim = Math.max(ult.fim, p.fim);
    else blocos.push({ini: p.inicio, fim: p.fim});
  });

  const volumeMusica = (f: number) => {
    const t = f / fps;
    let duck = 0;
    for (const b of blocos) {
      if (t < b.ini - 0.3 || t > b.fim + 0.6) continue;
      const pres = interpolate(t, [b.ini - 0.3, b.ini, b.fim, b.fim + 0.6], [0, 1, 1, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
      duck = Math.max(duck, pres);
    }
    const base = cfg.volumeMusica * (1 - 0.66 * duck);
    const entrada = interpolate(t, [0, 1.2], [0, 1], {extrapolateRight: 'clamp'});
    const saida = interpolate(t, [fimSeg - 1.2, fimSeg + 0.4], [1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return base * entrada * saida;
  };

  const sons: {src: string; frame: number; vol: number}[] = [];
  if (cfg.sfx) {
    cenas.forEach((cena, i) => {
      const inf = info[i];
      if (!inf) return;
      const {from, entradas} = inf;
      if (i === 0) sons.push({src: 'impacto', frame: 0, vol: 0.9});
      else if (cfg.transicao !== false) sons.push({src: 'whoosh', frame: Math.max(0, from - 4), vol: 0.3});

      if (TIPOS_COM_POP.includes(cena.tipo)) {
        (cena.elementos ?? []).forEach((el, k) => {
          sons.push({
            src: el.tipo === 'numero' ? 'tick' : 'pop',
            frame: from + (entradas[k] ?? 0),
            vol: 0.4,
          });
        });
      }
      if (cena.tipo === 'checklist') {
        let ant = 0;
        (cena.elementos ?? []).slice(0, 5).forEach((_, k) => {
          const ent = Math.max(k === 0 ? 14 : ant + 12, entradas[k] ?? 0);
          ant = ent;
          sons.push({src: 'clique', frame: from + ent + 2, vol: 0.55});
        });
      }
      if (i === cenas.length - 1) {
        sons.push({src: 'clique', frame: from + 24 + 34, vol: 0.7});
        sons.push({src: 'brilho', frame: from + 24 + 36, vol: 0.6});
      }
      if (cena.tipo === 'frase') sons.push({src: 'tick', frame: from + Math.max(8 + 5 * 6, entradas[0] ?? 0), vol: 0.5});
      if (cena.tipo === 'alerta') sons.push({src: 'carimbo', frame: from + 4, vol: 0.8});
      if (cena.tipo === 'documento') {
        const tMarca = Math.max(22, entradas[2] ?? entradas[1] ?? 0);
        const tCarimbo = Math.max(tMarca + 24, entradas[2] ?? 0);
        sons.push({src: 'carimbo', frame: from + tCarimbo, vol: 0.9});
      }
      if (cena.tipo === 'numero_gigante') {
        sons.push({src: 'riser', frame: Math.max(0, from + 42 - 66), vol: 0.5});
        sons.push({src: 'impacto', frame: from + 42, vol: 0.85});
        sons.push({src: 'brilho', frame: from + 43, vol: 0.5});
      }
    });
  }

  return (
    <>
      {cfg.musica ? <Audio src={staticFile('musica.mp3')} loop volume={volumeMusica} /> : null}
      {sons.map((s, i) => (
        <Sequence key={i} from={s.frame} durationInFrames={90}>
          <Audio src={staticFile(`sfx/${s.src}.wav`)} volume={Math.min(1, s.vol * (cfg.volumeSfx ?? 1))} />
        </Sequence>
      ))}
    </>
  );
};

// ---------- VÍDEO ----------
export const Video: React.FC<VideoProps> = ({roteiro, tempos, palavras, audio, visual}) => {
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

  // palavras-chave: destaque e gatilhos de todas as cenas
  const chaves = new Set<string>();
  roteiro.cenas.forEach((c) => {
    c.destaque
      .split(/\s+/)
      .map(norm)
      .filter((w) => w.length > 3 && !/^\d+$/.test(w))
      .forEach((w) => chaves.add(w));
    (c.elementos ?? []).forEach((e) => {
      if (e.gatilho) chaves.add(norm(e.gatilho));
    });
  });

  // zoom de impacto: um pequeno "soco" de câmera a cada palavra-chave
  const t = frame / fps;
  const iniciosChave = palavrasFinais.filter((p) => chaves.has(norm(p.palavra))).map((p) => p.inicio);
  const ultimo = iniciosChave.filter((x) => x <= t).pop();
  const soco = ultimo !== undefined ? 1 + 0.035 * Math.exp(-(t - ultimo) * 7) : 1;

  const fimTotal = tempos.length ? tempos[tempos.length - 1].fim : 1;

  // tema da legenda conforme o fundo da cena atual
  const idxCena = Math.max(0, tempos.findIndex((x) => t >= x.inicio && t < x.fim));
  const tipoAtual = roteiro.cenas[idxCena]?.tipo ?? '';
  const tema: 'escuro' | 'claro' | 'borda' =
    tipoAtual === 'cinetica' || tipoAtual === 'painel'
      ? 'claro'
      : (tipoAtual === 'frase' || tipoAtual === 'lista_caixas') && fundoDaCena(idxCena + 1).claro
        ? 'claro'
        : tipoAtual === 'versus'
          ? 'borda'
          : 'escuro';

  // tempo de cada cena e momento em que cada elemento aparece (pelo gatilho na fala)
  const info = roteiro.cenas.map((cena, i) => {
    const tp = tempos[i];
    if (!tp) return null;
    const from = Math.round(tp.inicio * fps);
    const dur = Math.max(1, Math.round((tp.fim - tp.inicio) * fps));
    const els = cena.elementos ?? [];
    const palavrasCena = palavrasFinais.filter(
      (p) => p.inicio >= tp.inicio - 0.05 && p.inicio < tp.fim,
    );
    const entradas = els.map((e, k) => {
      const g = e.gatilho ? norm(e.gatilho) : '';
      const achada = g ? palavrasCena.find((p) => norm(p.palavra).includes(g)) : undefined;
      if (achada) return Math.max(6, Math.round((achada.inicio - tp.inicio) * fps));
      const passo = (dur - 20) / Math.max(1, els.length);
      return Math.round(10 + passo * k);
    });
    return {from, dur, entradas};
  });

  return (
    <AbsoluteFill style={{backgroundColor: BG}}>
      <Audio src={staticFile('narracao.wav')} />
      <Trilha
        palavras={palavrasFinais}
        config={audio}
        cenas={roteiro.cenas}
        info={info}
        fimSeg={fimTotal}
      />
      <AbsoluteFill style={{transform: `scale(${soco})`}}>
        {roteiro.cenas.map((cena, i) => {
          const inf = info[i];
          if (!inf) return null;
          const {from, dur, entradas} = inf;

          return (
            <Sequence key={i} from={from} durationInFrames={dur}>
              <RenderCena
                cena={cena}
                n={i + 1}
                total={total}
                entradas={entradas}
                titulo_={roteiro.titulo}
              />
            </Sequence>
          );
        })}
      </AbsoluteFill>
      <Flutuantes />
      <Particulas />
      <Camadas fraca={tema !== 'escuro'} />
      <Legenda palavras={palavrasFinais} chaves={chaves} tema={tema} />
      {(visual?.cta ?? 'Siga para mais') && info.length && info[info.length - 1] ? (
        <ChamadaFinal
          texto={visual?.cta ?? 'Siga para mais'}
          marca={visual?.marca}
          inicio={info[info.length - 1]!.from + 24}
        />
      ) : null}
      {visual?.marca ? (
        <div
          style={{
            position: 'absolute',
            bottom: 90,
            right: 70,
            zIndex: 6,
            fontFamily: MONO,
            fontSize: 26,
            color: tema === 'claro' ? '#4f4c44' : '#a8a59b',
            letterSpacing: 2,
          }}
        >
          {visual.marca}
        </div>
      ) : null}
      <div
        style={{
          position: 'absolute',
          bottom: 90,
          left: 70,
          right: 70,
          fontFamily: MONO,
          fontSize: 24,
          color: tema === 'claro' ? '#4f4c44' : MUDO,
          letterSpacing: 2,
          zIndex: 6,
        }}
      >
        {roteiro.titulo}
      </div>
      <Segmentos tempos={tempos} cor={ACENTO} />
    </AbsoluteFill>
  );
};

// Momento (em quadros, dentro da cena) em que cada elemento aparece, pelo gatilho na fala.
export const calcularEntradas = (cena: Cena, ini: number, fim: number, palavras: Palavra[], fps: number): number[] => {
  const els = cena.elementos ?? [];
  const dur = Math.max(1, Math.round((fim - ini) * fps));
  const doTrecho = palavras.filter((p) => p.inicio >= ini - 0.05 && p.inicio < fim);
  return els.map((e, k) => {
    const g = e.gatilho ? norm(e.gatilho) : '';
    const achada = g ? doTrecho.find((p) => norm(p.palavra).includes(g)) : undefined;
    if (achada) return Math.max(6, Math.round((achada.inicio - ini) * fps));
    const passo = (dur - 20) / Math.max(1, els.length);
    return Math.round(10 + passo * k);
  });
};
