(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const poses = ['explicando','feliz','professor','surpreso','pensativo','desconfiado','bravo','preocupado','ideia','positivo','estudando','ok'];
  const labels = ['Explicando','Feliz','Professor','Surpreso','Pensativo','Desconfiado','Bravo','Preocupado','Ideia','Positivo','Estudando','Tudo certo'];
  const positions = ['esquerda','direita','ambos','oculto'];
  const positionLabels = ['Esquerda','Direita','Dois cantos','Oculto'];
  const fields = [...document.querySelectorAll('#mascot-panel [id^="mascote_"]')].filter(n => n.id !== 'mascote_trocas');
  let cues = [], urls = [], audioUrl = '', selectedCue = null, voiceBusy = false;
  function options(select, values, names, selected) {
    values.forEach((value,i) => { const o = new Option(names[i],value); select.add(o); }); select.value = selected;
  }
  options(el('mascote_expressao_direita'),poses,labels,'pensativo');
  poses.forEach((pose,i) => {
    const b = document.createElement('button'); b.type='button'; b.className='mascot-pose'; b.dataset.pose=pose;
    const img=document.createElement('img');img.src='/mascotes/'+pose+'.png';img.alt='';img.loading='lazy';
    const label=document.createElement('span');label.textContent=labels[i];b.append(img,label);b.title=labels[i];
    b.onclick=()=>{el('mascote_expressao').value=pose;el('mascote_automatico').value='nao';selectedCue=null;update();save();};
    el('mascot-poses').append(b);
  });
  function save() { try { const state={cues}; fields.forEach(n=>state[n.id]=n.type==='checkbox'?n.checked:n.value);localStorage.setItem('painel_mascote_v1',JSON.stringify(state)); } catch(_){} }
  function load() { try {const state=JSON.parse(localStorage.getItem('painel_mascote_v1')||'{}');if(state.mascote_voz){state.mascote_voz='referencia';}fields.forEach(n=>{if(state[n.id]!==undefined){if(n.type==='checkbox')n.checked=!!state[n.id];else n.value=state[n.id];}});cues=Array.isArray(state.cues)?state.cues.slice(0,300).filter(c=>c&&['cena','frame'].includes(c.por)&&poses.includes(c.expressao)&&poses.includes(c.expressao_direita)&&positions.includes(c.posicao)):[];} catch(_){} }
  function serialize() { el('mascote_trocas').value=JSON.stringify(cues); }
  function update() {
    const active=el('mascote_ativo').checked;
    el('mascot-content').hidden=!active;el('mascot-details').hidden=!active;
    el('mascot-video-options').hidden=el('mascote_fundo').value!=='video';
    el('mascot-right-field').hidden=el('mascote_posicao').value!=='ambos';
    document.querySelectorAll('.mascot-pose').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.pose===el('mascote_expressao').value)));
    let state={posicao:el('mascote_posicao').value,expressao:el('mascote_expressao').value,expressao_direita:el('mascote_expressao_direita').value};
    const f=Number(el('mascot-preview-frame').value)||0;
    if(selectedCue) state={...state,...selectedCue};
    else cues.filter(c=>c.por==='frame'&&Number(c.numero)<=f).sort((a,b)=>a.numero-b.numero).forEach(c=>state={...state,...c});
    const left=el('mascot-preview-left'),right=el('mascot-preview-right');
    left.hidden=!active||!['esquerda','ambos'].includes(state.posicao);right.hidden=!active||!['direita','ambos'].includes(state.posicao);
    left.src='/mascotes/'+state.expressao+'.png';right.src='/mascotes/'+(state.posicao==='ambos'?state.expressao_direita:state.expressao)+'.png';
    [left,right].forEach(n=>{n.style.width=el('mascote_tamanho').value+'%';n.style.bottom=(Number(el('mascote_rodape').value)/1920*100)+'%';});
    el('mascot-stage').classList.toggle('moving',el('mascote_animar').value==='sim');
    el('mascot-size-label').value=el('mascote_tamanho').value+'%';el('mascot-bottom-label').value=el('mascote_rodape').value+' px';el('mascot-volume-label').value=el('mascote_volume').value+'%';
    el('mascot-stage').querySelector('.mascot-caption-preview').style.bottom=((Number(el('mascote_rodape').value)+1080*Number(el('mascote_tamanho').value)/100*450/360+35)/1920*100)+'%';
    el('mascot-preview-video').style.objectFit=el('mascote_encaixe').value;
    serialize();
  }
  function media() {
    const vid=el('mascot-preview-video'),photo=el('mascot-preview-photo');
    vid.pause();vid.removeAttribute('src');photo.removeAttribute('src');urls.forEach(URL.revokeObjectURL);urls=[];
    const video=arqs.find(a=>VID.includes(ext(a.f.name))&&!a.cena)||arqs.find(a=>VID.includes(ext(a.f.name)));
    const image=arqs.find(a=>!VID.includes(ext(a.f.name)));
    vid.hidden=!video;photo.hidden=!!video||!image;el('mascot-preview-empty').hidden=!!video||!!image;
    if(video){const u=URL.createObjectURL(video.f);urls.push(u);vid.src=u;vid.play().catch(()=>{});}
    else if(image){const u=URL.createObjectURL(image.f);urls.push(u);photo.src=u;}
    update();
  }
  function drawCues() {
    const container=el('mascot-cues');container.replaceChildren();
    cues.forEach((c,i)=>{
      const row=document.createElement('div');row.className='mascot-cue';
      function control(title,key,values,names){const label=document.createElement('label');label.textContent=title;let input;
        if(values){input=document.createElement('select');options(input,values,names,c[key]);}
        else{input=document.createElement('input');input.type='number';input.min=c.por==='cena'?'1':'0';input.max=c.por==='cena'?'100':'108000';input.step='1';input.value=c[key];}
        input.setAttribute('aria-label',title+' da troca '+(i+1));input.oninput=()=>{c[key]=key==='numero'?Number(input.value):input.value;if(key==='por'){c.numero=c.por==='cena'?Math.max(1,c.numero):Math.max(0,c.numero);drawCues();}selectedCue=null;update();save();};label.append(input);row.append(label);}
      control('Trocar por','por',['cena','frame'],['Cena','Frame']);control('Número','numero');control('Posição','posicao',positions,positionLabels);control('Expressão','expressao',poses,labels);control('À direita','expressao_direita',poses,labels);
      const actions=document.createElement('div');actions.className='mascot-cue-actions';
      const see=document.createElement('button');see.type='button';see.textContent='ver';see.title='Ver esta troca';see.onclick=()=>{selectedCue=c;if(c.por==='frame'){el('mascot-preview-frame').value=c.numero;const v=el('mascot-preview-video');if(v.duration)v.currentTime=Math.min(c.numero/30,v.duration);}update();};
      const del=document.createElement('button');del.type='button';del.textContent='×';del.setAttribute('aria-label','Remover troca '+(i+1));del.onclick=()=>{cues.splice(i,1);selectedCue=null;drawCues();update();save();};actions.append(see,del);row.append(actions);container.append(row);
    });serialize();
  }
  load();drawCues();update();
  fields.forEach(n=>n.addEventListener('input',()=>{selectedCue=null;if(n.id==='mascote_voz'){el('mascot-voice-audio').pause();el('mascot-voice-audio').hidden=true;el('mascot-voice-status').textContent='Clique em Ouvir voz para escutar a voz brasileira selecionada. A geração usa a referência no seu PC.';}if(n.id==='mascote_tom'){el('mascote_expressao').value=n.value==='divertido'?'feliz':'professor';}update();save();}));
  el('mascot-preview-frame').oninput=()=>{selectedCue=null;update();};
  el('mascot-add-cue').onclick=()=>{if(cues.length>=300)return;cues.push({por:'cena',numero:Math.max(0,...cues.filter(c=>c.por==='cena').map(c=>c.numero))+1,posicao:el('mascote_posicao').value,expressao:el('mascote_expressao').value,expressao_direita:el('mascote_expressao_direita').value});drawCues();update();save();};
  el('mascot-voice-test').onclick=async()=>{
    const b=el('mascot-voice-test'),status=el('mascot-voice-status'),audio=el('mascot-voice-audio'),voice=el('mascote_voz');audio.pause();audio.hidden=true;b.disabled=true;voice.disabled=true;voiceBusy=true;status.textContent='Gerando com sua voz de referência no PC… Aguarde; no processador pode levar alguns minutos.';
    const fd=new FormData();fd.set('token',TOKEN);fd.set('perfil',el('mascote_voz').value);
    try{const r=await fetch('/voz-mascote',{method:'POST',body:fd});if(!r.ok){const j=await r.json();throw new Error(j.erro||'Não consegui gerar a voz.');}const blob=await r.blob();if(audioUrl)URL.revokeObjectURL(audioUrl);audioUrl=URL.createObjectURL(blob);audio.src=audioUrl;audio.hidden=false;await audio.play();status.textContent='Amostra gerada com sua referência. Compare o timbre e a expressão antes de criar o vídeo.';}catch(e){status.textContent=e.message;}finally{b.disabled=false;voice.disabled=false;voiceBusy=false;}
  };
  window.addEventListener('midias-atualizadas',media);
  window.mascoteEditor={validar(){serialize();if(voiceBusy)return 'Aguarde a amostra de voz terminar antes de criar o vídeo.';if(!el('mascote_ativo').checked)return '';if(el('mascote_fundo').value==='video'&&!arqs.some(a=>VID.includes(ext(a.f.name))))return 'Adicione um vídeo para usar como fundo, ou escolha “Cenas e fotos do editor”.';if(el('mascote_falas_exatas').checked&&!el('narrativa').value.trim())return 'Escreva a narrativa do personagem, uma fala por linha.';if(el('mascote_falas_exatas').checked&&el('mascote_fundo').value!=='video')return 'Para usar falas exatas, escolha um vídeo de fundo; ou desmarque essa opção.';const seen=new Set();for(const c of cues){const k=c.por+':'+c.numero;if(!Number.isInteger(c.numero)||c.numero<(c.por==='cena'?1:0)||c.numero>(c.por==='cena'?100:108000))return 'Confira os números das trocas por cena ou frame.';if(seen.has(k))return 'Há duas trocas na mesma cena ou frame.';seen.add(k);}return '';},limpar(){localStorage.removeItem('painel_mascote_v1');fields.forEach(n=>{if(n.type==='checkbox')n.checked=n.defaultChecked;else if(n.tagName==='SELECT')n.selectedIndex=0;else n.value=n.defaultValue;});el('mascote_expressao').value='professor';el('mascote_expressao_direita').value='pensativo';cues=[];selectedCue=null;drawCues();update();}};
})();
