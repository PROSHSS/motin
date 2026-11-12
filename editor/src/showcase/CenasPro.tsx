import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, OffthreadVideo, Loop} from 'remotion';
import type {CenaSC} from './Base';
import {FORTE, TEXTO, clamp} from './Base';

type Props = {c:CenaSC;dur:number};
const entrada=(frame:number,inicio:number,dur=22)=>Easing.bezier(.16,1,.3,1)(interpolate(frame,[inicio,inicio+dur],[0,1],clamp));
const resumo=(s:string,n=9)=>String(s||'').split(/\s+/).slice(0,n).join(' ');
const fonte=(s:string,max:number,largura=850)=>Math.max(29,Math.min(max,largura/(Math.max(6,s.length)*.57)));
const cor=(c:CenaSC)=>c.motion?.acento||c.acento||'#c7fb65';
const Media:React.FC<Props>=({c,dur})=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),v=c.video;
 if(v&&v.fim>v.inicio){const a=Math.max(0,Math.round(v.inicio*fps)),b=Math.max(a+2,Math.round(v.fim*fps));return <Loop durationInFrames={b-a}><OffthreadVideo src={staticFile(v.arquivo)} startFrom={a} endAt={b} muted style={{width:'100%',height:'100%',objectFit:'cover'}}/></Loop>;}
 const src=c.foto||c.recorte;
 if(!src)return <AbsoluteFill style={{background:'#1e2935'}}/>;
 return <Img src={staticFile(src)} style={{width:'100%',height:'100%',objectFit:'cover',transform:'scale('+(1.02+.06*frame/Math.max(1,dur))+')'}}/>;
};
export const PalavraCinetica:React.FC<Props>=({c,dur})=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig(),m=c.motion!,v=(m.variante||0)%3;
 const ac=cor(c),ink=m.claro?'#121923':'#fafaf5',bg=m.claro?'#f0ede7':'#0d121a',q=f/Math.max(1,dur);
 const title=resumo(m.titulo||c.narracao||'',v===1?10:7),a=entrada(f,1,24);
 const chunks=(m.batidas||[]).slice(0,4),active=chunks.reduce((p,b,i)=>f/fps>=b.em?i:p,0);
 return <AbsoluteFill style={{background:bg,overflow:'hidden'}}>
  <div style={{position:'absolute',inset:0,opacity:.07,backgroundImage:'linear-gradient('+ink+' 1px, transparent 1px)',backgroundSize:'100% 130px',transform:'translateY('+(q*28)+'px)'}}/>
  <div style={{position:'absolute',left:v===1?120:75,top:v===2?350:460,right:85,color:ink,fontFamily:FORTE,fontSize:fonte(title,v===2?125:148),fontWeight:900,lineHeight:1.0,letterSpacing:-4,transform:'translateY('+((1-a)*105)+'px) scale('+(.88+.12*a)+')',transformOrigin:'left center',opacity:a}}>{title}</div>
  <div style={{position:'absolute',left:80,top:v===2?790:900,width:870,height:9,background:ac,transformOrigin:'left',transform:'scaleX('+entrada(f,12,32)+')'}}/>
  {chunks.map((b,i)=>{const p=entrada(f,Math.max(14,b.em*fps),18),current=i===active;return <div key={i} style={{position:'absolute',left:90+(i%2)*45,top:(v===1?1040:1000)+i*115,right:90,fontFamily:TEXTO,fontSize:v===1?34:40,fontWeight:current?800:530,color:current?ac:ink,opacity:p*(current?1:.4),transform:'translateX('+((1-p)*(i%2?110:-110))+'px)'}}>{resumo(b.texto,8)}</div>;})}
  <div style={{position:'absolute',right:-140,bottom:255,width:340,height:340,borderRadius:v===0?'50%':50,border:'3px solid '+ac,opacity:.25,transform:'rotate('+(q*(v===1?-20:20))+'deg)'}}/>
 </AbsoluteFill>;
};
export const TelaDividida:React.FC<Props>=({c,dur})=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig(),m=c.motion!,v=(m.variante||0)%3;
 const ac=cor(c),ink=m.claro?'#16212a':'#f8f7f2',bg=m.claro?'#f2efe9':'#0d121b';
 const texto=resumo(m.titulo||c.narracao||'',9),a=entrada(f,5,27),items=(m.batidas||[]).slice(0,3),active=items.reduce((p,b,i)=>f/fps>=b.em?i:p,0);
 const y=v===1?560:490,h=v===2?600:690;
 return <AbsoluteFill style={{background:bg,overflow:'hidden'}}>
  <div style={{position:'absolute',left:83,top:180,right:90,color:ink,fontFamily:FORTE,fontSize:fonte(texto,92),fontWeight:870,lineHeight:1.05}}>{texto}</div>
  <div style={{position:'absolute',left:v===2?180:82,top:y,width:v===2?720:910,height:h,overflow:'hidden',borderRadius:v===2?135:40,background:'#242d38',boxShadow:'0 35px 80px #0004',opacity:a,transform:'translateY('+((1-a)*125)+'px) rotate('+(v===2?-3:0)+'deg)'}}>
   {c.video||c.foto||c.recorte?<Media c={c} dur={dur}/>:<div style={{height:'100%',display:'flex',alignItems:'center',justifyContent:'center',fontFamily:FORTE,color:ac,fontSize:fonte(m.chaves[0]||'',105,700)}}>{resumo(m.chaves[0]||'',1)}</div>}
  </div>
  {items.map((b,i)=>{const e=entrada(f,b.em*fps,19);return <div key={i} style={{position:'absolute',top:(v===1?1300:1265)+i*125,left:90,right:105,display:'flex',alignItems:'center',gap:24,padding:'15px 20px',background:i===active?(m.claro?'#e3e7e1':'#232d38'):'transparent',borderLeft:'7px solid '+(i===active?ac:'transparent'),borderRadius:15,opacity:e,transform:'translateX('+((1-e)*90)+'px)',fontFamily:TEXTO,fontSize:35,color:ink}}>
   <span style={{color:ac,fontWeight:900}}>{String(i+1).padStart(2,'0')}</span>{resumo(b.texto,8)}
  </div>;})}
 </AbsoluteFill>;
};
export const CamadasProfundidade:React.FC<Props>=({c,dur})=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig(),m=c.motion!,v=(m.variante||0)%3;
 const ac=cor(c),ink=m.claro?'#18232b':'#f5f4ee',bg=m.claro?'#efede8':'#0e141c',q=f/Math.max(1,dur);
 const a=spring({frame:f,fps,config:{damping:21,stiffness:95}});
 const positions=v===0?[[115,650],[545,990],[165,1290]]:v===1?[[490,630],[120,995],[590,1280]]:[[110,700],[540,945],[180,1295]];
 const label=resumo(m.titulo||c.narracao||'',9);
 return <AbsoluteFill style={{background:bg,overflow:'hidden'}}>
  <div style={{position:'absolute',inset:-100,opacity:.16,background:'radial-gradient(ellipse at 60% 42%, '+ac+', transparent 65%)',transform:'translateX('+(q*40)+'px)'}}/>
  <div style={{position:'absolute',left:75,top:190,right:95,color:ink,fontFamily:FORTE,fontSize:fonte(label,90),lineHeight:1.05,fontWeight:900}}>{label}</div>
  {c.video||c.foto||c.recorte?<div style={{position:'absolute',left:130,top:580,width:790,height:760,opacity:.27,overflow:'hidden',borderRadius:38,transform:'translateX('+((q-.5)*45)+'px)'}}><Media c={c} dur={dur}/></div>:null}
  {positions.map(([x,y],i)=>{const e=entrada(f,8+i*11,24),text=m.chaves[i]||'';return <div key={i} style={{position:'absolute',left:x+(q-.5)*(25+i*35),top:y-(q-.5)*(25+i*37),width:i===1?480:450,height:i===1?295:230,borderRadius:28+i*9,background:i===1?ac:(m.claro?'#fffdfa':'#202b35'),border:'1px solid '+(m.claro?'#d8d5cb':'#35414a'),boxShadow:'0 '+(25+i*12)+'px '+(55+i*20)+'px #0005',display:'flex',alignItems:'center',justifyContent:'center',padding:18,textAlign:'center',fontFamily:FORTE,fontWeight:800,fontSize:fonte(text,65,420),color:i===1?'#132019':ink,opacity:e,transform:'perspective(1300px) rotateY('+(v===1?-12:9)+'deg) rotateZ('+((i-1)*4)+'deg) translateY('+((1-e)*115)+'px) scale('+(.88+.12*a)+')'}}>{text}</div>;})}
 </AbsoluteFill>;
};
export const CenaPro:React.FC<Props>=(props)=>{
 const layout=props.c.motion?.layout;
 const Component=layout==='palavra'?PalavraCinetica:layout==='dividida'?TelaDividida:CamadasProfundidade;
 return <AbsoluteFill style={{overflow:'hidden'}}><Component {...props}/></AbsoluteFill>;
};
