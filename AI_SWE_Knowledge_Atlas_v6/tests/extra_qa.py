from pathlib import Path
import json,networkx as nx,hashlib
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];(R/'qa_rerun').mkdir(exist_ok=True);D=json.loads((R/'src/graph_data.json').read_text());checks=[]
def ok(name,success,detail=None):
 assert success,(name,detail)
 checks.append({'test':name,'passed':True,'details':detail});print('PASS',name,detail or '')
G=nx.read_graphml(R/'data/AI_SWE_Knowledge_Graph_W193_O50_P123_AUDITED_v6_20261011.graphml')
ok('Payload fingerprint matches actual GraphML file',hashlib.sha256(Path(R/'data/AI_SWE_Knowledge_Graph_W193_O50_P123_AUDITED_v6_20261011.graphml').read_bytes()).hexdigest()==D['meta']['graphSha256'])
ok('Embedded nodes preserve every original GraphML attribute',len(D['nodes'])==len(G) and all(n['attributes']==G.nodes[n['id']] for n in D['nodes']))
edges={(s,t,str(k)):a for s,t,k,a in G.edges(keys=True,data=True)}
ok('Embedded edges preserve all endpoints keys and attributes',len(edges)==len(D['edges']) and all(edges[(D['nodes'][e['source']]['id'],D['nodes'][e['target']]['id'],e['key'])]==e['attributes'] for e in D['edges']))
ok('Graph-level metadata unchanged',G.graph==D['meta']['graphAttributes'])
ok('Current chapter display titles contain no LaTeX residue',all('\\' not in c['label'] and '{' not in c['label'] and '}' not in c['label'] for c in D['chapters']))
for n in D['nodes']:
 if not n['collection']:continue
 expected={t for _,t,a in G.out_edges(n['id'],data=True) if a['relation']=='CITED_IN_CHAPTER_BUNDLE_V6'}
 assert set(n['actual'])==expected
ok('Source actual-citation memberships independently match original edge type',True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=(__import__('os').environ.get('CHROMIUM_EXECUTABLE') or __import__('shutil').which('chromium') or None),headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':900})
 errs=[];page.on('pageerror',lambda e:errs.append(str(e)));page.set_content((R/'AI_SWE_Knowledge_Atlas_v6.html').read_text());page.wait_for_function('window.atlasDiagnostics && !atlasDiagnostics().layoutRunning')
 d=page.evaluate('atlasDiagnostics()');pos={n['id']:n for n in d['positions']};bounds=page.locator('#graph').bounding_box();cam=d['camera'];selected=False
 ids=set(d['visibleEdgeIDs'])
 for e in [e for e in D['edges'] if e['id'] in ids][:64]:
  a=pos[D['nodes'][e['source']]['id']];bb=pos[D['nodes'][e['target']]['id']];x=(a['x']+bb['x'])/2;y=(a['y']+bb['y'])/2;sx=x*cam['k']+cam['x'];sy=y*cam['k']+cam['y']
  if not(30<sx<d['canvas']['width']-40 and 100<sy<d['canvas']['height']-90):continue
  if any(abs(n['x']-x)<n['w']/2+3.05/cam['k'] and abs(n['y']-y)<n['h']/2+3.05/cam['k'] for n in pos.values()):continue
  page.mouse.click(bounds['x']+sx,bounds['y']+sy)
  if page.evaluate('atlasDiagnostics().selectedEdge!==null'):selected=True;break
 ok('Canvas edge click opens relationship inspector',selected and page.locator('#inspectorLabel').inner_text().lower()=='relationship details')
 page.wait_for_timeout(200);page.screenshot(path=str(R/'qa_rerun/edge_inspector.png'),full_page=True);page.locator('#closeInspector').click()
 d=page.evaluate('atlasDiagnostics()');x=bounds['x']+24;y=bounds['y']+80;page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+60,y+10,steps=6);page.mouse.up();after=page.evaluate('atlasDiagnostics()')
 ok('Dragging canvas pans camera',abs(after['camera']['x']-d['camera']['x']-60)<1)
 k=after['camera']['k'];page.mouse.wheel(0,-180);page.wait_for_timeout(100);ok('Mouse wheel zooms graph',page.evaluate('atlasDiagnostics().camera.k')>k)
 page.keyboard.press('f');page.keyboard.press('/');ok('Keyboard search shortcut',page.locator('#search').evaluate('(el)=>document.activeElement===el'))
 # Exercise worker-unavailable fallback using the same final HTML.
 fallback=b.new_page();fallback.evaluate('window.Worker=undefined');fallback.set_content((R/'AI_SWE_Knowledge_Atlas_v6.html').read_text());fallback.wait_for_function('window.atlasDiagnostics && !atlasDiagnostics().layoutRunning')
 ok('Worker-unavailable layout fallback',fallback.evaluate('atlasDiagnostics().visibleSources===193 && window.__atlasLastLayout.overlapPairs===0'))
 ok('Additional scenarios have no JavaScript errors',not errs,errs)
 b.close()
(R/'qa_rerun/EXTRA_QA_REPORT.json').write_text(json.dumps({'tests':checks,'tests_passed':len(checks),'status':'PASS'},indent=2))
