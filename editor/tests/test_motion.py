import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import criar,motion_editor as M,painel,showcase_gen
class MotionTests(unittest.TestCase):
 def dados(self,n=10):return {'titulo':'Edição','narrado':True,'cenas':[{'tipo':'citacao','narracao':'Uma ideia clara transforma o vídeo. Agora veja cada detalhe.','duracao':4,'manchete':[],'citacao':{'texto':'Uma ideia clara.'},'fonte':'Autor','fatos':['F1']} for _ in range(n)]}
 def test_preserva_fala_fontes_e_tempos(self):
  d=self.dados(4);antes=copy.deepcopy(d);t=[{'inicio':i*4,'fim':(i+1)*4} for i in range(4)];ts=copy.deepcopy(t);M.dirigir(d,t,[])
  for a,c in zip(antes['cenas'],d['cenas']):
   for k,v in a.items():self.assertEqual(c[k],v)
   for b in c['motion']['batidas']:self.assertTrue(set(M.tokens(b['texto'])).issubset(set(M.tokens(c['narracao']))))
  self.assertEqual(ts,t)
 def test_evitar_repeticao(self):
  d=self.dados(12);M.dirigir(d,[],[]);ls=[c['motion']['layout'] for c in d['cenas']];self.assertGreaterEqual(len(set(ls)),6);self.assertTrue(all(a!=b for a,b in zip(ls,ls[1:])))
 def test_batidas_nos_tempos_da_voz(self):
  d=self.dados(2);d['cenas'][1]['narracao']='Repare nisso. Agora tudo muda.'
  pal=[{'palavra':s,'inicio':a,'fim':b} for s,a,b in [('Repare',4.7,5),('nisso.',5,5.5),('Agora',6.8,7.1),('tudo',7.1,7.4),('muda.',7.4,8.6)]]
  M.dirigir(d,[{'inicio':0,'fim':4},{'inicio':4.6,'fim':8.8}],pal);self.assertAlmostEqual(d['cenas'][1]['motion']['batidas'][1]['em'],2.5)
 def test_preserva_documentos_e_graficos(self):
  d=self.dados(3);d['cenas'][0].update({'tipo':'grafico','grafico':{'valores':[3,6,9]}});d['cenas'][1]['tipo']='fato_documento';d['cenas'][2].update({'tipo':'classica','cena':{'tipo':'numero_gigante','destaque':'87%'}})
  M.dirigir(d,[],[]);self.assertEqual([c['motion']['layout'] for c in d['cenas']],['original']*3);self.assertEqual(d['cenas'][0]['grafico']['valores'],[3,6,9])
 def test_numero_original(self):
  d=self.dados(1);d['cenas'][0]['numero']={'valor':87,'sufixo':'%','rotulo':'do total'};M.dirigir(d,[],[]);self.assertEqual(d['cenas'][0]['motion']['layout'],'dados');self.assertEqual(d['cenas'][0]['numero']['valor'],87)
 def test_voltar_edicao_anterior(self):
  d=self.dados(3);M.dirigir(d,[],[]);M.dirigir(d,[],[],'anterior');self.assertTrue(all('motion' not in c for c in d['cenas']))
 def test_clipe_e_trecho_fixos(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'midias').mkdir();(p/'midias/a.mp4').write_bytes(b'video-real');(p/'midias_principal.json').write_text(json.dumps([{'arquivo':'midias/a.mp4','cena':2,'inicio':1.25,'fim':3.5,'duracao':5}]))
   d=self.dados(4);M.preparar_midias(p,d);self.assertEqual(d['cenas'][1]['video']['inicio'],1.25);self.assertEqual((p/'public/midias/a.mp4').read_bytes(),b'video-real');self.assertFalse(criar.quer_imagem(d['cenas'][1]));criar.validar_roteiro(p,d);self.assertIn('video',d['cenas'][1])
 def test_videos_livres_em_ordem_e_avancam(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'a.mp4').write_bytes(b'video');(p/'midias_principal.json').write_text(json.dumps([{'arquivo':'a.mp4','cena':None,'inicio':0,'fim':30,'duracao':30}]))
   d=self.dados(6);M.preparar_midias(p,d);M.dirigir(d,[{'inicio':i*4,'fim':(i+1)*4} for i in range(6)],[]);vs=[c['video'] for c in d['cenas'] if c.get('video')];self.assertEqual(len(vs),3);self.assertGreater(vs[1]['inicio'],vs[0]['inicio'])
 def test_caminho_fora_do_projeto_rejeitado(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'midias_principal.json').write_text('[{"arquivo":"../fora.mp4"}]')
   with self.assertRaises(ValueError):M.preparar_midias(p,self.dados())
 def test_trechos_invalidos(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);v=p/'a.mp4';v.touch()
   with patch('mascote.sondar_video',return_value={'duracao':4,'tem_audio':False}):
    for a,b in [(-1,2),(3,2),(1,6),('nan',2)]:
     with self.assertRaises(ValueError):M.registrar_video(p,v,1,a,b)
 def test_painel_preserva_video_em_movimento(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(painel,'pasta_base',return_value=(Path(tmp),{})),patch('mascote.sondar_video',return_value={'duracao':8,'tem_audio':True}),patch.object(painel,'quadros_do_video',side_effect=AssertionError('Não congelar vídeo.')):
   _,p,job,_,_=painel.criar_trabalho({'tema':'Edição fluida','edicao':'motion','cena_0':'2','inicio_0':'1.5','fim_0':'5'},[('a.mp4',b'video')]);m=json.loads((p/'midias_principal.json').read_text())[0];self.assertEqual(m['cena'],2);self.assertEqual(m['inicio'],1.5);self.assertEqual(m['fim'],5);self.assertEqual(job['config']['edicao'],'motion')
 def test_imagem_com_video_nao_vira_fallback(self):
  d=self.dados(1);d['cenas'][0].update({'tipo':'classica','cena':{'tipo':'imagem'},'video':{'arquivo':'a.mp4'}})
  with tempfile.TemporaryDirectory() as tmp:self.assertEqual(showcase_gen.sem_foto_faltando(d,Path(tmp)),0);self.assertIn('video',d['cenas'][0])
 def test_migracao_dos_clipes_antigos(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'cena2_antigo.mp4').write_bytes(b'video')
   with patch('mascote.sondar_video',return_value={'duracao':8,'tem_audio':True}):d=self.dados(3);M.preparar_midias(p,d)
   self.assertIn('video',d['cenas'][1]);self.assertTrue((p/'cena2_antigo.mp4').exists())
 def test_assinatura_nao_toca_audio(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'narracao.wav').write_bytes(b'voz-aprovada');d=self.dados(2);self.assertNotEqual(M.assinatura(d,p,'motion'),M.assinatura(d,p,'anterior'));M.dirigir(d,[],[]);self.assertEqual((p/'narracao.wav').read_bytes(),b'voz-aprovada')
if __name__=='__main__':unittest.main()
