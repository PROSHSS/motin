import type {VideoProps} from './Video';

const object = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null;
const interval = (v: unknown): v is Record<string, unknown> & {inicio: number; fim: number} =>
  object(v) && typeof v.inicio === 'number' && Number.isFinite(v.inicio) &&
  typeof v.fim === 'number' && Number.isFinite(v.fim) && v.inicio >= 0 && v.fim > v.inicio;

export function validateData(roteiro: unknown, tempos: unknown, palavras: unknown): VideoProps {
  if (!object(roteiro) || typeof roteiro.titulo !== 'string' || !Array.isArray(roteiro.cenas) || !roteiro.cenas.length)
    throw new Error('roteiro.json: informe um título e pelo menos uma cena.');
  roteiro.cenas.forEach((c, i) => {
    if (!object(c) || !['texto', 'barras', 'hemiciclo', 'imagem'].includes(String(c.tipo)) ||
      typeof c.narracao !== 'string' || typeof c.destaque !== 'string' ||
      (c.imagem !== undefined && (typeof c.imagem !== 'string' || /(^\/|\.\.|:)/.test(c.imagem))))
      throw new Error(`roteiro.json: cena ${i + 1} inválida. Use texto, barras, hemiciclo ou imagem; imagem deve ser um caminho relativo em public/.`);
  });
  if (!Array.isArray(tempos) || tempos.length !== roteiro.cenas.length)
    throw new Error('tempos_cenas.json: deve haver um intervalo para cada cena.');
  tempos.forEach((t, i) => {
    if (!interval(t) || !object(t) || t.cena !== i + 1 || (i > 0 && t.inicio < tempos[i - 1].fim))
      throw new Error(`tempos_cenas.json: cena ${i + 1} fora de ordem, sobreposta ou com intervalo inválido.`);
  });
  if (!Array.isArray(palavras)) throw new Error('palavras.json: use uma lista de palavras com início e fim.');
  palavras.forEach((p, i) => {
    if (!interval(p) || !object(p) || typeof p.palavra !== 'string' || (i > 0 && p.inicio < palavras[i - 1].inicio))
      throw new Error(`palavras.json: palavra ${i + 1} inválida ou fora de ordem.`);
  });
  return {roteiro, tempos, palavras} as VideoProps;
}

export const percentage = (text: string): number | null => {
  const fraction = text.match(/(\d+)\s*\/\s*(\d+)/);
  if (fraction) return Number(fraction[2]) === 0 ? null : Math.max(0, Math.min(100, Number(fraction[1]) / Number(fraction[2]) * 100));
  const match = text.match(/-?\d+(?:[.,]\d+)?/);
  return match ? Math.max(0, Math.min(100, Number(match[0].replace(',', '.')))) : null;
};
