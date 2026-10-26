import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateData, percentage} from '../src/data.ts';
const load = (name) => JSON.parse(readFileSync(new URL(`../public/${name}.json`, import.meta.url)));
const data = () => [load('roteiro'), load('tempos_cenas'), load('palavras')];
test('dados reais do exemplo são válidos', () => assert.equal(validateData(...data()).roteiro.cenas.length, 8));
test('rejeita cenas sem intervalo ou intervalos sobrepostos', () => {
 const [r,t,p] = data();
 assert.throws(() => validateData(r,t.slice(1),p), /intervalo/);
 t[1].inicio=0;
 assert.throws(() => validateData(r,t,p), /sobreposta/);
});
test('rejeita JSON incompleto e palavras com duração inválida', () => {
 assert.throws(() => validateData({},[],[]), /título/);
 const [r,t,p] = data(); p[0].fim=p[0].inicio;
 assert.throws(() => validateData(r,t,p), /palavra 1/);
});
test('porcentagens respeitam decimais, frações e limites', () => {
 assert.equal(percentage('47,03%'),47.03);
 assert.equal(percentage('47.03%'),47.03);
 assert.equal(percentage('3/5'),60);
 assert.equal(percentage('3/0'),null);
 assert.equal(percentage('-10%'),0);
 assert.equal(percentage('120%'),100);
 assert.equal(percentage('sem número'),null);
});
