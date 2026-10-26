import React from 'react';
import {Composition, staticFile} from 'remotion';
import {Video, VideoProps} from './Video';
import {validateData} from './data';

async function load(name: string): Promise<unknown> {
  const response = await fetch(staticFile(name));
  if (!response.ok) throw new Error(`${name}: falha ao carregar (HTTP ${response.status}).`);
  try { return await response.json(); } catch { throw new Error(`${name}: JSON inválido.`); }
}

const FPS = 30;

export const Root: React.FC = () => {
  return (
    <Composition
      id="Documentario"
      component={Video}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={FPS * 60}
      defaultProps={{roteiro: {titulo: '', cenas: []}, tempos: [], palavras: []} as VideoProps}
      calculateMetadata={async () => {
        const [roteiro, tempos, palavras] = await Promise.all([
          load('roteiro.json'),
          load('tempos_cenas.json'),
          load('palavras.json'),
        ]);
        const data = validateData(roteiro, tempos, palavras);
        const fim = Math.max(...data.tempos.map((t) => t.fim), ...data.palavras.map((p) => p.fim));
        return {
          durationInFrames: Math.ceil((fim + 0.5) * FPS),
          props: data,
        };
      }}
    />
  );
};
