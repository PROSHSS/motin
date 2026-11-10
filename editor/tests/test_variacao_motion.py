import copy,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import criar,motion_editor as M,motion_variacao as V

class VariacaoTests(unittest.TestCase):
 def dados(self):
  textos=['Uma ideia transforma a explicação. Repare nos detalhes.','Primeiro, organize as etapas com calma.','Pesquise o assunto no aplicativo.','Proteja sua privacidade ao usar o celular.','Converse com o público durante a live.','A impressão 3D constrói a peça em camadas.','O carro percorre o trajeto da viagem.','Conecte as ideias e veja o resultado.']
  return {'titulo':'Tecnologia no dia a dia','narrado':True,'cenas':[{'tipo':'citacao','narracao':t,'duracao':4,'manchete':[]} for t in textos]}
 def planejar(self,d,ctx):return M.dirigir(copy.deepcopy(d),[],[],contexto=ctx)
 def test_reexportacao_repete_plano_congelado(self):
  with tempfile.TemporaryDirectory() as tmp:
   b=Path(tmp);d=self.dados();p=b/'projetos/a';ctx=V.preparar_direcao(d,p,b);a=self.planejar(d,ctx)
   self.assertEqual(ctx,V.preparar_direcao(d,p,b));self.assertEqual(a,self.planejar(d,ctx))
 def test_memoria_so_registra_sucessos_e_sem_duplicatas(self):
  with tempfile.TemporaryDirectory() as tmp:
   b=Path(tmp);d=self.dados();p=b/'a';ctx=V.preparar_direcao(d,p,b);self.assertEqual(V.memoria(b),[])
   out=self.planejar(d,ctx);self.assertTrue(V.registrar_sucesso(out,p,b));self.assertTrue(V.registrar_sucesso(out,p,b));self.assertEqual(len(V.memoria(b)),1)
 def test_historico_futuro_nao_muda_reexportacao(self):
  with tempfile.TemporaryDirectory() as tmp:
   b=Path(tmp);d=self.dados();ctx=V.preparar_direcao(d,b/'a',b);antes=self.planejar(d,ctx)
   ctxb=V.preparar_direcao(d,b/'b',b);V.registrar_sucesso(self.planejar(d,ctxb),b/'b',b)
   self.assertEqual(antes,self.planejar(d,V.preparar_direcao(d,b/'a',b)))
 def test_novo_pedido_muda_montagem_e_preserva_audio(self):
  with tempfile.TemporaryDirectory() as tmp:
   b=Path(tmp);p=b/'a';p.mkdir();(p/'narracao.wav').write_bytes(b'voz-aprovada');d=self.dados()
   c1=V.preparar_direcao(d,p,b);a=self.planejar(d,c1)
   c2=V.preparar_direcao(d,p,b,'a'*24);c3=V.preparar_direcao(d,p,b,'a'*24)
   self.assertNotEqual(c1['id'],c2['id']);self.assertEqual(c2,c3);self.assertEqual(c2,V.preparar_direcao(d,p,b));self.assertNotEqual(a,self.planejar(d,c2));self.assertEqual((p/'narracao.wav').read_bytes(),b'voz-aprovada')
 def test_texto_novo_gera_nova_direcao(self):
  with tempfile.TemporaryDirectory() as tmp:
   b=Path(tmp);d=self.dados();a=V.preparar_direcao(d,b/'a',b);d['cenas'][0]['narracao']='Outro começo para a história.';c=V.preparar_direcao(d,b/'a',b);self.assertNotEqual(a['id'],c['id'])
 def test_aberturas_consideram_videos_anteriores(self):
  with tempfile.TemporaryDirectory() as tmp:
   b=Path(tmp);d=self.dados();c=V.preparar_direcao(d,b/'a',b);a=self.planejar(d,c);V.registrar_sucesso(a,b/'a',b)
   c2=V.preparar_direcao(d,b/'b',b);out=self.planejar(d,c2);self.assertNotEqual(a['cenas'][0]['motion']['layout'],out['cenas'][0]['motion']['layout'])
 def test_cores_consideram_historico(self):
  with tempfile.TemporaryDirectory() as tmp:
   b=Path(tmp);d=self.dados();a=self.planejar(d,V.preparar_direcao(d,b/'a',b));V.registrar_sucesso(a,b/'a',b)
   c=self.planejar(d,V.preparar_direcao(d,b/'b',b));self.assertNotEqual(a['direcao_motion']['cor'],c['direcao_motion']['cor'])
 def test_temas_e_acoes_de_fato(self):
  cases=[('A impressora deposita o filamento em camadas.','impressao3d','produzir'),('Proteja a privacidade no aplicativo.','tecnologia','proteger'),('O carro percorre o trajeto na estrada.','mobilidade','percorrer'),('Pesquise a configuração do celular.','tecnologia','buscar'),('Converse nos comentários durante a live.','tecnologia','comunicar')]
  for t,d,a in cases:self.assertEqual(V.dominio(t),d);self.assertEqual(V.acao(t),a)
  self.assertNotEqual(V.dominio('A realidade aparece na tela.'),'financas')
 def test_todos_os_numeros_preservados(self):
  d={'titulo':'Dados','cenas':[{'tipo':'contador','narracao':f'O valor é {n}.','duracao':4,'contador':{'para':n,'rotulo':'valor'}} for n in (12,35,87)]}
  M.dirigir(d,[],[]);self.assertEqual([c['motion']['layout'] for c in d['cenas']],['dados']*3);self.assertEqual([c['contador']['para'] for c in d['cenas']],[12,35,87]);self.assertGreaterEqual(len({c['motion']['variante'] for c in d['cenas']}),2)
 def test_diagramas_e_rotulos_vem_do_roteiro(self):
  d=self.planejar(self.dados(),{'semente':55,'historico':[],'dominio':'tecnologia','id':'test','versao':V.VERSAO_DIRECAO})
  for c in d['cenas']:
   for o in c['motion']['objetos']:self.assertTrue(set(M.tokens(o['texto'])).issubset(set(M.tokens(c['narracao']))))
 def test_planos_diferem_com_semente(self):
  d=self.dados();planos=[]
  for seed in range(20):
   out=self.planejar(d,{'semente':seed,'historico':[],'dominio':'tecnologia','id':str(seed),'versao':V.VERSAO_DIRECAO})
   planos.append(tuple((c['motion']['layout'],c['motion']['variante'],c['motion']['corte'],c['motion']['acento']) for c in out['cenas']))
  self.assertEqual(len(set(planos)),20)
 def test_chave_do_conteudo_ignora_direcao_anterior(self):
  d=self.dados();h=V.identidade_conteudo(d);M.dirigir(d,[],[]);self.assertEqual(h,V.identidade_conteudo(d))
 def test_falha_de_render_nao_confirma_memoria_ou_apaga_video(self):
  class RenderFalhou(Exception):pass
  with tempfile.TemporaryDirectory() as tmp:
   b=Path(tmp);p=b/'projetos/teste';(p/'public').mkdir(parents=True);(b/'saidas').mkdir();old=b/'saidas/teste.mp4';old.write_bytes(b'video-anterior')
   d={'titulo':'Teste','narrado':True,'cenas':[{'tipo':'citacao','narracao':'Uma ideia clara.','duracao':2,'manchete':[]}]}
   (p/'roteiro.json').write_text(json.dumps(d));(p/'narracao.wav').write_bytes(b'voz-aprovada');(p/'tempos_cenas.json').write_text('[{"inicio":0,"fim":2}]');(p/'palavras.json').write_text('[{"palavra":"Uma","inicio":0,"fim":1}]');(p/'.tempos_ok').write_text('ok')
   def audio(*a):(p/'public/audio.json').write_text('{}')
   args=types.SimpleNamespace(novo=False,fatos=None,voz=None,refazer_voz=False,sem_musica=True,rerender=False)
   cfg={**criar.PADRAO,'pasta_dados':str(b),'edicao':'motion','polir_voz':False}
   with patch.object(criar,'etapa_narracao',return_value=False),patch.object(criar,'fotos_gerar'),patch.object(criar,'preparar_audio',side_effect=audio),patch.object(criar,'validar_roteiro'),patch.object(criar,'auditar_texto_tela'),patch.object(criar,'rodar',side_effect=RenderFalhou):
    with self.assertRaises(RenderFalhou):criar.produzir_showcase('Teste',args,cfg,{})
   self.assertEqual(V.memoria(b),[]);self.assertFalse((p/'.edicao_motion').exists());self.assertEqual(old.read_bytes(),b'video-anterior');self.assertEqual((p/'narracao.wav').read_bytes(),b'voz-aprovada')

if __name__=='__main__':unittest.main()
