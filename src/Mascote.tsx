import React from 'react';
import {AbsoluteFill, Freeze, Img, Loop, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type Expressao = 'explicando'|'feliz'|'professor'|'surpreso'|'pensativo'|'desconfiado'|'bravo'|'preocupado'|'ideia'|'positivo'|'estudando'|'ok';
export type Posicao = 'esquerda'|'direita'|'ambos'|'oculto';
export type TrocaMascote = {numero: number; posicao: Posicao; expressao: Expressao; expressao_direita: Expressao};
export type VideoMascote = {arquivo: string; cena?: number|null; duracao: number; tem_audio?: boolean};
export type ConfigMascote = {
  ativo: boolean; posicao: Posicao; expressao: Expressao; expressao_direita: Expressao;
  tamanho: number; rodape: number; animar: boolean; automatico: boolean;
  voz?: string; fundo: 'video'|'editor'; encaixe: 'cover'|'contain'; volume_original: number;
  repetir_video: boolean; cenas: TrocaMascote[]; quadros: TrocaMascote[]; videos: VideoMascote[];
};
type Bloco = {from: number; dur: number; c: {narracao?: string; tipo?: string}};
type Palavra = {inicio: number; fim: number};
type Tempo = {inicio: number; fim: number};

export const expressaoAutomatica = (texto: string, tipo?: string): Expressao => {
  const t = texto.toLocaleLowerCase('pt-BR');
  if (/\b(morreu|morte|vítima|vitima|tragédia|tragedia|risco|perigo|cuidado|triste)\b/.test(t)) return 'preocupado';
  if (/\b(absurdo|revolta|raiva|indignação|indignacao)\b/.test(t)) return 'bravo';
  if (/\b(mentira|duvidoso|suspeito|será mesmo|sera mesmo)\b/.test(t)) return 'desconfiado';
  if (t.includes('?')) return 'pensativo';
  if (/\b(surpresa|incrível|incrivel|chocante|inesperado)\b/.test(t)) return 'surpreso';
  if (/\b(ideia|solução|solucao|descoberta|dica)\b/.test(t)) return 'ideia';
  if (/\b(engraçado|engracado|risada|rir|piada|feliz|alegria)\b/.test(t)) return 'feliz';
  if (/\b(conseguiu|parabéns|parabens|certo|vitória|vitoria)\b/.test(t)) return 'positivo';
  if (tipo === 'fecho') return 'ok';
  if (/\b(estudo|pesquisa|cientistas|livro)\b/.test(t)) return 'estudando';
  return 'professor';
};

export const resolverMascote = (cfg: ConfigMascote, cena: number, frame: number, texto = '', tipo?: string) => {
  let state = {posicao: cfg.posicao, expressao: cfg.automatico ? expressaoAutomatica(texto, tipo) : cfg.expressao, expressao_direita: cfg.expressao_direita};
  const scene = cfg.cenas?.find(c => c.numero === cena);
  if (scene) state = {...state, ...scene};
  // Último frame definido vence. Sem aleatoriedade: prévia e render usam a mesma regra.
  const keyframe = [...(cfg.quadros ?? [])].sort((a,b) => a.numero-b.numero).filter(c => c.numero <= frame).pop();
  if (keyframe) state = {...state, ...keyframe};
  return state;
};

const Clip: React.FC<{video: VideoMascote; cfg: ConfigMascote; total: number}> = ({video, cfg, total}) => {
  const {fps} = useVideoConfig();
  const duration = Math.max(1, Math.floor(video.duracao * fps));
  const muted = !video.tem_audio || cfg.volume_original <= 0;
  const element = <OffthreadVideo src={staticFile(video.arquivo)} muted={muted} volume={cfg.volume_original}
    style={{width:'100%',height:'100%',objectFit:cfg.encaixe}} />;
  return <AbsoluteFill style={{background:'#101116'}}>
    {cfg.repetir_video ? <Loop durationInFrames={duration}>{element}</Loop> : <>
      <Sequence durationInFrames={Math.min(duration,total)}>{element}</Sequence>
      {total > duration ? <Sequence from={duration} durationInFrames={total-duration}><Freeze frame={duration-1}>
        <OffthreadVideo src={staticFile(video.arquivo)} muted style={{width:'100%',height:'100%',objectFit:cfg.encaixe}} />
      </Freeze></Sequence> : null}
    </>}
  </AbsoluteFill>;
};

export const FundoMascote: React.FC<{cfg: ConfigMascote; blocos: Bloco[]; total: number}> = ({cfg,blocos,total}) => {
  const frame=useCurrentFrame();
  if (!cfg.ativo || cfg.fundo !== 'video' || !cfg.videos?.length) return null;
  const base = cfg.videos.find(v=>!v.cena) ?? cfg.videos[0];
  let cenaAtual=1;blocos.forEach((b,i)=>{if(frame>=b.from)cenaAtual=i+1;});
  const temVideoDaCena=cfg.videos.some(v=>v.cena===cenaAtual);
  return <AbsoluteFill style={{zIndex:10}}>
    <Clip video={base} cfg={{...cfg,volume_original:temVideoDaCena?0:cfg.volume_original}} total={total} />
    {blocos.map((b,i)=>{
      const video=cfg.videos.find(v=>v.cena===i+1);
      if (!video) return null;
      const end=blocos[i+1]?.from ?? total;
      return <Sequence key={i} from={b.from} durationInFrames={end-b.from}><Clip video={video} cfg={cfg} total={end-b.from} /></Sequence>;
    })}
  </AbsoluteFill>;
};

export const ApresentadorMascote: React.FC<{cfg: ConfigMascote; blocos: Bloco[]; palavras: Palavra[]; tempos?: Tempo[]}> = ({cfg,blocos,palavras,tempos}) => {
  const frame=useCurrentFrame();const {fps}=useVideoConfig();
  if (!cfg.ativo || !blocos.length) return null;
  let index=0;blocos.forEach((b,i)=>{if(frame>=b.from)index=i;});
  const b=blocos[index];const state=resolverMascote(cfg,index+1,frame,b.c.narracao,b.c.tipo);
  const time=frame/fps;
  const speaking=palavras.length ? palavras.some(p=>time>=p.inicio&&time<=p.fim) : !!tempos?.some(t=>time>=t.inicio&&time<=t.fim);
  const enter=interpolate(frame,[0,10],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const lively=cfg.voz==='divertido';
  const bob=cfg.animar&&speaking ? Math.sin(frame*0.38)*(lively?7:3.5) : 0;
  const tilt=cfg.animar&&speaking ? Math.sin(frame*0.19)*(lively?1.8:0.8) : 0;
  const render=(side:'esquerda'|'direita',pose:Expressao)=> <Img key={side} src={staticFile(`mascotes/${pose}.png`)}
    style={{position:'absolute',width:`${cfg.tamanho}%`,bottom:cfg.rodape+(1-enter)*-45+bob,
      ...(side==='esquerda'?{left:36}:{right:92}),height:'auto',opacity:enter,
      transform:`${side==='direita'?'scaleX(-1) ':''}rotate(${tilt}deg) scale(${1+(speaking&&cfg.animar?Math.sin(frame*0.4)*0.008:0)})`,
      transformOrigin:'50% 100%',filter:'drop-shadow(0 6px 8px rgba(0,0,0,.4))'}} />;
  return <AbsoluteFill style={{zIndex:42,pointerEvents:'none'}}>
    {['esquerda','ambos'].includes(state.posicao)?render('esquerda',state.expressao):null}
    {['direita','ambos'].includes(state.posicao)?render('direita',state.posicao==='ambos'?state.expressao_direita:state.expressao):null}
  </AbsoluteFill>;
};
