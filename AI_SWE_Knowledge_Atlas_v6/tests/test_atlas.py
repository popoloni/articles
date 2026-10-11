from playwright.sync_api import sync_playwright
from pathlib import Path
import json,time,math,hashlib
BASE=Path(__file__).resolve().parents[1];QA=BASE/'qa_rerun';QA.mkdir(exist_ok=True)
D=json.loads((BASE/'src/graph_data.json').read_text());HTML=(BASE/'AI_SWE_Knowledge_Atlas_v6.html').read_text()
checks=[];errors=[];network=[]
def ok(name,value,detail=None):
 assert value, f'FAIL {name}: {detail}'
 checks.append({'test':name,'passed':True,'details':detail})
 print('PASS',name,detail or '',flush=True)
def diag(page):return page.evaluate('atlasDiagnostics()')
def settled(page):page.wait_for_function('window.atlasDiagnostics && !atlasDiagnostics().layoutRunning',timeout=20000)
def scope(page):page.locator('#tab-scope').click()
def reset(page):
 scope(page);page.locator('#resetBtn').click();settled(page)
def rels(page):page.locator('#tab-relations').click()
def overlap_count(ds):
 ps=ds['positions'];return sum(abs(a['x']-b['x'])<(a['w']+b['w'])/2+1 and abs(a['y']-b['y'])<(a['h']+b['h'])/2+1 for i,a in enumerate(ps) for b in ps[i+1:])
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=(__import__('os').environ.get('CHROMIUM_EXECUTABLE') or __import__('shutil').which('chromium') or None),headless=True,args=['--no-sandbox'])
 context=b.new_context(viewport={'width':1512,'height':982},device_scale_factor=1,accept_downloads=True,offline=True)
 page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:network.append(r.url))
 start=time.time();page.set_content(HTML,wait_until='domcontentloaded');settled(page);startup=round(time.time()-start,3)
 d=diag(page)
 ok('Default original W193 IDs only',set(d['visibleNodeIDs'])=={f'W{x:03}' for x in range(1,194)})
 ok('Full graph payload counts', (d['totalNodes'],d['totalEdges'],d['totalRelations'])==(881,5860,218))
 ok('Default readable edges',len(d['visibleEdgeIDs'])==64)
 ok('Default layout has no node overlaps',overlap_count(d)==0)
 ok('Startup offline with no external requests',not any(u.startswith(('http:','https:')) for u in network),{'seconds':startup})
 page.wait_for_timeout(250);page.screenshot(path=str(QA/'default_desktop.png'),full_page=True)
 page.locator('#sourceO').check();settled(page);ok('Add O50',diag(page)['sourceCounts']=={'W':193,'O':50,'P':0})
 page.locator('#sourceP').check();settled(page);ok('Add P123',diag(page)['sourceCounts']=={'W':193,'O':50,'P':123})
 ok('All-source layout has no node overlaps',overlap_count(diag(page))==0)
 page.locator('#printedOnly').check();settled(page);ok('Printed W193 O16 P14 subset',diag(page)['sourceCounts']=={'W':193,'O':16,'P':14})
 page.locator('#printedOnly').uncheck();settled(page);page.locator('#strictPulse').check();settled(page);ok('Strict P108 subset',diag(page)['sourceCounts']=={'W':193,'O':50,'P':108})
 page.locator('#strictPulse').uncheck();settled(page);page.locator('#sourceW').uncheck();page.locator('#sourceO').uncheck();settled(page);ok('P-only subset',diag(page)['sourceCounts']=={'W':0,'O':0,'P':123})
 reset(page)
 page.locator('#noGroups').click();settled(page);ok('No selected groups gives empty state',diag(page)['visibleSources']==0 and page.locator('#emptyState').is_visible())
 page.locator('[data-filter-group="T:Productivity"]').check();settled(page)
 expect={n['id'] for n in D['nodes'] if n['collection']=='W' and 'T:Productivity' in n['streams']}
 ok('Primary and secondary stream filter',set(diag(page)['visibleNodeIDs'])==expect,{'sources':len(expect)})
 page.locator('[data-filter-group="T:Skills & learning"]').check();settled(page)
 expect={n['id'] for n in D['nodes'] if n['collection']=='W' and any(t in n['streams'] for t in ['T:Productivity','T:Skills & learning'])}
 ok('Multi-group union is deduplicated',set(diag(page)['visibleNodeIDs'])==expect and len(diag(page)['visibleNodeIDs'])==len(expect))
 reset(page);page.locator('#allSources').click();settled(page);page.locator('[data-grouping="chapter"]').click();settled(page)
 ok('Chapter grouping retains all sources including unmapped',diag(page)['visibleSources']==366)
 page.locator('#noGroups').click();page.locator('[data-filter-group="C:C02"]').check();settled(page)
 expect={n['id'] for n in D['nodes'] if n['collection'] and 'C:C02' in n['mapped']}
 ok('Editorial chapter group exact membership',set(diag(page)['visibleNodeIDs'])==expect,{'sources':len(expect)})
 page.locator('#chapterBasis').select_option('actual');settled(page);page.locator('#noGroups').click();page.locator('[data-filter-group="C:C02"]').check();settled(page)
 expect={n['id'] for n in D['nodes'] if n['collection'] and 'C:C02' in n['actual']}
 ok('Actual v6 chapter citations exact membership',set(diag(page)['visibleNodeIDs'])==expect,{'sources':len(expect)})
 page.locator('#allGroups').click();settled(page);ok('Actual view retains uncited group',diag(page)['visibleSources']==366 and any(g['id']=='unassigned' for g in diag(page)['groups']))
 page.locator('#noGroups').click();page.locator('[data-filter-group="C:C08"]').check();settled(page)
 page.locator('#contextDetails').evaluate('(x)=>x.open=true');page.locator('#groupHubs').click();settled(page)
 ok('Actual chapter hub enabled', 'C:C08' in diag(page)['visibleNodeIDs'])
 page.wait_for_timeout(250);page.screenshot(path=str(QA/'chapter8_actual.png'),full_page=True)
 reset(page);rels(page);page.locator('#noEdges').click();settled(page);ok('Disable all edges preserves 193 nodes',diag(page)['visibleSources']==193 and len(diag(page)['visibleEdgeIDs'])==0)
 page.locator('#allEdges').click();settled(page);ok('All direct W-W links',len(diag(page)['visibleEdgeIDs'])==701)
 page.locator('[data-relation="inferred_topic_similarity"]').uncheck();settled(page);ok('Individual inferred-similarity switch',len(diag(page)['visibleEdgeIDs'])==64)
 page.locator('#relationSearch').fill('primary stream');ok('Relationship-name search shows exact matching row',page.locator('[data-rel-row]:visible').count()==1)
 page.locator('#relationSearch').fill('');page.locator('#readableEdges').click()
 scope(page);page.locator('#contextDetails').evaluate('(x)=>x.open=true');page.locator('#allContext').click();settled(page);page.locator('#allSources').click();settled(page);rels(page);page.locator('#allEdges').click();settled(page)
 d=diag(page);ok('All 881 nodes and 5860 edges reachable',len(d['visibleNodeIDs'])==881 and len(d['visibleEdgeIDs'])==5860)
 ok('Every original edge type has a control',page.locator('[data-relation]').count()==218)
 # Independent expected edge counts while exercising actual change handlers for every switch.
 isolated=page.evaluate('''() => {
 const answer=[];document.getElementById('noEdges').click();
 for(const el of document.querySelectorAll('[data-relation]')){
  el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}));
  answer.push([el.dataset.relation,atlasDiagnostics().visibleEdgeIDs.length]);
  el.checked=false;el.dispatchEvent(new Event('change',{bubbles:true}));
 }
 return answer;
}''')
 ok('Each of 218 relationship types isolated with exact count',dict(isolated)=={r['id']:r['count'] for r in D['relations']})
 page.locator('#allEdges').click();scope(page);page.locator('#layoutBtn').click();settled(page);d=diag(page)
 ok('Full-graph autolayout finite positions',all(math.isfinite(v) for n in d['positions'] for v in [n['x'],n['y']]))
 ok('Full-graph autolayout has no node overlaps',overlap_count(d)==0)
 reset(page);page.locator('#search').fill('W023');page.wait_for_timeout(300);settled(page)
 ok('Stable ID search',diag(page)['visibleNodeIDs']==['W023'])
 page.locator('.result-item').click();ok('Node inspector correct title and raw attributes','Early-2025' in page.locator('.record-title').inner_text() and page.locator('#inspectorBody .raw').count()==1)
 page.screenshot(path=str(QA/'inspector_desktop.png'),full_page=True)
 page.locator('#closeInspector').click();page.locator('#search').fill('');page.wait_for_timeout(300);settled(page);scope(page)
 # Drag a visible node at an unobscured coordinate.
 d=diag(page);bounds=page.locator('#graph').bounding_box();cam=d['camera'];target=next(n for n in d['positions'] if 120<n['x']*cam['k']+cam['x']<d['canvas']['width']-120 and 140<n['y']*cam['k']+cam['y']<d['canvas']['height']-140)
 sx=bounds['x']+target['x']*cam['k']+cam['x'];sy=bounds['y']+target['y']*cam['k']+cam['y']
 page.mouse.move(sx,sy);page.mouse.down();page.mouse.move(sx+48,sy+30,steps=12);page.mouse.up();d2=diag(page);moved=next(n for n in d2['positions'] if n['id']==target['id'])
 ok('Dragging changes coordinates and pins node',moved['pinned'] and abs(moved['x']-target['x'])>20)
 page.locator('#layoutBtn').click();settled(page);d3=diag(page);kept=next(n for n in d3['positions'] if n['id']==target['id'])
 ok('Auto-layout respects manually pinned coordinates',abs(kept['x']-moved['x'])<1e-8 and abs(kept['y']-moved['y'])<1e-8)
 # Select node through Results without narrowing search, then focus neighborhood.
 page.locator('#tab-sources').click();idx=next(i for i,n in enumerate(D['nodes']) if n['id']==target['id']);button=page.locator(f'[data-result-node="{idx}"]')
 if button.count()==0:page.locator('#moreResults').click()
 page.locator(f'[data-result-node="{idx}"]').click();page.locator('[data-detail-action="focus"]').click();settled(page)
 focusdiag=diag(page);ok('Neighborhood focus preserves selected node',target['id'] in focusdiag['visibleNodeIDs'] and focusdiag['visibleSources']<193)
 page.locator('#clearFocus').click();settled(page);page.locator('#closeInspector').click()
 # View serialization via actual download and file input.
 page.locator('#exportBtn').click()
 with page.expect_download() as info:page.locator('[data-export="view"]').click()
 viewfile=QA/'saved_view.json';info.value.save_as(str(viewfile));view=json.loads(viewfile.read_text())
 ok('Saved view stores graph hash and pin',view['graphSha256']==D['meta']['graphSha256'] and any(n['id']==target['id'] and n['pinned'] for n in view['positions']))
 with page.expect_download() as info:page.locator('[data-export="filtered"]').click()
 filteredfile=QA/'filtered_export.json';info.value.save_as(str(filteredfile));filtered=json.loads(filteredfile.read_text());ok('Filtered JSON export has original edges',len(filtered['nodes'])==193 and len(filtered['edges'])==64)
 with page.expect_download() as info:page.locator('[data-export="full"]').click()
 fullfile=QA/'full_export.json';info.value.save_as(str(fullfile));full=json.loads(fullfile.read_text())
 ok('Full JSON export includes all nodes/edges',len(full['nodes'])==881 and len(full['edges'])==5860)
 # Compare all original attrs; not merely totals.
 nodemap={n['id']:n for n in full['nodes']};edgemap={e['id']:e for e in full['edges']}
 ok('Every exported node attribute preserved',all({k:v for k,v in nodemap[n['id']].items() if k!='id'}==n['attributes'] for n in D['nodes']))
 ok('Every exported edge attribute and endpoint preserved',all({k:v for k,v in edgemap[e['id']].items() if k not in ['id','source','target','key']}==e['attributes'] and edgemap[e['id']]['source']==D['nodes'][e['source']]['id'] and edgemap[e['id']]['target']==D['nodes'][e['target']]['id'] and edgemap[e['id']]['key']==e['key'] for e in D['edges']))
 with page.expect_download() as info:page.locator('[data-export="svg"]').click()
 svgfile=QA/'visible.svg';info.value.save_as(str(svgfile))
 import xml.etree.ElementTree as ET
 root=ET.parse(svgfile).getroot();ok('SVG is valid standalone XML',root.tag.endswith('svg') and len(root.findall('.//{http://www.w3.org/2000/svg}title'))>=193)
 page.locator('#closeModal').click();reset(page)
 page.locator('#loadFile').set_input_files(str(viewfile));page.wait_for_timeout(200);settled(page);rest=diag(page)
 positions={n['id']:n for n in rest['positions']};expected={n['id']:n for n in view['positions']}
 ok('Saved view restores exact positions and pins',all(positions[n]['x']==expected[n]['x'] and positions[n]['y']==expected[n]['y'] and positions[n]['pinned']==expected[n]['pinned'] for n in positions))
 bad={**view,'graphSha256':'wrong'};badfile=QA/'wrong_graph_view.json';badfile.write_text(json.dumps(bad));before=diag(page)
 page.locator('#loadFile').set_input_files(str(badfile));page.wait_for_timeout(100);after=diag(page)
 ok('Wrong-graph view rejected without mutation',before['positions']==after['positions'] and 'fingerprint mismatch' in page.locator('#toast').inner_text())
 reset(page);page.locator('#helpBtn').click();ok('Help exposes provenance fingerprint',D['meta']['graphSha256'] in page.locator('#modalBody').inner_text());page.keyboard.press('Escape');ok('Escape closes modal',page.locator('#modalBackdrop').is_hidden())
 # Confirm there are no auto requests, including under offline browser configuration.
 ok('No page JavaScript errors',not errors,errors);ok('No external network dependencies requested',not [u for u in network if u.startswith(('http:','https:'))],network)
 # Mobile scope, layout and keyboard-independent controls.
 mobile=context.new_page(viewport={'width':390,'height':844}) if False else None
 mc=b.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True,offline=True)
 mp=mc.new_page();mp.on('pageerror',lambda e:errors.append(str(e)));mp.set_content(HTML,wait_until='domcontentloaded');settled(mp)
 ok('Mobile initial W193',diag(mp)['visibleSources']==193)
 ok('Mobile no horizontal document overflow',mp.evaluate('document.documentElement.scrollWidth<=innerWidth'))
 mp.wait_for_timeout(300);mp.screenshot(path=str(QA/'mobile_default.png'),full_page=True)
 mp.locator('#mobileMenu').click();ok('Mobile scope drawer opens',mp.locator('#sidebar').evaluate('(x)=>x.classList.contains("open")'))
 mp.locator('#sourceO').check();settled(mp);ok('Mobile collection switch',diag(mp)['visibleSources']==243)
 mp.screenshot(path=str(QA/'mobile_filters.png'),full_page=True)
 mp.locator('#sidebarMask').click(position={'x':350,'y':100});mp.locator('#zoomIn').click();ok('Mobile zoom control',diag(mp)['camera']['k']>0)
 ok('Mobile no script errors',not errors,errors)
 report={'status':'PASS','browser':'System Chromium headless','browser_version':b.version,'execution':'Offline about:blank document populated with the exact HTML file; file: navigation is blocked by the test environment administrator. No HTTP(S) requests required.','startup_seconds':startup,'tests':checks,'tests_passed':len(checks),'javascript_errors':errors,'network_requests':network,'html_sha256':hashlib.sha256(HTML.encode()).hexdigest(),'graph_sha256':D['meta']['graphSha256'],'mobile_is_emulation':True}
 (QA/'QA_REPORT.json').write_text(json.dumps(report,indent=2));b.close()
print('ALL',len(checks),'PASSED')
