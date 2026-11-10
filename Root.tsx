import React from 'react';
import {Composition, staticFile} from 'remotion';
import {Video, VideoProps} from './Video';
import {Showcase, ShowcaseProps, duracaoTotal} from './Showcase';

const FPS = 30;

export const Root: React.FC = () => {
  return (
    <>
    <RootShowcase />
    <Composition
      id="Documentario"
      component={Video}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={FPS * 60}
      defaultProps={{roteiro: {titulo: '', cenas: []}, tempos: [], palavras: []} as VideoProps}
      calculateMetadata={async () => {
        const [roteiro, tempos, palavras, audio, visual] = await Promise.all([
          fetch(staticFile('roteiro.json')).then((r) => r.json()),
          fetch(staticFile('tempos_cenas.json')).then((r) => r.json()),
          fetch(staticFile('palavras.json')).then((r) => r.json()),
          fetch(staticFile('audio.json'))
            .then((r) => (r.ok ? r.json() : {musica: false, sfx: false, volumeMusica: 1}))
            .catch(() => ({musica: false, sfx: false, volumeMusica: 1})),
          fetch(staticFile('visual.json'))
            .then((r) => (r.ok ? r.json() : {}))
            .catch(() => ({})),
        ]);
        const fim = tempos.length ? tempos[tempos.length - 1].fim : 60;
        return {
          durationInFrames: Math.ceil((fim + 0.5) * FPS),
          props: {roteiro, tempos, palavras, audio, visual},
        };
      }}
    />
    </>
  );
};

export const RootShowcase: React.FC = () => (
  <Composition
    id="Showcase"
    component={Showcase}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={FPS * 20}
    defaultProps={{dados: {titulo: '', acento: '#c9a24a', modo: 'claro', cenas: []}} as ShowcaseProps}
    calculateMetadata={async () => {
      const [dados, audio, tempos, palavras] = await Promise.all([
        fetch(staticFile('showcase.json')).then((r) => r.json()),
        fetch(staticFile('audio.json')).then((r) => (r.ok ? r.json() : {})).catch(() => ({})),
        fetch(staticFile('tempos_cenas.json')).then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch(staticFile('palavras.json')).then((r) => (r.ok ? r.json() : [])).catch(() => []),
      ]);
      const fps = dados.fps ?? FPS;
      return {durationInFrames: duracaoTotal(dados, tempos, fps), fps, props: {dados, audio, tempos, palavras}};
    }}
  />
);
