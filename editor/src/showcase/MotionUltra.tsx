/**
 * Motion Ultra 1.0 — upgrades visuais para layouts existentes.
 * Compatível com Remotion 4, React 18 e os tipos de showcase/Base.tsx.
 * Tudo é determinado pelo frame: não há relógios, CSS animations ou aleatoriedade.
 * O áudio, as legendas e o mascote continuam sob responsabilidade de Showcase.tsx.
 */
import React from 'react';
import {
  AbsoluteFill, Easing, Img, Loop, OffthreadVideo, interpolate,
  spring, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';
import {CenaSC, FORTE, TEXTO} from './Base';

type Props = {c: CenaSC; dur: number};
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const trans = (x: number, range: number[], values: number[]) => interpolate(x, range, values, clamp);
const ease = Easing.bezier(.2, .8, .2, 1);
const aparece = (f: number, ini: number, tempo = 18) => ease(trans(f, [ini, ini + tempo], [0, 1]));
const limita = (s: string | undefined, max = 88) => (s || '').replace(/\s+/g, ' ').trim().slice(0, max);
const contexto = (c: CenaSC) => {
  const m = c.motion;
  const claro = Boolean(m?.claro);
  return {
    claro, fundo: claro ? '#F3F4EF' : '#0B111A',
    texto: claro ? '#161B20' : '#FAFBF7',
    secund: claro ? '#505A65' : '#B8C4CE',
    painel: claro ? '#FFFFFF' : '#17212E',
    traco: claro ? '#D5DCE1' : '#394759',
    destaque: m?.acento || c.acento || '#C7FB65',
  };
};

const Midia: React.FC<{c: CenaSC; dur: number; zoom?: number; deslocar?: number}> = ({c, dur, zoom=1.11, deslocar=26}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const q = Math.min(1, Math.max(0, f / Math.max(1, dur)));
  const v = c.video;
  const drift=q*q*(3-2*q);
  const tr = `scale(${1.045 + (zoom - 1)*drift}) translateX(${(drift - .5)*deslocar}px)`;
  if (v?.arquivo) {
    const inicio = Math.max(0, Math.round((Number(v.inicio)||0)*fps));
    const fim = Math.max(inicio+2, Math.round((Number(v.fim)||.5)*fps));
    return <AbsoluteFill style={{overflow:'hidden'}}><div style={{position:'absolute',inset:0,transform:tr}}>
      <Loop durationInFrames={Math.max(2,fim-inicio)}>
        <OffthreadVideo src={staticFile(v.arquivo)} startFrom={inicio} endAt={fim} muted style={{width:'100%',height:'100%',objectFit:'cover'}} />
      </Loop>
    </div></AbsoluteFill>;
  }
  const foto = c.foto || c.recorte;
  if (foto) return <AbsoluteFill style={{overflow:'hidden'}}><Img src={staticFile(foto)} style={{width:'100%',height:'100%',objectFit:'cover',transform:tr}}/></AbsoluteFill>;
  // Sem arquivo real: fundo ilustrativo, nunca mídia falsamente real.
  const T = contexto(c);
  return <AbsoluteFill style={{background:`radial-gradient(ellipse at 40% 35%,${T.destaque}55,transparent 60%),linear-gradient(140deg,#1D3140,#0B111A)`}}>
    <div style={{position:'absolute',top:570,left:130,right:130,fontFamily:FORTE,fontWeight:900,fontSize:120,opacity:.12,color:'#fff',textAlign:'center',transform:`translateY(${q*30}px)`}}>{limita(c.motion?.chaves[0] || '',20)}</div>
  </AbsoluteFill>;
};

const Texto: React.FC<{titulo:string;rotulo?:string;claro?:boolean;top?:number;size?:number}> = ({titulo,rotulo,claro,top=190,size=86}) => {
  const f=useCurrentFrame(); const T=claro?{txt:'#182029',sub:'#53606C'}:{txt:'#F6F8FA',sub:'#CAD3DC'};
  const p=aparece(f,2,20);
  return <div style={{position:'absolute',left:75,right:130,top,zIndex:5,opacity:p,transform:`translateY(${(1-p)*66}px)`}}>
    {rotulo?<div style={{fontFamily:TEXTO,color:T.sub,fontSize:24,fontWeight:700,letterSpacing:5,textTransform:'uppercase',marginBottom:22}}>{limita(rotulo,50)}</div>:null}
    <div style={{fontFamily:FORTE,color:T.txt,fontSize:size,fontWeight:900,lineHeight:1.02,letterSpacing:-3,overflowWrap:'anywhere',textShadow:claro?'none':'0 3px 25px #0006'}}>{limita(titulo,80)}</div>
  </div>;
};

const Trilho: React.FC<{p:number;destaque:string;left?:number;top?:number;width?:number}> = ({p,destaque,left=80,top=1445,width=650}) =>
  <svg width={width} height="100" viewBox="0 0 700 100" style={{position:'absolute',left,top,zIndex:7,overflow:'visible'}}>
    <path d="M10 50 C165 4,315 92,690 50" stroke={destaque} strokeWidth="8" strokeLinecap="round" fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={1-p}/>
    <circle cx={10+680*p} cy={50+Math.sin(p*Math.PI*2)*18} r="12" fill={destaque} opacity={p>.05?1:0}/>
  </svg>;

/** Celular com scroll demonstrativo, foco progressivo, toque e linha de interface. */
const Celular: React.FC<Props> = ({c,dur}) => {
  const f=useCurrentFrame(), {fps}=useVideoConfig(), T=contexto(c), m=c.motion!;
  const entra=spring({fps,frame:f-3,config:{mass:.8,damping:22,stiffness:125}});
  const q=trans(f,[0,dur],[0,1]);
  const scroll=trans(f,[18,Math.max(40,dur-12)],[0,240]);
  const toque=m.batidas?.length>1?Math.round((m.batidas[1].em||.8)*fps):Math.min(48,Math.round(dur*.35));
  const pulso=trans(Math.abs(f-toque),[0,12],[1,0]);
  const linhas=(m.batidas?.length?m.batidas:m.chaves.map((texto,i)=>({texto,em:i*.8,icone:''}))).slice(0,4);
  return <AbsoluteFill style={{background:T.fundo,overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:`radial-gradient(ellipse at 70% 60%, ${T.destaque}20, transparent 54%)`}}/>
    <Texto titulo={m.titulo} rotulo="Entenda na prática" claro={T.claro} top={140} size={78}/>
    <div style={{position:'absolute',left:205,top:535,width:670,height:1040,borderRadius:80,background:'#101820',border:'8px solid #77838A',boxShadow:'0 45px 110px #0008,inset 0 0 0 6px #ffffff14',overflow:'hidden',opacity:entra,transform:`perspective(2000px) rotateY(${-15+q*10}deg) rotateZ(${-3+q*4}deg) translateY(${(1-entra)*260}px)`}}>
      <div style={{position:'absolute',inset:16,borderRadius:59,overflow:'hidden',background:'#F5F8FA'}}>
        <div style={{height:87,background:'#0F1922',color:'#F5FAFF',display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 34px',fontFamily:TEXTO,fontSize:24,fontWeight:700}}><span>Exemplo visual</span><div style={{width:165,height:32,borderRadius:25,background:'#03080E'}}/></div>
        <div style={{position:'absolute',left:30,right:30,top:110,bottom:18,overflow:'hidden'}}>
          <div style={{transform:`translateY(${-scroll}px)`}}>
            <div style={{fontFamily:FORTE,fontWeight:900,color:'#102030',fontSize:48,lineHeight:1.08,margin:'20px 0 28px'}}>{limita(m.chaves[0]||m.titulo,42)}</div>
            <div style={{height:245,position:'relative',borderRadius:25,overflow:'hidden',background:'#DCE5E9'}}><Midia c={c} dur={dur}/></div>
            <div style={{marginTop:25}}>{linhas.map((b,i)=>{const ativos=f/fps>=(b.em||0);return <div key={i} style={{margin:'15px 0',borderRadius:23,background:ativos?'#DFF0EA':'#E9EFF2',border:ativos?`2px solid ${T.destaque}`:'2px solid #E0E8ED',padding:'22px 23px',display:'flex',alignItems:'center',gap:18}}><span style={{width:43,height:43,borderRadius:22,background:ativos?'#112A29':'#CFD7DD',color:ativos?'#fff':'#334',fontFamily:TEXTO,fontSize:23,fontWeight:800,textAlign:'center',lineHeight:'43px',flexShrink:0}}>{i+1}</span><span style={{fontFamily:TEXTO,color:'#14212D',fontSize:29,fontWeight:680,lineHeight:1.15}}>{limita(b.texto,58)}</span></div>})}</div>
          </div>
        </div>
        <div style={{position:'absolute',bottom:10,left:'38%',width:'24%',height:7,borderRadius:8,background:'#17202A'}}/>
      </div>
    </div>
    <svg width="1050" height="850" viewBox="0 0 1050 850" style={{position:'absolute',inset:0,top:700,pointerEvents:'none',zIndex:6}}><path d="M90 100 Q150 10 255 85" stroke={T.destaque} strokeWidth="7" fill="none" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1-aparece(f,16,27)}/></svg>
    <div style={{position:'absolute',left:675,top:990+trans(f,[0,dur],[70,-70]),zIndex:8,opacity:aparece(f,10,16),transform:`scale(${1+pulso*.16})`,pointerEvents:'none'}}>
      <svg width="120" height="142" viewBox="0 0 120 142"><path d="M25 8 L25 117 L51 84 L70 127 L90 118 L70 75 L111 74 Z" fill="#0C1219" stroke="#FFF" strokeWidth="7" strokeLinejoin="round"/></svg>
      {pulso>0?<div style={{position:'absolute',left:-26,top:-32,width:92,height:92,border:`6px solid ${T.destaque}`,borderRadius:'50%',opacity:pulso,transform:`scale(${1+(1-pulso)})`}}/>:null}
    </div>
    <Trilho p={aparece(f,18,Math.max(25,dur-36))} destaque={T.destaque} top={1620} width={690}/>
  </AbsoluteFill>;
};

/** Infográfico: linha curva se desenhando e nós reagindo ao tempo da narração. */
const Caminho: React.FC<Props> = ({c,dur}) => {
  const f=useCurrentFrame(),{fps}=useVideoConfig(),T=contexto(c),m=c.motion!;
  const steps=(c.checklist?.length?c.checklist.map((texto,i)=>({texto,em:m.batidas[i]?.em??i*.85})):m.batidas).slice(0,4);
  const arr=steps.length?steps:[{texto:m.titulo,em:0}];
  const prog=aparece(f,18,Math.max(30,dur-28));
  return <AbsoluteFill style={{background:T.fundo,overflow:'hidden'}}>
    <Texto titulo={m.titulo} rotulo="Como funciona" claro={T.claro} top={160} size={82}/>
    <div style={{position:'absolute',left:65,top:580,width:950,height:960}}>
      <svg width="950" height="960" viewBox="0 0 950 960" style={{position:'absolute',inset:0}}>
        <path d="M145 65 C470 65 90 380 390 390 S700 640 510 855" stroke={T.traco} strokeWidth="12" strokeLinecap="round" fill="none"/>
        <path d="M145 65 C470 65 90 380 390 390 S700 640 510 855" stroke={T.destaque} strokeWidth="13" strokeLinecap="round" fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={1-prog}/>
      </svg>
      {arr.map((b,i)=>{const pos=[{x:145,y:65},{x:275,y:294},{x:390,y:390},{x:510,y:855}][Math.min(i,3)];const ativo=f/fps>=b.em;const p=aparece(f,Math.max(i*9,Math.round(b.em*fps)),15);const w=i%2===0?430:460;const x=i%2===0?pos.x+70:Math.max(45,pos.x-460);return <React.Fragment key={i}>
        <div style={{position:'absolute',left:pos.x-31,top:pos.y-31,width:62,height:62,borderRadius:'50%',background:ativo?T.destaque:T.painel,border:`7px solid ${T.fundo}`,boxShadow:'0 10px 30px #0004',color:ativo?'#102019':T.texto,fontFamily:FORTE,fontSize:28,fontWeight:900,textAlign:'center',lineHeight:'50px',opacity:p,transform:`scale(${.5+.5*p})`,zIndex:6}}>{i+1}</div>
        <div style={{position:'absolute',left:x,top:pos.y-34,width:w,borderRadius:20,padding:'23px 25px',boxSizing:'border-box',background:T.painel,border:`2px solid ${ativo?T.destaque:T.traco}`,boxShadow:'0 22px 45px #0002',opacity:p,transform:`translateY(${(1-p)*40}px)`}}><span style={{fontFamily:TEXTO,fontWeight:700,fontSize:30,lineHeight:1.16,color:T.texto}}>{limita(b.texto,56)}</span></div>
      </React.Fragment>;})}
    </div>
    <div style={{position:'absolute',left:83,top:1585,height:5,width:765,background:T.traco}}><div style={{width:`${prog*100}%`,background:T.destaque,height:'100%',borderRadius:4}}/></div>
  </AbsoluteFill>;
};

/** Documentário: imagem/vídeo com câmera em movimento, foco e linhas de rastreamento. */
const Documental: React.FC<Props> = ({c,dur}) => {
  const f=useCurrentFrame(),T=contexto(c),m=c.motion!,q=trans(f,[0,dur],[0,1]);
  const open=aparece(f,3,22), line=aparece(f,17,30);
  return <AbsoluteFill style={{overflow:'hidden',background:'#090E15'}}>
    <Midia c={c} dur={dur} zoom={1.16} deslocar={36}/>
    <AbsoluteFill style={{background:'linear-gradient(to bottom,#050B14B0,transparent 32%,transparent 51%,#050B14EC 91%)'}}/>
    <div style={{position:'absolute',left:64,right:125,top:185,fontFamily:TEXTO,fontSize:25,letterSpacing:5,fontWeight:800,color:'#E0E6E9',opacity:open}}>DOCUMENTÁRIO VISUAL</div>
    <div style={{position:'absolute',left:66,right:150,top:1180,opacity:open,transform:`translateY(${(1-open)*80}px)`}}><div style={{width:90,height:8,background:T.destaque,marginBottom:25}}/><div style={{fontFamily:FORTE,fontSize:90,lineHeight:1.04,letterSpacing:-3,fontWeight:900,color:'#FFF',textShadow:'0 4px 25px #0009'}}>{limita(m.titulo,70)}</div></div>
    <svg width="1080" height="950" viewBox="0 0 1080 950" style={{position:'absolute',top:250,left:0,opacity:.7}}>
      <path d="M170 490 H345 V275 H745" stroke={T.destaque} strokeWidth="6" strokeLinecap="round" fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={1-line}/>
      <path d="M745 275 h85 v85" stroke={T.destaque} strokeWidth="4" fill="none" opacity={line}/>
      <circle cx="745" cy="275" r={12+Math.sin(q*Math.PI*8)*4} fill={T.destaque} opacity={line}/>
    </svg>
    <div style={{position:'absolute',top:540+Math.sin(q*Math.PI)*32,left:360,width:460,height:370,border:`2px solid ${T.destaque}85`,borderRadius:20,opacity:line*.8,transform:`scale(${.95+.05*q})`}}><span style={{position:'absolute',left:-3,top:-3,width:60,borderTop:`7px solid ${T.destaque}`}}/><span style={{position:'absolute',right:-3,bottom:-3,width:60,borderBottom:`7px solid ${T.destaque}`}}/></div>
  </AbsoluteFill>;
};

/** Colagem assimétrica: dois enquadramentos, trilho desenhado e recorte em perspectiva. */
const ColagemPro: React.FC<Props> = ({c,dur}) => {
  const f=useCurrentFrame(),{fps}=useVideoConfig(),T=contexto(c),m=c.motion!,q=trans(f,[0,dur],[0,1]);
  const a=spring({frame:f-4,fps,config:{damping:24,stiffness:100}}),b=spring({frame:f-14,fps,config:{damping:23,stiffness:115}});
  return <AbsoluteFill style={{background:T.fundo,overflow:'hidden'}}>
    <Texto titulo={m.titulo} rotulo="Uma nova perspectiva" claro={T.claro} top={170} size={78}/>
    <div style={{position:'absolute',top:630,left:55,width:745,height:865,borderRadius:36,overflow:'hidden',background:T.painel,boxShadow:'0 40px 80px #0005',opacity:a,transform:`perspective(1800px) rotateY(${-9+q*7}deg) rotateZ(${-4+q*3}deg) translateY(${(1-a)*140}px)`}}><Midia c={c} dur={dur}/></div>
    <div style={{position:'absolute',top:950,right:42,width:375,height:410,borderRadius:29,overflow:'hidden',border:`8px solid ${T.fundo}`,background:T.painel,boxShadow:'0 25px 80px #0007',opacity:b,transform:`translateX(${(1-b)*210}px) rotate(${5-3*q}deg)`}}><Midia c={c} dur={dur} zoom={1.3} deslocar={-23}/></div>
    <div style={{position:'absolute',top:1450,left:95,right:160,display:'flex',gap:16}}>{m.chaves.slice(0,3).map((w,i)=><span key={i} style={{fontFamily:TEXTO,fontSize:26,fontWeight:800,padding:'15px 18px',borderRadius:35,background:T.painel,color:T.texto,border:`1px solid ${T.traco}`,opacity:aparece(f,25+i*7)}}>{limita(w,26)}</span>)}</div>
    <Trilho p={aparece(f,17,Math.max(24,dur-25))} destaque={T.destaque} left={70} top={1580} width={750}/>
  </AbsoluteFill>;
};

const temas = [
  {nome:'Astronomia', termos:/planeta|orbita|espaco|lua|estrela|solar|universo/, bg:'#101529', ink:'#f6e9d6', cor:'#ff926e', luz:'#96aaff'},
  {nome:'Acústica', termos:/som\b|audio|onda|eco\b|ouvido|musica|voz/, bg:'#101f23', ink:'#f5f2dc', cor:'#c8f96a', luz:'#64c8b2'},
  {nome:'Fotografia', termos:/foto|camera|lente|foco|obturador/, bg:'#271923', ink:'#fff0da', cor:'#ffae73', luz:'#dc829d'},
  {nome:'Tecnologia', termos:/chip|circuito|processador|computador|digital|internet|sinal/, bg:'#101d32', ink:'#f1f5ff', cor:'#8ee7ff', luz:'#a69dff'},
  {nome:'Cartografia', termos:/rota|mapa|caminho|trajeto|cidade|percurso/, bg:'#efe9d7', ink:'#162f32', cor:'#b64124', luz:'#5e8880'},
  {nome:'Tempo', termos:/relogio|tempo|segundo|minuto|ponteiro|cronometro/, bg:'#20201f', ink:'#f7ecd2', cor:'#ffc668', luz:'#96a5a5'},
];
const smooth = (x:number) => { const v=Math.max(0,Math.min(1,x)); return v*v*(3-2*v); };
const seguro = (s:string) => s.replace(/[&<>"']/g,k=>(({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'} as Record<string,string>)[k]));
function linhas(s:string, max:number) {
  const out:string[]=[];
  for(const palavra of s.trim().split(/\s+/)){
    const j=out.length-1;
    if(j<0 || (out[j]+' '+palavra).length>max) out.push(palavra);
    else out[j]+=' '+palavra;
  }
  return out;
}
function arte(id:number,t:number,titulo:string,detalhe:string,espelho=false) {
  const {bg,ink,cor,luz,nome}=temas[id];
  const circ=(x:number,y:number,r:number,fill:string,stroke='none',w=1)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${w}"/>`;
  const path=(d:string,color:string,w:number,fill='none')=>`<path d="${d}" fill="${fill}" stroke="${color}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"/>`;
  const rep=(n:number,fn:(i:number)=>string)=>Array.from({length:n},(_,i)=>fn(i)).join('');
  const txt=(x:number,y:number,s:string,size:number,weight:number,color=ink)=>`<text x="${x}" y="${y}" font-family="DejaVu Sans, Arial, sans-serif" font-size="${size}" font-weight="${weight}" fill="${color}">${seguro(s)}</text>`;
  const a=t*Math.PI*2, enter=smooth(t/.17), turn=espelho?-1:1;
  let hero='';
  if(id===0){
    const track=(front:boolean)=>rep(3,i=>{
      const theta=a*(.41+i*.18)*turn+i*2.1+.5;
      return (Math.sin(theta)>0)===front?circ(Math.cos(theta)*(105+25*i),Math.sin(theta)*(32+10*i),6+i, i===1?cor:ink):'';
    });
    hero=`<g transform="rotate(-24)">${rep(3,i=>`<ellipse rx="${105+25*i}" ry="${32+10*i}" fill="none" stroke="${luz}" opacity=".65"/>`)}${track(false)}${circ(0,0,54,'url(#sphere)')}${track(true)}</g>`;
  } else if(id===1){
    hero=rep(7,j=>{const d=Array.from({length:101},(_,i)=>{const x=i/100;return (i?'L':'M')+(x*320-160)+' '+((j-3)*10+Math.sin(x*12-a*1.6+j*.3)*Math.sin(Math.PI*x)**2*(45+j*4));}).join(' ');return path(d,j===3?cor:luz,j===3?4:1.2);});
  } else if(id===2){
    const aperture=18+20*(1-Math.cos(a))*.5;
    hero=circ(0,0,122,'none',luz,2)+circ(0,0,109,'none',ink,1)+rep(8,i=>`<g transform="rotate(${i*45+12*Math.sin(a)})">${path(`M 0 -101 Q 50 -97 72 -72 L ${aperture} -8 L 0 -${aperture} Z`,bg,1,i%2?luz:cor)}</g>`)+circ(0,0,aperture*.6,'url(#sphere)');
  } else if(id===3){
    hero=rep(20,i=>{const j=i%5,ang=Math.floor(i/5)*90; const y=(j-2)*18,delta=(j-2)*12, p=(t*1.5+j*.17)%1;
      return `<g transform="rotate(${ang})">${path(`M 55 ${y} H 78 L 101 ${y+delta} H 142`,luz,2)}${circ(142,y+delta,3,cor)}${circ(55+87*p,y+delta*smooth((p-.26)/.27),3.5,ink)}</g>`;})+`<rect x="-54" y="-54" width="108" height="108" rx="12" fill="${bg}" stroke="${cor}" stroke-width="3"/>`+rep(9,i=>circ((i%3-1)*20,(Math.floor(i/3)-1)*20,5,i===4?ink:luz));
  } else if(id===4){
    hero=rep(17,i=>path(`M -160 ${i*15-130} q 65 -22 109 7 t 93 1 t 118 -10`,luz,.7));
    const point=(p:number)=>[p*286-143,48*Math.sin(p*6+.6)-46*p];
    hero+=path(Array.from({length:101},(_,i)=>(i?'L':'M')+point(i/100).join(' ')).join(' '),ink,4);
    const [x,y]=point(.05+.9*smooth(t));hero+=circ(x,y,17,bg,cor,2)+circ(x,y,8,cor);
  } else {
    hero=circ(0,0,120,'none',luz,2)+rep(60,i=>`<g transform="rotate(${i*6})">${path('M 0 -110 V '+(i%5?-106:-96),i%5?luz:ink,i%5?1:3)}</g>`)+`<g transform="rotate(${-66+t*180})">${path('M 0 19 V -88',cor,5)}</g>`+path('M 0 0 L -44 -28',ink,7)+circ(0,0,7,cor);
  }
  const title=linhas(titulo,19), size=Math.min(38,Math.max(21,Math.floor(130/title.length)),Math.floor(570/Math.max(...title.map(s=>s.length),1)));
  const note=linhas(detalhe,33).slice(0,3);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="432" height="768" viewBox="0 0 432 768"><defs><radialGradient id="sphere" cx="30%" cy="22%" r="80%"><stop stop-color="${ink}"/><stop offset=".48" stop-color="${cor}"/><stop offset="1" stop-color="${bg}"/></radialGradient></defs><rect width="432" height="768" fill="${bg}"/>${path('M 32 62 H 358',luz,1)}${txt(32,52,nome.toUpperCase(),12,700,luz)}<g transform="translate(0 ${10*(1-enter)})">${title.slice(0,5).map((s,i)=>txt(30,117+i*size*1.1,s,size,700)).join('')}</g><g transform="translate(205 365) scale(${.86+.09*enter+.04*smooth(t)})">${hero}</g><g opacity="${.25+.75*smooth(t/.16)}">${path('M 32 525 H '+(54+60*enter),cor,3)}${note.map((s,i)=>txt(32,557+23*i,s,17,500)).join('')}</g></svg>`;
}

const Prancha: React.FC<Props & {id:number}> = ({c,dur,id}) => {
  const frame=useCurrentFrame(), {fps}=useVideoConfig(), m=c.motion!;
  const beats=(m.batidas||[]).filter(b=>b.texto && frame>=b.em*fps);
  const beat=beats[beats.length-1];
  const detail=beat?.texto || (m.chaves||[]).find(v=>v!==m.titulo) || '';
  const svg=arte(id, Math.min(1,frame/Math.max(1,dur-1)),limita(m.titulo,80),detail===m.titulo?'':limita(detail,85),Boolean((m.variante||0)%2));
  return <AbsoluteFill style={{background:temas[id].bg}}><svg width="100%" height="100%" viewBox="0 0 432 768" dangerouslySetInnerHTML={{__html:svg}}/></AbsoluteFill>;
};
export const MotionUltra: React.FC<Props> = ({c,dur}) => {
  const tipo=c.motion?.layout;
  if (!c.motion) return null;
  const m=c.motion;
  const assunto=[m.titulo,...(m.chaves||[])].join(' ').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const id=temas.findIndex(tema=>tema.termos.test(assunto));
  if(id>=0 && (!(c.video?.arquivo || c.foto || c.recorte) || (m.variante||0)%3===2)) return <Prancha c={c} dur={dur} id={id}/>;
  switch (tipo) {
    case 'interface': return <Celular c={c} dur={dur}/>;
    case 'sequencia': return <Caminho c={c} dur={dur}/>;
    case 'editorial': return <Documental c={c} dur={dur}/>;
    case 'colagem': return <ColagemPro c={c} dur={dur}/>;
    default: return null;
  }
};
