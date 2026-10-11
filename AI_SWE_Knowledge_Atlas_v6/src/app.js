(() => {
'use strict';
const D = JSON.parse(document.getElementById('graph-data').textContent);
const $ = id => document.getElementById(id);
const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number = n => n.toLocaleString('en-US');
const safeURL = s => {try{const u=new URL(s);return ['http:','https:'].includes(u.protocol)?u.href:null;}catch{return null;}};
const sourceColors={W:'#3765a0',O:'#9164b3',P:'#bc742b'};
const palette=['#397f91','#b4774b','#75699e','#9c6a88','#64836b','#6a7aa1','#8b8660','#4c8b7a','#8a748e','#537d9b','#a77467','#698558'];
const familyColors={classification:'#8098ad',similarity:'#b2bec9',comparison:'#708bb0',actual:'#398a7a',mapping:'#9299b6',dependency:'#b37d44',provenance:'#9a8e77',evidence:'#718fa4',audit:'#b77976'};
const nodeColors={themes:'#4b8392',topics:'#73889c',chapters:'#455e7b',sections:'#8797ac',teaching:'#759486',claims:'#9d8a60',audits:'#b07770',provenance:'#908099'};
const familyNames=Object.fromEntries(D.edgeFamilies.map(f=>[f.id,f.label]));
const names=new Map([...D.themes,...D.chapters].map(g=>[g.id,g.label]));
const nodes=D.nodes.map((r,i)=>({i,r,id:r.id,x:NaN,y:NaN,w:54,h:25,pinned:false,group:'',search:[r.id,r.label,r.authors,r.summary,r.year,...r.streams.map(x=>names.get(x)),r.kind].join(' ').toLowerCase()}));
const byID=new Map(nodes.map(n=>[n.id,n]));
const links=D.edges.map((e,i)=>({...e,i,s:nodes[e.source],t:nodes[e.target],lane:0}));
const adjacent=nodes.map(()=>[]);links.forEach(e=>{adjacent[e.source].push(e);if(e.target!==e.source)adjacent[e.target].push(e);});
const allThemeIDs=[...D.themes.map(g=>g.id),'unassigned'];
const allChapterIDs=[...D.chapters.map(g=>g.id),'unassigned'];
const allRelIDs=D.relations.map(r=>r.id);
const defaultState=()=>({collections:new Set(['W']),context:new Set(),themeFilters:new Set(allThemeIDs),chapterFilters:new Set(allChapterIDs),grouping:'theme',chapterBasis:'mapped',relations:new Set(allRelIDs.filter(r=>r!=='inferred_topic_similarity')),query:'',printedOnly:false,strictPulse:false,hideIsolated:false,labels:'id',hulls:true,arrows:true,pinDragged:true,opacity:30,focus:null,focusDepth:1});
let S=defaultState(), visible=[], visibleLinks=[], visibleSet=new Set(), groups=[], countsByRelation={}, facetCounts={}, selected=null, selectedEdge=null, hovered=null, hoverEdge=null;
let camera={x:0,y:0,k:1}, cw=1,ch=1,dpr=1, redrawQueued=false, worker=null, layoutToken=0, isLayingOut=false, layoutWasExplicit=false, activeTab='scope', resultsLimit=60, selectedConnLimit=40;
let lastPointer={clientX:0,clientY:0}, pendingHover=0,toastTimer, savedModalFocus=null;
let groupIndex=new Map(), resultNodes=[];
const canvas=$('graph'),ctx=canvas.getContext('2d',{alpha:false});
function toast(msg){$('toast').textContent=msg;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),4000);}
function announce(msg){$('announcer').textContent=msg;}
function colorOf(n){if(S.grouping==='theme'){let i=D.themes.findIndex(g=>g.id===n.group);if(i>=0)return palette[i];}if(S.grouping==='chapter'){let i=D.chapters.findIndex(g=>g.id===n.group);if(i>=0)return palette[i];}return n.r.collection?sourceColors[n.r.collection]:nodeColors[n.r.category]||'#778a9a';}
function enabledBase(n){
 const r=n.r;
 if(r.collection){
  if(!S.collections.has(r.collection))return false;
  if(S.printedOnly&&!r.printed)return false;
  if(S.strictPulse&&r.collection==='P'&&String(r.attributes.strict_non_pulse_derived).toLowerCase()==='false')return false;
 } else if(!S.context.has(r.category))return false;
 return !S.query||S.query.toLowerCase().split(/\s+/).filter(Boolean).every(t=>n.search.includes(t));
}
function memberships(n){if(S.grouping==='theme')return n.r.streams;if(S.grouping==='chapter')return n.r[S.chapterBasis];if(S.grouping==='collection')return [n.r.collection||n.r.category];return ['all'];}
function activeGroups(){return S.grouping==='theme'?S.themeFilters:S.chapterFilters;}
function passGroup(n){if(!['theme','chapter'].includes(S.grouping))return true;const m=memberships(n),set=activeGroups();return m.length?m.some(x=>set.has(x)):set.has('unassigned');}
function assignedGroup(n){const m=memberships(n);if(['theme','chapter'].includes(S.grouping))return m.find(x=>activeGroups().has(x))||'unassigned';return m[0]||'unassigned';}
function sizeNode(n){
 if(n.r.collection){n.w=S.labels==='title'?150:64;n.h=S.labels==='title'?42:25;}
 else {n.w=S.labels==='title'?150:92;n.h=S.labels==='title'?42:25;}
}
function switchTab(tab){activeTab=tab;for(const x of ['scope','relations','sources']){const on=x===tab;$('tab-'+x).classList.toggle('active',on);$('tab-'+x).setAttribute('aria-selected',String(on));$(x+'Pane').hidden=!on;}if(tab==='sources')renderResults();}
function setMobile(open){$('sidebar').classList.toggle('open',open);$('sidebarMask').classList.toggle('open',open);$('mobileMenu').setAttribute('aria-expanded',String(open));}
function syncControls(){
 document.querySelectorAll('[data-collection]').forEach(el=>el.checked=S.collections.has(el.dataset.collection));
 document.querySelectorAll('[data-grouping]').forEach(el=>{const on=el.dataset.grouping===S.grouping;el.classList.toggle('active',on);el.setAttribute('aria-pressed',String(on));});
 $('printedOnly').checked=S.printedOnly;$('strictPulse').checked=S.strictPulse;$('hideIsolated').checked=S.hideIsolated;$('showHulls').checked=S.hulls;$('arrows').checked=S.arrows;$('pinDragged').checked=S.pinDragged;$('labels').value=S.labels;$('edgeOpacity').value=S.opacity;$('chapterBasis').value=S.chapterBasis;$('search').value=S.query;
 document.querySelectorAll('[data-context]').forEach(el=>el.checked=S.context.has(el.dataset.context));
 updateRelationControls();
}
function buildControls(){
 $('contextList').innerHTML=D.nodeGroups.map(g=>`<label class="check-row"><input type="checkbox" data-context="${g.id}"><span class="dot" style="background:${nodeColors[g.id]}"></span><span class="text label-small">${esc(g.label)}</span><span class="count">${g.count}</span></label>`).join('');
 $('edgeFamilies').innerHTML=D.edgeFamilies.map(f=>`<details class="edge-family" data-family="${f.id}" ${['comparison','similarity'].includes(f.id)?'open':''}><summary><input type="checkbox" data-family-check="${f.id}" aria-label="Toggle all ${esc(f.label)} relationships"><span>${esc(f.label)}</span><span class="count" data-family-count="${f.id}"></span></summary><div class="children">${D.relations.filter(r=>r.family===f.id).map(r=>`<label class="check-row" data-rel-row="${esc(r.id)}" title="${esc(r.id)}"><input type="checkbox" data-relation="${esc(r.id)}" aria-label="${esc(r.id)}"><span class="stroke" style="--stroke:${familyColors[f.id]};${f.id==='similarity'?'border-top-style:dashed':''}"></span><span class="text label-small">${esc(r.label)}</span><span class="count" data-rel-count="${esc(r.id)}"></span></label>`).join('')}</div></details>`).join('');
 $('edgeFamilies').addEventListener('click',ev=>{if(ev.target.matches('[data-family-check]'))ev.stopPropagation();});
 $('edgeFamilies').addEventListener('change',ev=>{
  const el=ev.target;
  if(el.dataset.relation){el.checked?S.relations.add(el.dataset.relation):S.relations.delete(el.dataset.relation);rebuild({reseed:false});}
  else if(el.dataset.familyCheck){D.relations.filter(r=>r.family===el.dataset.familyCheck).forEach(r=>el.checked?S.relations.add(r.id):S.relations.delete(r.id));rebuild({reseed:false});}
 });
 $('contextList').addEventListener('change',ev=>{const id=ev.target.dataset.context;if(id){ev.target.checked?S.context.add(id):S.context.delete(id);rebuild();}});
 $('groupList').addEventListener('change',ev=>{if(ev.target.dataset.filterGroup){ev.target.checked?activeGroups().add(ev.target.dataset.filterGroup):activeGroups().delete(ev.target.dataset.filterGroup);rebuild();}});
}
function renderGroups(){
 const mode=S.grouping,isFacet=['theme','chapter'].includes(mode);
 $('chapterBasisWrap').hidden=mode!=='chapter';$('allGroups').disabled=!isFacet;$('noGroups').disabled=!isFacet;
 $('groupHeading').textContent={theme:'Polimi streams',chapter:'Book chapters',collection:'Collection groups',none:'Unclustered view'}[mode];
 if(!isFacet){$('groupList').innerHTML='';$('groupNote').textContent=mode==='collection'?'Node colors follow their source or context collection. Use the collection switches above to choose subsets.':'All selected nodes share one layout area. Source colors and original edge directions remain visible.';return;}
 const facetList=mode==='theme'?D.themes:D.chapters;
 const unknown=mode==='theme'?'No stream assignment':S.chapterBasis==='actual'?'No current chapter citation':'No chapter mapping';
 const showUnknown=facetCounts.unassigned>0;
 $('groupList').innerHTML=[...facetList,...(showUnknown?[{id:'unassigned',label:unknown}]:[])].map((g,i)=>`<label class="check-row" title="${esc(g.label)}"><input type="checkbox" data-filter-group="${esc(g.id)}" ${activeGroups().has(g.id)?'checked':''}><span class="dot" style="background:${g.id==='unassigned'?'#9aa6b0':palette[i%palette.length]}"></span><span class="text label-small">${g.n?`<strong>${String(g.n).padStart(2,'0')}</strong> · `:''}${esc(g.label)}</span><span class="count">${facetCounts[g.id]||0}</span></label>`).join('');
 $('groupNote').textContent=mode==='theme'?'Filters match primary or secondary stream membership. Source counts overlap; each source is drawn once.':(S.chapterBasis==='actual'?'Only v6 chapter-bundle citations determine membership. A source printed only in the bibliography may have no chapter citation.':'Includes editorial/proposed placements, not just actual citations. Switch to actual v6 citations to distinguish the two.');
}
function updateRelationControls(){
 document.querySelectorAll('[data-relation]').forEach(el=>el.checked=S.relations.has(el.dataset.relation));
 document.querySelectorAll('[data-rel-count]').forEach(el=>{const id=el.dataset.relCount;el.textContent=`${countsByRelation[id]||0} / ${D.relations.find(r=>r.id===id).count}`;});
 document.querySelectorAll('[data-family-check]').forEach(el=>{const rels=D.relations.filter(r=>r.family===el.dataset.familyCheck),on=rels.filter(r=>S.relations.has(r.id)).length;el.checked=on===rels.length;el.indeterminate=on>0&&on<rels.length;});
 document.querySelectorAll('[data-family-count]').forEach(el=>{const f=el.dataset.familyCount;el.textContent=`${visibleLinks.filter(e=>e.family===f).length} / ${D.edgeFamilies.find(r=>r.id===f).count}`;});
 $('edgeTypesCount').textContent=`${S.relations.size} / ${D.relations.length} types`;
}
function updateCaption(){
 const doc=visible.filter(n=>n.r.collection).length,aux=visible.length-doc;
 const sc=['W','O','P'].filter(c=>S.collections.has(c)).map(c=>`${c}: ${visible.filter(n=>n.r.collection===c).length}`).join(' + ')||'Context only';
 const groupLabel={theme:'Polimi thematic streams',chapter:S.chapterBasis==='actual'?'Actual v6 chapter citations':'Editorial chapter mappings',collection:'Source & context collections',none:'Unclustered network'}[S.grouping];
 $('viewCaption').innerHTML=`<strong>${esc(groupLabel)}</strong><small>${esc(sc)}${aux?' · '+aux+' context nodes':''} · ${S.relations.has('inferred_topic_similarity')?'inferred similarities enabled':'inferred similarities hidden'}${S.query?' · search active':''}</small>`;
 $('visibleDocs').textContent=number(doc);$('visibleContext').textContent=number(aux);$('visibleEdges').textContent=number(visibleLinks.length);
 $('pinCount').textContent=`${nodes.filter(n=>n.pinned).length} pinned`;
 $('focusChip').hidden=!S.focus;if(S.focus)$('focusLabel').textContent=`${S.focus} · ${S.focusDepth}-hop neighborhood`;
 $('emptyState').hidden=visible.length!==0;
 announce(`${doc} sources, ${aux} context nodes, ${visibleLinks.length} directed relationships visible.`);
}
function parallelLanes(){const pairs=new Map();for(const e of visibleLinks){const key=e.source<e.target?e.source+'|'+e.target:e.target+'|'+e.source;if(!pairs.has(key))pairs.set(key,[]);pairs.get(key).push(e);}for(const arr of pairs.values())arr.forEach((e,j)=>{e.lane=(j-(arr.length-1)/2)*6*(e.source<=e.target?1:-1);});}
function rebuild({reseed=true,fit=true,run=true}={}){
 stopLayout();
 const base=nodes.filter(enabledBase);facetCounts={};
 for(const n of base.filter(n=>n.r.collection)){let m=memberships(n);if(!m.length)m=['unassigned'];for(const g of m)facetCounts[g]=(facetCounts[g]||0)+1;}
 visible=base.filter(passGroup);visibleSet=new Set(visible.map(n=>n.i));
 visibleLinks=links.filter(e=>visibleSet.has(e.source)&&visibleSet.has(e.target)&&S.relations.has(e.relation));
 if(S.focus){
  const anchor=byID.get(S.focus);
  if(anchor&&visibleSet.has(anchor.i)){
   const keep=new Set([anchor.i]);for(let hop=0;hop<S.focusDepth;hop++){const now=new Set(keep);for(const e of visibleLinks)if(now.has(e.source)||now.has(e.target)){keep.add(e.source);keep.add(e.target);}}
   visible=visible.filter(n=>keep.has(n.i));visibleSet=new Set(visible.map(n=>n.i));visibleLinks=visibleLinks.filter(e=>visibleSet.has(e.source)&&visibleSet.has(e.target));
  }else S.focus=null;
 }
 if(S.hideIsolated){const connected=new Set(visibleLinks.flatMap(e=>[e.source,e.target]));visible=visible.filter(n=>connected.has(n.i));visibleSet=new Set(visible.map(n=>n.i));}
 for(const n of visible){n.group=assignedGroup(n);sizeNode(n);}
 countsByRelation={};for(const e of visibleLinks)countsByRelation[e.relation]=(countsByRelation[e.relation]||0)+1;
 parallelLanes();renderGroups();syncControls();updateCaption();resultsLimit=60;renderResults();
 if(selected!==null&&$('inspector').classList.contains('open'))renderNodeDetails(nodes[selected],false);
 if(selectedEdge!==null&&$('inspector').classList.contains('open'))renderEdgeDetails(links[selectedEdge],false);
 if(visible.length){
  const mustSeed=reseed||visible.some(n=>!Number.isFinite(n.x));
  if(mustSeed)seedLayout();else recomputeGroupBounds();
  if(fit&&mustSeed)fitGraph(false);
  if(run&&mustSeed)startLayout(false,false);
 }else groups=[];
 requestDraw();
}
function groupLabel(id){if(id==='unassigned')return S.grouping==='chapter'?(S.chapterBasis==='actual'?'No current chapter citation':'No chapter mapping'):'No stream assignment';if(id==='all')return 'All visible nodes';if(names.has(id)){const chapter=D.chapters.find(c=>c.id===id);return chapter?`${String(chapter.n).padStart(2,'0')} · ${chapter.label}`:names.get(id);}return {W:'W · Polimi bibliography',O:'O · Addy Osmani',P:'P · The Pragmatic Engineer'}[id]||D.nodeGroups.find(g=>g.id===id)?.label||id;}
function orderedGroups(){const map=new Map();for(const n of visible){if(!map.has(n.group))map.set(n.group,[]);map.get(n.group).push(n);}const order=S.grouping==='theme'?allThemeIDs:S.grouping==='chapter'?allChapterIDs:S.grouping==='collection'?['W','O','P',...D.nodeGroups.map(g=>g.id)]:['all'];return [...map].sort((a,b)=>order.indexOf(a[0])-order.indexOf(b[0])).map(([id,ns])=>({id,nodes:ns,label:groupLabel(id),color:colorOf(ns[0])}));}
// Deterministic balanced area partition. Groups are display regions, not added graph nodes.
function partition(items,x,y,w,h,out){
 const total=items.reduce((s,g)=>s+g.weight,0),factor=w*h/total;
 let pending=[...items].sort((a,b)=>b.weight-a.weight).map(g=>({...g,area:g.weight*factor})),rx=x,ry=y,rw=w,rh=h;
 function worst(row,side){const sum=row.reduce((s,g)=>s+g.area,0),max=Math.max(...row.map(g=>g.area)),min=Math.min(...row.map(g=>g.area));return Math.max(side*side*max/(sum*sum),sum*sum/(side*side*min));}
 while(pending.length){
  const side=Math.min(rw,rh);let row=[pending.shift()];
  while(pending.length&&worst([...row,pending[0]],side)<=worst(row,side))row.push(pending.shift());
  const sum=row.reduce((s,g)=>s+g.area,0);
  if(rw>=rh){const sw=sum/rh;let yy=ry;for(const g of row){const hh=g.area/sw;out.push({...g,x:rx,y:yy,w:sw,h:hh});yy+=hh;}rx+=sw;rw-=sw;}
  else{const sh=sum/rw;let xx=rx;for(const g of row){const ww=g.area/sh;out.push({...g,x:xx,y:ry,w:ww,h:sh});xx+=ww;}ry+=sh;rh-=sh;}
 }
}
function arrangeOrder(ns){
 // Breadth-first walk brings directly related nodes together, without creating edges.
 const permitted=new Set(ns.map(n=>n.i)), seen=new Set(),result=[];
 const deg=n=>adjacent[n.i].filter(e=>S.relations.has(e.relation)&&permitted.has(e.source===n.i?e.target:e.source)).length;
 const starts=[...ns].sort((a,b)=>deg(b)-deg(a)||a.id.localeCompare(b.id));
 for(const start of starts){if(seen.has(start.i))continue;const queue=[start];seen.add(start.i);for(let q=0;q<queue.length;q++){const n=queue[q];result.push(n);const next=adjacent[n.i].filter(e=>S.relations.has(e.relation)).map(e=>nodes[e.source===n.i?e.target:e.source]).filter(t=>permitted.has(t.i)&&!seen.has(t.i)).sort((a,b)=>a.id.localeCompare(b.id));for(const t of next)if(!seen.has(t.i)){seen.add(t.i);queue.push(t);}}}
 return result;
}
function seedLayout(){
 let list=orderedGroups();if(!list.length){groups=[];return;}
 const maxW=Math.max(...visible.map(n=>n.w)),maxH=Math.max(...visible.map(n=>n.h));
 list=list.map(g=>({...g,weight:g.nodes.length*(maxW+17)*(maxH+17)+10500}));
 let W=Math.max(380,cw-65),H=Math.max(360,ch-175),scale=Math.max(1,Math.sqrt(list.reduce((s,g)=>s+g.weight,0)/(W*H)));
 W*=scale;H*=scale;let rects=[];
 for(let attempt=0;attempt<14;attempt++){
  rects=[];partition(list,0,0,W,H,rects);let good=true;
  for(const g of rects){g.x+=7;g.y+=7;g.w-=14;g.h-=14;g.cols=Math.max(1,Math.floor((g.w-25)/(maxW+15)));g.rows=Math.ceil(g.nodes.length/g.cols);if(g.w<maxW+38||g.h<g.rows*(maxH+13)+65)good=false;}
  if(good)break;W*=1.13;H*=1.13;
 }
 groups=rects;groupIndex=new Map(groups.map(g=>[g.id,g]));
 for(const g of groups){
  const order=arrangeOrder(g.nodes),dx=(g.w-26)/g.cols,dy=(g.h-62)/g.rows;
  order.forEach((n,i)=>{let col=i%g.cols,row=Math.floor(i/g.cols);if(row%2)col=g.cols-1-col;const x=g.x+13+(col+.5)*dx,y=g.y+49+(row+.5)*dy;n.homeX=x;n.homeY=y;if(!n.pinned){n.x=x;n.y=y;}n.box={x:g.x+9,y:g.y+44,w:g.w-18,h:g.h-53};});
 }
}
function recomputeGroupBounds(){
 groups=orderedGroups().map(g=>{const x=Math.min(...g.nodes.map(n=>n.x-n.w/2))-15,y=Math.min(...g.nodes.map(n=>n.y-n.h/2))-45;return {...g,x,y,w:Math.max(...g.nodes.map(n=>n.x+n.w/2))+15-x,h:Math.max(...g.nodes.map(n=>n.y+n.h/2))+15-y};});groupIndex=new Map(groups.map(g=>[g.id,g]));
}
// The same solver runs in an inline worker, with a synchronous fallback.
function solveLayout(payload,report){
 const ns=payload.nodes.map(n=>({...n,vx:0,vy:0})),es=payload.edges,iterations=220,gap=10;
 const cellSize=Math.max(120,...ns.map(n=>n.w+gap+5));
 function collision(pass=1){
  for(let iteration=0;iteration<pass;iteration++){
   const grid=new Map();
   ns.forEach((n,i)=>{const k=Math.floor(n.x/cellSize)+','+Math.floor(n.y/cellSize);if(!grid.has(k))grid.set(k,[]);grid.get(k).push(i);});
   for(let i=0;i<ns.length;i++){
    const a=ns[i],gx=Math.floor(a.x/cellSize),gy=Math.floor(a.y/cellSize);
    for(let ix=gx-1;ix<=gx+1;ix++)for(let iy=gy-1;iy<=gy+1;iy++)for(const j of grid.get(ix+','+iy)||[]){
     if(j<=i)continue;const b=ns[j];if(a.pinned&&b.pinned)continue;
     const dx=b.x-a.x,dy=b.y-a.y,ox=(a.w+b.w)/2+gap-Math.abs(dx),oy=(a.h+b.h)/2+gap-Math.abs(dy);if(ox<=0||oy<=0)continue;
     const part=a.pinned||b.pinned?1:.5;
     if(ox<oy){const d=(dx===0?(i%2?1:-1):Math.sign(dx))*(ox+.01)*part;if(!a.pinned)a.x-=d;if(!b.pinned)b.x+=d;}
     else{const d=(dy===0?(i%2?1:-1):Math.sign(dy))*(oy+.01)*part;if(!a.pinned)a.y-=d;if(!b.pinned)b.y+=d;}
    }
   }
  }
 }
 for(let step=0;step<iterations;step++){
  const alpha=1-step/iterations;
  for(const n of ns)if(!n.pinned){n.vx+=(n.hx-n.x)*.016*alpha;n.vy+=(n.hy-n.y)*.016*alpha;}
  for(const [a,b] of es){const s=ns[a],t=ns[b];if(s.g!==t.g)continue;const dx=t.x-s.x,dy=t.y-s.y,dist=Math.hypot(dx,dy)||1,target=(s.w+t.w)/2+28;const f=(dist-target)/dist*.012*alpha;if(!s.pinned){s.vx+=dx*f;s.vy+=dy*f;}if(!t.pinned){t.vx-=dx*f;t.vy-=dy*f;}}
  for(const n of ns)if(!n.pinned){n.vx*=.55;n.vy*=.55;n.x+=Math.max(-4,Math.min(4,n.vx));n.y+=Math.max(-4,Math.min(4,n.vy));const b=n.box;n.x=Math.max(b.x+n.w/2,Math.min(b.x+b.w-n.w/2,n.x));n.y=Math.max(b.y+n.h/2,Math.min(b.y+b.h-n.h/2,n.y));}
  collision(step>180?3:1);
  if(step%22===21)report({progress:(step+1)/iterations,positions:ns.map(n=>[n.x,n.y])});
 }
 collision(50);
 // Deterministic clearance pass: a heavily linked claim cluster can remain
 // congested after relaxation. Keep pins untouched and move only conflicting
 // free nodes into vacant positions, preferring their own display region.
 const placed=ns.filter(n=>n.pinned);
 function free(n,x,y){return placed.every(a=>Math.abs(x-a.x)>=(n.w+a.w)/2+gap||Math.abs(y-a.y)>=(n.h+a.h)/2+gap);}
 for(const n of ns){
  if(n.pinned)continue;
  if(!free(n,n.x,n.y)){
   let found=false;
   const tryPoint=(x,y,bounded)=>{const b=n.box;if(bounded&&(x-n.w/2<b.x||x+n.w/2>b.x+b.w||y-n.h/2<b.y||y+n.h/2>b.y+b.h))return false;if(free(n,x,y)){n.x=x;n.y=y;return true;}return false;};
   found=tryPoint(n.hx,n.hy,true);
   for(let ring=1;!found&&ring<=30;ring++)for(let j=0;!found&&j<16;j++){const a=j*Math.PI/8;found=tryPoint(n.hx+Math.cos(a)*ring*(n.w+gap),n.hy+Math.sin(a)*ring*(n.h+gap),true);}
   for(let ring=1;!found&&ring<=150;ring++)for(let j=0;!found&&j<16;j++){const a=j*Math.PI/8;found=tryPoint(n.hx+Math.cos(a)*ring*(n.w+gap),n.hy+Math.sin(a)*ring*(n.h+gap),false);}
  }
  placed.push(n);
 }
 let overlap=0;for(let i=0;i<ns.length;i++)for(let j=i+1;j<ns.length;j++)if(Math.abs(ns[i].x-ns[j].x)<(ns[i].w+ns[j].w)/2+2&&Math.abs(ns[i].y-ns[j].y)<(ns[i].h+ns[j].h)/2+2)overlap++;
 report({progress:1,done:true,overlap,positions:ns.map(n=>[n.x,n.y])});
}
function stopLayout(){layoutToken++;if(worker){worker.terminate();worker=null;}isLayingOut=false;$('progress').style.width='0';$('layoutLabel').textContent='Auto-layout';$('layoutBtn').setAttribute('aria-busy','false');}
function startLayout(explicit=true,reseed=true){
 stopLayout();if(!visible.length)return;
 if(reseed){seedLayout();fitGraph(false);requestDraw();}
 const current=[...visible],index=new Map(current.map((n,i)=>[n.i,i]));
 const payload={nodes:current.map(n=>({x:n.x,y:n.y,w:n.w,h:n.h,pinned:n.pinned,hx:n.homeX??n.x,hy:n.homeY??n.y,g:n.group,box:n.box||{x:n.x-200,y:n.y-200,w:400,h:400}})),edges:visibleLinks.map(e=>[index.get(e.source),index.get(e.target)])};
 const token=++layoutToken;isLayingOut=true;layoutWasExplicit=explicit;$('layoutLabel').textContent='Stop layout';$('layoutBtn').setAttribute('aria-busy','true');$('progress').style.width='3%';
 const onMessage=msg=>{
  if(token!==layoutToken)return;
  msg.positions?.forEach((p,i)=>{current[i].x=p[0];current[i].y=p[1];});$('progress').style.width=`${msg.progress*100}%`;requestDraw();
  if(msg.done){isLayingOut=false;if(worker){worker.terminate();worker=null;}$('layoutLabel').textContent='Auto-layout';$('layoutBtn').setAttribute('aria-busy','false');setTimeout(()=>{if(token===layoutToken)$('progress').style.width='0';},200);if(explicit)toast(msg.overlap?`Layout complete · ${msg.overlap} overlapping node pairs. Release pins to give the layout more freedom.`:'Layout complete · no overlapping node bounds.');if(groups.length===1){recomputeGroupBounds();fitGraph(false);}window.__atlasLastLayout={nodes:current.length,overlapPairs:msg.overlap,completed:true};}
 };
 try{const blob=new Blob([`const solveLayout=${solveLayout.toString()};onmessage=e=>solveLayout(e.data,m=>postMessage(m));`],{type:'application/javascript'}),url=URL.createObjectURL(blob);worker=new Worker(url);URL.revokeObjectURL(url);worker.onmessage=e=>onMessage(e.data);worker.onerror=()=>{if(worker)worker.terminate();worker=null;setTimeout(()=>{if(token===layoutToken)solveLayout(payload,onMessage);},0);};worker.postMessage(payload);}catch{setTimeout(()=>{if(token===layoutToken)solveLayout(payload,onMessage);},0);}
}
function boardSize(){const r=$('board').getBoundingClientRect();cw=r.width;ch=r.height;dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(cw*dpr);canvas.height=Math.round(ch*dpr);requestDraw();}
function fitGraph(animate=true){
 if(!visible.length)return;
 const inspectorW=$('inspector').classList.contains('open')&&cw>600?350:0;
 const x0=Math.min(...visible.map(n=>n.x-n.w/2),...groups.map(g=>g.x)),x1=Math.max(...visible.map(n=>n.x+n.w/2),...groups.map(g=>g.x+g.w));
 const y0=Math.min(...visible.map(n=>n.y-n.h/2),...groups.map(g=>g.y)),y1=Math.max(...visible.map(n=>n.y+n.h/2),...groups.map(g=>g.y+g.h));
 const availW=Math.max(160,cw-inspectorW-44),availH=Math.max(150,ch-170),k=Math.max(.08,Math.min(2.2,availW/Math.max(100,x1-x0),availH/Math.max(100,y1-y0)));
 camera={k,x:22+(availW-(x1-x0)*k)/2-x0*k,y:91+(availH-(y1-y0)*k)/2-y0*k};requestDraw();
}
function zoom(factor,x=cw/2,y=ch/2){const k=Math.max(.07,Math.min(6,camera.k*factor)),ratio=k/camera.k;camera.x=x-(x-camera.x)*ratio;camera.y=y-(y-camera.y)*ratio;camera.k=k;requestDraw();}
function centerNode(n){const aw=$('inspector').classList.contains('open')&&cw>600?cw-350:cw;camera.k=Math.max(camera.k,1.35);camera.x=aw/2-n.x*camera.k;camera.y=ch/2-n.y*camera.k;requestDraw();}
function requestDraw(){if(!redrawQueued){redrawQueued=true;requestAnimationFrame(()=>{redrawQueued=false;draw();});}}
function roundedRect(c,x,y,w,h,r){r=Math.max(0,Math.min(r,w/2,h/2));c.beginPath();c.moveTo(x+r,y);c.lineTo(x+w-r,y);c.quadraticCurveTo(x+w,y,x+w,y+r);c.lineTo(x+w,y+h-r);c.quadraticCurveTo(x+w,y+h,x+w-r,y+h);c.lineTo(x+r,y+h);c.quadraticCurveTo(x,y+h,x,y+h-r);c.lineTo(x,y+r);c.quadraticCurveTo(x,y,x+r,y);c.closePath();}
function clipText(text,width,font){ctx.font=font;let s=String(text);if(ctx.measureText(s).width<=width)return s;while(s.length&&ctx.measureText(s+'…').width>width)s=s.slice(0,-1);return s+'…';}
function edgeGeometry(e){
 const s=e.s,t=e.t,dx=t.x-s.x,dy=t.y-s.y,dist=Math.hypot(dx,dy)||1,nx=dx/dist,ny=dy/dist;
 if(s.i===t.i)return {sx:s.x+s.w/2,sy:s.y,tx:s.x,ty:s.y-s.h/2,cx:s.x+s.w,cy:s.y-s.h*2,loop:true};
 const ar=Math.min((s.w/2+1.5)/Math.max(Math.abs(nx),.0001),(s.h/2+1.5)/Math.max(Math.abs(ny),.0001)),br=Math.min((t.w/2+1.5)/Math.max(Math.abs(nx),.0001),(t.h/2+1.5)/Math.max(Math.abs(ny),.0001));
 const offset=e.lane;
 return {sx:s.x+nx*ar,sy:s.y+ny*ar,tx:t.x-nx*br,ty:t.y-ny*br,cx:(s.x+t.x)/2-ny*offset,cy:(s.y+t.y)/2+nx*offset};
}
function isDashed(e){return ['similarity','comparison'].includes(e.family)||e.relation.includes('PROPOSAL')||e.relation.includes('CANDIDATE');}
function draw(){
 ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#f8fafb';ctx.fillRect(0,0,cw,ch);
 // Quiet grid, drawn in screen space; no image or font dependencies.
 ctx.fillStyle='#dae3e9';let grid=24*camera.k;while(grid<17)grid*=2;while(grid>40)grid/=2;const ox=((camera.x%grid)+grid)%grid,oy=((camera.y%grid)+grid)%grid;
 for(let x=ox;x<cw;x+=grid)for(let y=oy;y<ch;y+=grid)ctx.fillRect(x,y,.8,.8);
 ctx.save();ctx.translate(camera.x,camera.y);ctx.scale(camera.k,camera.k);
 if(S.hulls&&S.grouping!=='none')for(const g of groups){
  ctx.fillStyle=g.color+'09';ctx.strokeStyle=g.color+'29';ctx.lineWidth=1/camera.k;roundedRect(ctx,g.x,g.y,g.w,g.h,11);ctx.fill();ctx.stroke();
  const fs=Math.max(10,10/camera.k),font=`600 ${fs}px "Segoe UI",Arial,sans-serif`;ctx.font=font;ctx.fillStyle=g.color;ctx.textAlign='left';ctx.textBaseline='top';
  const count=String(g.nodes.length),countW=ctx.measureText(count).width;ctx.fillText(clipText(g.label,g.w-37-countW,font),g.x+13,g.y+12);ctx.globalAlpha=.7;ctx.textAlign='right';ctx.fillText(count,g.x+g.w-12,g.y+12);ctx.globalAlpha=1;
 }
 let highlight=null;
 if(selected!==null&&visibleSet.has(selected)){highlight=new Set([selected]);for(const e of visibleLinks)if(e.source===selected||e.target===selected){highlight.add(e.source);highlight.add(e.target);}}
 const activeEdge=selectedEdge!==null?selectedEdge:hoverEdge;
 for(const e of visibleLinks){
  const connected=selected!==null&&(e.source===selected||e.target===selected),active=e.i===activeEdge;
  ctx.globalAlpha=active ? .96 : connected ? .8 : highlight ? .075 : S.opacity/100;
  ctx.strokeStyle=active?'#264654':familyColors[e.family];ctx.lineWidth=(active?2.4:connected?1.6:e.family==='similarity' ? .7 : 1)/camera.k;ctx.setLineDash(isDashed(e)?[4/camera.k,4/camera.k]:[]);
  const p=edgeGeometry(e);ctx.beginPath();ctx.moveTo(p.sx,p.sy);ctx.quadraticCurveTo(p.cx,p.cy,p.tx,p.ty);ctx.stroke();
  if(S.arrows&&(camera.k>.75||active||connected)){const a=Math.atan2(p.ty-p.cy,p.tx-p.cx),len=(active?7:4.5)/camera.k;ctx.setLineDash([]);ctx.fillStyle=ctx.strokeStyle;ctx.beginPath();ctx.moveTo(p.tx,p.ty);ctx.lineTo(p.tx-len*Math.cos(a-.42),p.ty-len*Math.sin(a-.42));ctx.lineTo(p.tx-len*Math.cos(a+.42),p.ty-len*Math.sin(a+.42));ctx.closePath();ctx.fill();}
 }
 ctx.setLineDash([]);ctx.globalAlpha=1;
 for(const n of visible){
  const screenX=n.x*camera.k+camera.x,screenY=n.y*camera.k+camera.y;if(screenX<-180||screenY<-90||screenX>cw+180||screenY>ch+90)continue;
  const chosen=n.i===selected,over=n.i===hovered,color=colorOf(n),activeRelated=highlight===null||highlight.has(n.i),alpha=activeRelated?1:.35;
  ctx.globalAlpha=alpha;ctx.fillStyle=chosen?color:'#ffffff';ctx.strokeStyle=chosen?color:over?'#26485d':color+'99';ctx.lineWidth=(chosen?2.3:over?1.7:1.05)/camera.k;
  if(chosen||over){ctx.shadowColor='#203a5522';ctx.shadowBlur=9/camera.k;ctx.shadowOffsetY=2/camera.k;}
  roundedRect(ctx,n.x-n.w/2,n.y-n.h/2,n.w,n.h,n.r.collection?5:2.5);ctx.fill();ctx.stroke();ctx.shadowBlur=0;ctx.shadowOffsetY=0;
  if(n.r.collection){ctx.fillStyle=chosen?'#ffffffbb':sourceColors[n.r.collection];ctx.beginPath();ctx.arc(n.x-n.w/2+6,n.y-(S.labels==='title'?8:0),1.9/camera.k,0,Math.PI*2);ctx.fill();}
  if(S.labels!=='none'&&camera.k>.32){
   const fs=Math.min(19,Math.max(10.5,8.7/camera.k));ctx.fillStyle=chosen?'#fff':'#263d51';ctx.textBaseline='middle';ctx.textAlign='center';
   let label=n.id;
   if(!n.r.collection){if(n.r.kind==='chapter')label=n.id.replace('C:C','CH ');else if(n.r.kind==='section')label=n.id.replace('S:','§ ');else label=n.r.kind==='theme'||n.r.kind==='topic'?n.r.label:n.r.kind.replaceAll('_',' ');}
   const font=`${n.r.collection?'650':'500'} ${fs}px "Segoe UI",Arial,sans-serif`;ctx.font=font;
   ctx.fillText(clipText(label,n.w-16,font),n.x+(n.r.collection?2:0),n.y-(S.labels==='title'?8:0));
   if(S.labels==='title'&&camera.k>.47){const tf=`${Math.max(9,8/camera.k)}px "Segoe UI",Arial,sans-serif`;ctx.fillStyle=chosen?'#ffffffe0':'#627388';ctx.fillText(clipText(n.r.label,n.w-13,tf),n.x,n.y+10);}
  }
  if(n.pinned){ctx.fillStyle=chosen?'#fff':color;ctx.beginPath();ctx.arc(n.x+n.w/2-2,n.y-n.h/2+2,3/camera.k,0,Math.PI*2);ctx.fill();}
 }
 ctx.globalAlpha=1;ctx.restore();$('zoomValue').textContent=Math.round(camera.k*100)+'%';
}
function pointerWorld(ev){const r=canvas.getBoundingClientRect();return {x:(ev.clientX-r.left-camera.x)/camera.k,y:(ev.clientY-r.top-camera.y)/camera.k,sx:ev.clientX-r.left,sy:ev.clientY-r.top};}
function hitNode(p){for(let i=visible.length-1;i>=0;i--){const n=visible[i];if(Math.abs(p.x-n.x)<=n.w/2+3/camera.k&&Math.abs(p.y-n.y)<=n.h/2+3/camera.k)return n;}return null;}
function segmentDistance(px,py,ax,ay,bx,by){const dx=bx-ax,dy=by-ay,len=dx*dx+dy*dy,t=len?Math.max(0,Math.min(1,((px-ax)*dx+(py-ay)*dy)/len)):0;return Math.hypot(px-ax-t*dx,py-ay-t*dy);}
function hitEdge(p){let best=null,distance=5/camera.k;for(const e of visibleLinks){const g=edgeGeometry(e);if(p.x<Math.min(g.sx,g.tx,g.cx)-distance||p.x>Math.max(g.sx,g.tx,g.cx)+distance||p.y<Math.min(g.sy,g.ty,g.cy)-distance||p.y>Math.max(g.sy,g.ty,g.cy)+distance)continue;let ax=g.sx,ay=g.sy;for(let k=1;k<=10;k++){const t=k/10,u=1-t,bx=u*u*g.sx+2*u*t*g.cx+t*t*g.tx,by=u*u*g.sy+2*u*t*g.cy+t*t*g.ty,d=segmentDistance(p.x,p.y,ax,ay,bx,by);if(d<distance){distance=d;best=e;}ax=bx;ay=by;}}return best;}
function tooltip(n,e,ev){const tip=$('tooltip');if(!n&&!e){tip.classList.remove('visible');return;}if(n){tip.innerHTML=`<b>${esc(n.id)} · ${esc(n.r.collection?({W:'Polimi',O:'Osmani',P:'Pragmatic Engineer'}[n.r.collection]):n.r.kind.replaceAll('_',' '))}</b><div class="tip-title">${esc(n.r.label)}</div><small>${esc(n.r.authors||n.r.summary.slice(0,140))}</small><small>${n.pinned?'Pinned · double-click to release':'Click to inspect · drag to position'}</small>`;}else{tip.innerHTML=`<b>${esc(e.s.id)} → ${esc(e.t.id)}</b><div class="tip-title">${esc(e.relation)}</div><small>${esc((e.attributes.rationale||e.attributes.provenance||'Original directed graph relationship').slice(0,250))}</small><small>Click to inspect the original relationship.</small>`;}
 tip.classList.add('visible');const r=tip.getBoundingClientRect();tip.style.left=Math.min(window.innerWidth-r.width-12,Math.max(12,ev.clientX+15))+'px';tip.style.top=Math.min(window.innerHeight-r.height-12,Math.max(12,ev.clientY+18))+'px';}
let drag=null, pointers=new Map(), pinch=null;
canvas.addEventListener('pointerdown',ev=>{
 if(ev.button!==0)return;canvas.focus({preventScroll:true});pointers.set(ev.pointerId,{x:ev.clientX,y:ev.clientY});canvas.setPointerCapture(ev.pointerId);tooltip(null,null,ev);
 if(pointers.size===2){const a=[...pointers.values()];pinch={dist:Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y),x:(a[0].x+a[1].x)/2,y:(a[0].y+a[1].y)/2};drag=null;return;}
 const p=pointerWorld(ev),n=hitNode(p);if(n)stopLayout();drag={id:ev.pointerId,n,startX:ev.clientX,startY:ev.clientY,x:n?n.x:camera.x,y:n?n.y:camera.y,moved:false};canvas.style.cursor=n?'grabbing':'grabbing';
});
canvas.addEventListener('pointermove',ev=>{
 lastPointer={clientX:ev.clientX,clientY:ev.clientY};
 if(pointers.has(ev.pointerId))pointers.set(ev.pointerId,{x:ev.clientX,y:ev.clientY});
 if(pinch&&pointers.size>=2){const a=[...pointers.values()],dist=Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y),x=(a[0].x+a[1].x)/2,y=(a[0].y+a[1].y)/2,r=canvas.getBoundingClientRect();zoom(dist/Math.max(1,pinch.dist),pinch.x-r.left,pinch.y-r.top);camera.x+=x-pinch.x;camera.y+=y-pinch.y;pinch={dist,x,y};requestDraw();return;}
 if(drag){const dx=ev.clientX-drag.startX,dy=ev.clientY-drag.startY;if(Math.hypot(dx,dy)>3)drag.moved=true;if(drag.moved){if(drag.n){drag.n.x=drag.x+dx/camera.k;drag.n.y=drag.y+dy/camera.k;if(S.pinDragged)drag.n.pinned=true;}else{camera.x=drag.x+dx;camera.y=drag.y+dy;}requestDraw();}return;}
 if(pendingHover)return;pendingHover=requestAnimationFrame(()=>{pendingHover=0;const p=pointerWorld(lastPointer),n=hitNode(p),e=n?null:hitEdge(p);const ni=n?.i??null,ei=e?.i??null;if(hovered!==ni||hoverEdge!==ei){hovered=ni;hoverEdge=ei;requestDraw();}canvas.style.cursor=n?'grab':e?'pointer':'default';tooltip(n,e,lastPointer);});
});
function pointerEnd(ev){pointers.delete(ev.pointerId);if(pinch){if(pointers.size<2)pinch=null;drag=null;return;}if(drag){if(!drag.moved){const p=pointerWorld(ev),n=hitNode(p);if(n)selectNode(n);else{const e=hitEdge(p);if(e)selectEdge(e);else clearSelection();}}else if(drag.n){updateCaption();if(selected===drag.n.i)renderNodeDetails(drag.n,false);}drag=null;}canvas.style.cursor='default';}
canvas.addEventListener('pointerup',pointerEnd);canvas.addEventListener('pointercancel',ev=>{pointers.delete(ev.pointerId);drag=null;pinch=null;});
canvas.addEventListener('pointerleave',ev=>{if(!drag){hovered=null;hoverEdge=null;tooltip(null,null,ev);requestDraw();}});
canvas.addEventListener('dblclick',ev=>{const n=hitNode(pointerWorld(ev));if(n){n.pinned=!n.pinned;updateCaption();if(selected===n.i)renderNodeDetails(n,false);toast(n.id+(n.pinned?' pinned.':' released.'));requestDraw();}});
canvas.addEventListener('wheel',ev=>{ev.preventDefault();const r=canvas.getBoundingClientRect(),delta=ev.deltaMode===1?ev.deltaY*16:ev.deltaY;zoom(Math.exp(-Math.max(-250,Math.min(250,delta))*.0017),ev.clientX-r.left,ev.clientY-r.top);tooltip(null,null,ev);},{passive:false});
function nodeBadge(n){return n.r.collection?`<span class="pill" style="color:${sourceColors[n.r.collection]}">${{W:'W · Polimi catalogue',O:'O · Osmani',P:'P · Pragmatic Engineer'}[n.r.collection]}</span>`:`<span class="pill">${esc(n.r.kind.replaceAll('_',' '))}</span>`;}
function chapterChips(ids){return ids.length?ids.map(id=>`<span class="pill" title="${esc(names.get(id)||id)}">CH ${id.replace('C:C','')} · ${esc(names.get(id)||id)}</span>`).join(''):'<span class="micro">None recorded.</span>';}
function openInspector(label){$('inspectorLabel').textContent=label;$('inspector').classList.add('open');tooltip(null,null,lastPointer);}
function selectNode(n,center=false){selected=n.i;selectedEdge=null;selectedConnLimit=40;openInspector(n.r.collection?'Source details':'Context record');renderNodeDetails(n,true);if(center)centerNode(n);requestDraw();}
function selectEdge(e){selected=null;selectedEdge=e.i;openInspector('Relationship details');renderEdgeDetails(e,true);requestDraw();}
function clearSelection(){selected=null;selectedEdge=null;$('inspector').classList.remove('open');requestDraw();}
function renderNodeDetails(n,resetScroll=true){
 const r=n.r,a=r.attributes,url=safeURL(r.url),inView=visibleSet.has(n.i),isSource=!!r.collection;
 const access=a.access_status||'',partial=access&&(access.toLowerCase().includes('preview')||access.toLowerCase().includes('minimal')||access.toLowerCase().includes('excerpt'));
 const conns=adjacent[n.i],visibleConns=conns.filter(e=>visibleSet.has(e.source)&&visibleSet.has(e.target)&&S.relations.has(e.relation));
 const sorted=[...conns].sort((a,b)=>Number(!(visibleSet.has(a.source)&&visibleSet.has(a.target)&&S.relations.has(a.relation)))-Number(!(visibleSet.has(b.source)&&visibleSet.has(b.target)&&S.relations.has(b.relation)))||a.relation.localeCompare(b.relation));
 const list=sorted.slice(0,selectedConnLimit).map(e=>{const other=e.source===n.i?e.t:e.s,on=visibleSet.has(e.source)&&visibleSet.has(e.target)&&S.relations.has(e.relation);return `<div class="conn"><button data-inspect-node="${other.i}">${e.source===n.i?'→':'←'} ${esc(other.id)} · ${esc(other.r.label)}</button><small class="${on?'':'off'}"><button data-inspect-edge="${e.i}" style="font-size:9px;font-weight:400;color:inherit">${esc(e.relation)}</button>${on?'':' · hidden by view filters'}</small></div>`;}).join('');
 $('inspectorBody').innerHTML=`<div class="record-id" style="color:${r.collection?sourceColors[r.collection]:'#61788e'}">${esc(n.id)}</div><h2 class="record-title">${esc(r.label)}</h2><div class="record-meta">${esc(r.authors)}${r.year?'<br>'+esc(r.year):''}</div><div class="pills">${nodeBadge(n)}${r.printed?'<span class="pill">Printed bibliography</span>':''}${partial?'<span class="pill warn">Restricted / preview-based</span>':''}${n.pinned?'<span class="pill">Pinned</span>':''}</div>${!inView?'<p class="caution">This record is outside the current view. Reveal it to enable its collection and relax the filters.</p>':''}<div class="button-row"><button class="small" data-detail-action="reveal">${inView?'Center on node':'Reveal in graph'}</button><button class="small" data-detail-action="pin">${n.pinned?'Unpin':'Pin'}</button><button class="small" data-detail-action="focus" ${inView?'':'disabled'}>1-hop view</button><button class="small" data-detail-action="focus2" ${inView?'':'disabled'}>2-hop</button></div>${url?`<a class="external-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open recorded source ↗</a>`:''}${r.summary?`<div class="record-section"><h4>${isSource?'In brief':'Description'}</h4><p>${esc(r.summary)}</p></div>`:''}${a.summary&&a.summary!==r.summary?`<details><summary>Full annotated summary</summary><p class="note">${esc(a.summary)}</p></details>`:''}${a.main_findings?`<details><summary>Main findings / arguments</summary><p class="note">${esc(a.main_findings)}</p></details>`:''}${r.limitation?`<div class="record-section"><h4>Evidence boundary</h4><div class="caution">${esc(r.limitation)}</div></div>`:''}${access?`<p class="micro">Access classification: ${esc(access)}${a.access_note?'<br>'+esc(a.access_note):''}</p>`:''}<div class="record-section"><h4>Polimi stream membership</h4><div class="pills">${r.streams.length?r.streams.map(id=>`<span class="pill">${esc(names.get(id)||id)}</span>`).join(''):'<span class="micro">No stream assigned.</span>'}</div></div><div class="record-section"><h4>${isSource?'Actual chapter citations · v6':'Structural chapter membership'}</h4><div class="pills">${chapterChips(r.actual)}</div><p class="micro">${isSource?'Derived only from current chapter-bundle citation links; not all printed references have a chapter citation.':'Chapter and section identity used for display grouping, not a claim of source citation.'}</p><h4 style="margin-top:15px">Editorial chapter mappings</h4><div class="pills">${chapterChips(r.mapped)}</div><p class="micro">Includes broader editorial proposals and actual use. These are not interchangeable.</p></div><div class="record-section connections"><h4>Connections · ${visibleConns.length} visible / ${conns.length} total</h4>${list}${conns.length>selectedConnLimit?'<button class="small" data-detail-action="more">Show more connections</button>':''}</div><details><summary>All original graph attributes</summary><pre class="raw">${esc(JSON.stringify(a,null,2))}</pre></details>`;
 if(resetScroll)$('inspectorBody').scrollTop=0;
}
function renderEdgeDetails(e,resetScroll=true){
 const on=visibleSet.has(e.source)&&visibleSet.has(e.target)&&S.relations.has(e.relation),a=e.attributes;
 $('inspectorBody').innerHTML=`<div class="record-id" style="color:${familyColors[e.family]}">${esc(familyNames[e.family])}</div><h2 class="record-title" style="font-family:inherit;font-size:17px;overflow-wrap:anywhere">${esc(e.relation)}</h2><div class="pills"><span class="pill">Original directed edge</span><span class="pill">Key ${esc(e.key)}</span><span class="pill ${on?'':'warn'}">${on?'Visible':'Hidden by filters'}</span></div><div class="record-section"><h4>From</h4><button class="flat" data-inspect-node="${e.source}" style="text-align:left;padding:0;color:var(--accent)">${esc(e.s.id)} · ${esc(e.s.r.label)}</button><h4 style="margin-top:19px">To</h4><button class="flat" data-inspect-node="${e.target}" style="text-align:left;padding:0;color:var(--accent)">${esc(e.t.id)} · ${esc(e.t.r.label)}</button></div>${a.rationale?`<div class="record-section"><h4>Recorded rationale</h4><p>${esc(a.rationale)}</p></div>`:''}${a.provenance?`<div class="record-section"><h4>Provenance</h4><p>${esc(a.provenance)}</p></div>`:''}${a.citation_identity_level?`<p class="caution">Citation identity: ${esc(a.citation_identity_level)}</p>`:''}${a.mapping_confidence?`<p class="micro">Mapping confidence: ${esc(a.mapping_confidence)}</p>`:''}<div class="record-section"><button class="small" data-hide-edge-type="${esc(e.relation)}">Hide this relationship type</button><p class="micro">This hides every ${esc(e.relation)} link, not just this edge. It does not alter the underlying graph.</p></div><details open><summary>All original edge attributes</summary><pre class="raw">${esc(JSON.stringify(a,null,2))}</pre></details>`;
 if(resetScroll)$('inspectorBody').scrollTop=0;
}
$('inspectorBody').addEventListener('click',ev=>{
 const b=ev.target.closest('button');if(!b)return;
 if(b.dataset.inspectNode){const n=nodes[Number(b.dataset.inspectNode)];selectNode(n,false);return;}
 if(b.dataset.inspectEdge){selectEdge(links[Number(b.dataset.inspectEdge)]);return;}
 if(b.dataset.hideEdgeType){S.relations.delete(b.dataset.hideEdgeType);rebuild({reseed:false});return;}
 const act=b.dataset.detailAction,n=selected!==null?nodes[selected]:null;if(!n||!act)return;
 if(act==='pin'){n.pinned=!n.pinned;renderNodeDetails(n,false);updateCaption();requestDraw();}
 if(act==='reveal'){if(visibleSet.has(n.i)){centerNode(n);}else revealNode(n);}
 if(act==='focus'||act==='focus2'){S.focus=n.id;S.focusDepth=act==='focus2'?2:1;rebuild();}
 if(act==='more'){selectedConnLimit+=60;const scroll=$('inspectorBody').scrollTop;renderNodeDetails(n,false);$('inspectorBody').scrollTop=scroll;}
});
function revealNode(n){
 if(n.r.collection)S.collections.add(n.r.collection);else S.context.add(n.r.category);
 S.query='';S.printedOnly=false;S.strictPulse=false;S.focus=null;S.hideIsolated=false;S.themeFilters=new Set(allThemeIDs);S.chapterFilters=new Set(allChapterIDs);rebuild();selectNode(n,true);toast('Collection enabled and restrictive filters cleared to reveal '+n.id+'.');
}
function renderResults(){
 resultNodes=[...visible].sort((a,b)=>a.id.localeCompare(b.id,undefined,{numeric:true}));const sources=resultNodes.filter(n=>n.r.collection).length;
 $('resultsHeading').innerHTML=`<strong>${number(resultNodes.length)} visible records</strong> · ${number(sources)} sources<br>Keyboard-accessible alternative to the canvas. Results follow the same filters.`;
 $('resultsList').innerHTML=resultNodes.slice(0,resultsLimit).map(n=>`<button class="result-item" data-result-node="${n.i}"><div class="ri-head"><strong style="color:${n.r.collection?sourceColors[n.r.collection]:nodeColors[n.r.category]}">${esc(n.id)}</strong><span class="count">${esc(n.r.collection||n.r.kind.replaceAll('_',' '))}</span></div><div class="ri-title">${esc(n.r.label)}</div><small>${esc(n.r.authors||n.r.summary.slice(0,120))}</small></button>`).join('');$('moreResults').hidden=resultNodes.length<=resultsLimit;
}
$('resultsList').addEventListener('click',ev=>{const b=ev.target.closest('[data-result-node]');if(b){selectNode(nodes[Number(b.dataset.resultNode)],true);if(window.innerWidth<=800)setMobile(false);}});
$('moreResults').onclick=()=>{resultsLimit+=100;renderResults();};
function reset(){stopLayout();S=defaultState();nodes.forEach(n=>{n.pinned=false;});clearSelection();$('relationSearch').value='';filterRelationList();switchTab('scope');rebuild();toast('Original Polimi view restored: W001–W193.');}
function filterRelationList(){const q=$('relationSearch').value.trim().toLowerCase();document.querySelectorAll('[data-rel-row]').forEach(row=>{row.hidden=q&&!row.dataset.relRow.toLowerCase().replaceAll('_',' ').includes(q.replaceAll('_',' '));});document.querySelectorAll('[data-family]').forEach(f=>{const any=[...f.querySelectorAll('[data-rel-row]')].some(r=>!r.hidden);f.hidden=!any;if(q&&any)f.open=true;});}
let searchTimer;
$('search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{S.query=$('search').value.trim();S.focus=null;rebuild();if(S.query)switchTab('sources');},180);});
$('relationSearch').addEventListener('input',filterRelationList);
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
document.querySelectorAll('[data-grouping]').forEach(b=>b.onclick=()=>{S.grouping=b.dataset.grouping;S.focus=null;rebuild();});
document.querySelectorAll('[data-collection]').forEach(b=>b.onchange=()=>{b.checked?S.collections.add(b.dataset.collection):S.collections.delete(b.dataset.collection);rebuild();});
$('chapterBasis').onchange=()=>{S.chapterBasis=$('chapterBasis').value;S.chapterFilters=new Set(allChapterIDs);S.focus=null;rebuild();};
for(const [id,key] of [['printedOnly','printedOnly'],['strictPulse','strictPulse'],['hideIsolated','hideIsolated']])$(id).onchange=()=>{S[key]=$(id).checked;rebuild();};
for(const [id,key] of [['showHulls','hulls'],['arrows','arrows'],['pinDragged','pinDragged']])$(id).onchange=()=>{S[key]=$(id).checked;requestDraw();};
$('labels').onchange=()=>{S.labels=$('labels').value;rebuild();};$('edgeOpacity').oninput=()=>{S.opacity=Number($('edgeOpacity').value);requestDraw();};
$('allSources').onclick=()=>{S.collections=new Set(['W','O','P']);rebuild();};$('noSources').onclick=()=>{S.collections.clear();rebuild();};
$('allGroups').onclick=()=>{if(S.grouping==='theme')S.themeFilters=new Set(allThemeIDs);else S.chapterFilters=new Set(allChapterIDs);rebuild();};$('noGroups').onclick=()=>{activeGroups().clear();rebuild();};
$('allContext').onclick=()=>{S.context=new Set(D.nodeGroups.map(g=>g.id));rebuild();};$('noContext').onclick=()=>{S.context.clear();rebuild();};
$('groupHubs').onclick=()=>{if(S.grouping==='theme')S.context.add('themes');else if(S.grouping==='chapter')S.context.add('chapters');else{S.context.add('themes');S.context.add('chapters');}rebuild();};
$('fullGraph').onclick=()=>{S.collections=new Set(['W','O','P']);S.context=new Set(D.nodeGroups.map(g=>g.id));S.themeFilters=new Set(allThemeIDs);S.chapterFilters=new Set(allChapterIDs);S.relations=new Set(allRelIDs);S.printedOnly=false;S.strictPulse=false;S.hideIsolated=false;S.query='';S.focus=null;rebuild();toast('All 881 nodes and 5,860 original relationships are enabled.');};
$('releasePins').onclick=()=>{nodes.forEach(n=>n.pinned=false);updateCaption();if(selected!==null)renderNodeDetails(nodes[selected],false);requestDraw();toast('All pins released. Auto-layout can reposition every visible node.');};
$('readableEdges').onclick=()=>{S.relations=new Set(allRelIDs.filter(r=>r!=='inferred_topic_similarity'));rebuild({reseed:false});};$('allEdges').onclick=()=>{S.relations=new Set(allRelIDs);rebuild({reseed:false});};$('noEdges').onclick=()=>{S.relations.clear();rebuild({reseed:false});};
$('resetBtn').onclick=reset;$('emptyReset').onclick=reset;$('clearFocus').onclick=()=>{S.focus=null;rebuild();};$('closeInspector').onclick=clearSelection;
$('layoutBtn').onclick=()=>{if(isLayingOut){stopLayout();toast('Layout stopped. Current positions retained.');}else startLayout(true,true);};
$('zoomIn').onclick=()=>zoom(1.25);$('zoomOut').onclick=()=>zoom(.8);$('fitBtn').onclick=()=>fitGraph();$('fitTop').onclick=()=>fitGraph();
$('mobileMenu').onclick=()=>setMobile(!$('sidebar').classList.contains('open'));$('sidebarMask').onclick=()=>setMobile(false);
function showModal(title,html){savedModalFocus=document.activeElement;$('modalTitle').textContent=title;$('modalBody').innerHTML=html;$('modalBackdrop').hidden=false;$('closeModal').focus();}
function closeModal(){ $('modalBackdrop').hidden=true;savedModalFocus?.focus();}
$('closeModal').onclick=closeModal;$('modalBackdrop').onclick=ev=>{if(ev.target===$('modalBackdrop'))closeModal();};
$('helpBtn').onclick=()=>showModal('Reading the atlas',`
<p>This single file embeds the <strong>audited v6 graph: 881 nodes, 5,860 directed relationships and 218 distinct edge types</strong>. There are no network libraries, analytics, accounts or server requirements. Opening a source link is the only intentional navigation to an external website.</p>
<h3>Start with a collection, then narrow the question</h3><p>The initial view contains the original <strong>193 Polimi W-series documents</strong>. Add O-series Osmani articles or P-series Pragmatic Engineer articles independently. The latter includes credited guest authors and interview participants. The Results tab is a keyboard-accessible alternative to selecting nodes on the canvas.</p>
<h3>Grouping is a view, not new evidence</h3><p>Polimi filters use both primary and secondary stream memberships. Chapter grouping offers <strong>editorial mappings</strong> and, separately, <strong>actual v6 chapter-bundle citations</strong>. When a record belongs to several selected groups, it is positioned in the first eligible group and counted only once. Records with no matching classification remain in an explicitly named unassigned group. Group labels are display regions, not synthetic graph nodes.</p>
<h3>Every edge remains inspectable</h3><p>The Relationships tab provides a switch for each original relationship type. Family switches are navigation conveniences, not evidence categories added to the graph. Both endpoints must be visible to render an edge. Add context nodes to see chapter, theme, claim, dataset and audit links. Hiding a membership edge does not erase a node’s classification. The default readable preset hides only inferred-topic-similarity links.</p>
<h3>Move and arrange</h3><p>Drag a node to position it; dragged nodes are pinned by default. Double-click a node to toggle its pin. Drag blank space to pan and use the wheel or a two-finger pinch to zoom. Auto-layout partitions the visible groups, applies link relaxation and resolves rectangular node collisions. It preserves pins and does not guarantee crossing-free edges, non-overlapping manual pins, or readable full titles at every zoom level.</p>
<div class="shortcut"><span>Find a source</span><kbd>/</kbd></div><div class="shortcut"><span>Fit the visible graph</span><kbd>F</kbd></div><div class="shortcut"><span>Run auto-layout</span><kbd>L</kbd></div><div class="shortcut"><span>Pin / unpin the selected node</span><kbd>P</kbd></div><div class="shortcut"><span>Close details or dialog</span><kbd>Esc</kbd></div>
<h3>Save your arrangement</h3><p>Export a view file to preserve positions, pins and filters. Importing that file restores the arrangement only for this exact graph fingerprint. The atlas deliberately opens in the original 193-document view each time; it does not automatically persist browser state. Graphical density is not a measure of evidential strength.</p>
<h3>Source and audit boundary</h3><p>W, O and P identify provenance, not evidence-quality rankings. Original source caveats and all node/edge attributes remain accessible. The P corpus retains its 71 restricted substantive records. Research replication and the real production pilot remain open; this explorer changes no source claims or validation status.</p><p class="micro">Graph: ${esc(D.meta.graphFile)}<br>SHA-256:</p><div class="hash">${D.meta.graphSha256}</div><details><summary>Original graph-level metadata</summary><pre class="raw">${esc(JSON.stringify(D.meta.graphAttributes,null,2))}</pre></details>`);
function download(name,text,type='application/json'){const blob=new Blob([text],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);}
function viewState(){const state={...S};for(const k of ['collections','context','themeFilters','chapterFilters','relations'])state[k]=[...S[k]];return {format:'AI_SWE_ATLAS_VIEW',version:1,graphSha256:D.meta.graphSha256,edition:D.meta.edition,createdAt:new Date().toISOString(),state,camera:{...camera},positions:nodes.filter(n=>Number.isFinite(n.x)&&Number.isFinite(n.y)).map(n=>({id:n.id,x:n.x,y:n.y,pinned:n.pinned})),selected:selected!==null?nodes[selected].id:null};}
function filteredExport(){return {meta:{...D.meta,exportScope:'VISIBLE_FILTERED_SUBGRAPH',view:viewState().state,visibleNodes:visible.length,visibleEdges:visibleLinks.length},nodes:visible.map(n=>({id:n.id,...n.r.attributes})),edges:visibleLinks.map(e=>({id:e.id,source:e.s.id,target:e.t.id,key:e.key,...e.attributes}))};}
function fullExport(){return {meta:D.meta,nodes:nodes.map(n=>({id:n.id,...n.r.attributes})),edges:links.map(e=>({id:e.id,source:e.s.id,target:e.t.id,key:e.key,...e.attributes}))};}
function svgExport(){
 if(!visible.length){toast('No visible nodes to export.');return;}
 let out=[`<svg xmlns="http://www.w3.org/2000/svg" width="${Math.round(cw)}" height="${Math.round(ch)}" viewBox="0 0 ${Math.round(cw)} ${Math.round(ch)}"><title>AI &amp; Software Engineering — audited v6 filtered graph</title><desc>Original directed graph links only. W, O and P indicate provenance, not evidence quality. ${visible.length} visible nodes; ${visibleLinks.length} visible edges.</desc><rect width="100%" height="100%" fill="#f8fafb"/><g transform="translate(${camera.x} ${camera.y}) scale(${camera.k})" font-family="Arial,sans-serif">`];
 if(S.hulls&&S.grouping!=='none')for(const g of groups){out.push(`<rect x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="11" fill="${g.color}" fill-opacity=".04" stroke="${g.color}" stroke-opacity=".2"/><text x="${g.x+12}" y="${g.y+25}" font-size="12" fill="${g.color}">${esc(g.label.length>Math.floor(g.w/7)?g.label.slice(0,Math.floor(g.w/7)-1)+'…':g.label)} (${g.nodes.length})</text>`);}
 for(const e of visibleLinks){const p=edgeGeometry(e);out.push(`<path d="M${p.sx},${p.sy} Q${p.cx},${p.cy} ${p.tx},${p.ty}" fill="none" stroke="${familyColors[e.family]}" stroke-width="${1/camera.k}" opacity="${S.opacity/100}" ${isDashed(e)?'stroke-dasharray="4 4"':''}><title>${esc(e.s.id+' → '+e.t.id+' · '+e.relation)}</title></path>`);if(S.arrows){const a=Math.atan2(p.ty-p.cy,p.tx-p.cx),l=5/camera.k;out.push(`<path d="M${p.tx},${p.ty} L${p.tx-l*Math.cos(a-.42)},${p.ty-l*Math.sin(a-.42)} L${p.tx-l*Math.cos(a+.42)},${p.ty-l*Math.sin(a+.42)} Z" fill="${familyColors[e.family]}" opacity="${S.opacity/100}"/>`);}}
 for(const n of visible){const label=n.r.collection?n.id:n.r.kind==='chapter'?n.id.replace('C:C','CH '):n.r.kind==='section'?n.id.replace('S:','§ '):n.r.kind.replaceAll('_',' ').slice(0,16);out.push(`<g><title>${esc(n.id+' · '+n.r.label)}</title><rect x="${n.x-n.w/2}" y="${n.y-n.h/2}" width="${n.w}" height="${n.h}" rx="${n.r.collection?5:2.5}" fill="white" stroke="${colorOf(n)}"/>${S.labels!=='none'?`<text x="${n.x}" y="${n.y+(S.labels==='title'?-5:4)}" text-anchor="middle" font-size="11" fill="#263d51">${esc(label)}</text>`:''}${S.labels==='title'?`<text x="${n.x}" y="${n.y+13}" text-anchor="middle" font-size="9" fill="#617181">${esc(n.r.label.slice(0,25)+(n.r.label.length>25?'…':''))}</text>`:''}${n.pinned?`<circle cx="${n.x+n.w/2-2}" cy="${n.y-n.h/2+2}" r="3" fill="${colorOf(n)}"/>`:''}</g>`);}
 out.push('</g></svg>');download('AI_SWE_Atlas_v6_visible_graph.svg',out.join(''),'image/svg+xml');
}
$('exportBtn').onclick=()=>showModal('Export & restore',`
<p>Your graph remains in this browser. Exporting creates a local file; nothing is uploaded.</p>
<div class="choice"><div><strong>Save this arrangement</strong><p>Filters, camera, positions and pins. Restore in this exact v6 atlas.</p></div><button class="small primary" data-export="view">Save view</button></div>
<div class="choice"><div><strong>Restore a saved view</strong><p>Load an exported view JSON. Graph fingerprints must match.</p></div><button class="small" data-export="load">Load view</button></div>
<div class="choice"><div><strong>Visible subgraph · JSON</strong><p>${visible.length} nodes, ${visibleLinks.length} edges, all original attributes.</p></div><button class="small" data-export="filtered">Export</button></div>
<div class="choice"><div><strong>Complete graph · JSON</strong><p>All 881 nodes and 5,860 edges, including hidden records.</p></div><button class="small" data-export="full">Export</button></div>
<div class="choice"><div><strong>Current canvas · SVG</strong><p>Scalable vector snapshot with edge directions and stable IDs.</p></div><button class="small" data-export="svg">Export</button></div>
<p class="micro">Saved views contain no article-body downloads. JSON exports preserve graph attributes; source links may require internet or subscription access.</p>`);
$('modalBody').addEventListener('click',ev=>{const act=ev.target.closest('[data-export]')?.dataset.export;if(!act)return;if(act==='view')download('AI_SWE_Atlas_v6_saved_view.json',JSON.stringify(viewState(),null,2));if(act==='filtered')download('AI_SWE_Atlas_v6_visible_graph.json',JSON.stringify(filteredExport(),null,2));if(act==='full')download('AI_SWE_Atlas_v6_complete_graph.json',JSON.stringify(fullExport(),null,2));if(act==='svg')svgExport();if(act==='load'){$('loadFile').value='';$('loadFile').click();}});
function restoreView(data){
 if(!data||data.format!=='AI_SWE_ATLAS_VIEW'||data.version!==1)throw new Error('This is not a supported atlas view file.');
 if(data.graphSha256!==D.meta.graphSha256)throw new Error('Graph fingerprint mismatch. This view belongs to a different graph edition.');
 const raw=data.state;if(!raw||!Array.isArray(data.positions))throw new Error('The view file is incomplete.');
 const next=defaultState(),allowedSets={collections:['W','O','P'],context:D.nodeGroups.map(g=>g.id),themeFilters:allThemeIDs,chapterFilters:allChapterIDs,relations:allRelIDs};
 for(const [k,allowed] of Object.entries(allowedSets)){if(!Array.isArray(raw[k])||raw[k].some(x=>typeof x!=='string'||!allowed.includes(x)))throw new Error('Invalid '+k+' filters.');next[k]=new Set(raw[k]);}
 if(!['theme','chapter','collection','none'].includes(raw.grouping)||!['mapped','actual'].includes(raw.chapterBasis)||!['id','title','none'].includes(raw.labels))throw new Error('Unknown grouping or display mode.');
 for(const k of ['grouping','chapterBasis','labels'])next[k]=raw[k];
 for(const k of ['printedOnly','strictPulse','hideIsolated','hulls','arrows','pinDragged']){if(typeof raw[k]!=='boolean')throw new Error('Invalid '+k+' setting.');next[k]=raw[k];}
 if(typeof raw.query!=='string'||raw.query.length>2000)throw new Error('Invalid search field.');next.query=raw.query;
 next.opacity=Math.max(10,Math.min(100,Number(raw.opacity)||30));next.focus=raw.focus&&byID.has(raw.focus)?raw.focus:null;next.focusDepth=raw.focusDepth===2?2:1;
 const seen=new Set();for(const p of data.positions){if(!p||!byID.has(p.id)||seen.has(p.id)||!Number.isFinite(p.x)||!Number.isFinite(p.y)||Math.abs(p.x)>1e7||Math.abs(p.y)>1e7||typeof p.pinned!=='boolean')throw new Error('Invalid or duplicate node position.');seen.add(p.id);}
 const cam=data.camera;if(!cam||![cam.x,cam.y,cam.k].every(Number.isFinite)||cam.k<.07||cam.k>6||Math.abs(cam.x)>1e8||Math.abs(cam.y)>1e8)throw new Error('Invalid camera coordinates.');
 stopLayout();S=next;nodes.forEach(n=>{n.pinned=false;});clearSelection();rebuild({run:false,fit:false});
 for(const p of data.positions){const n=byID.get(p.id);n.x=p.x;n.y=p.y;n.pinned=p.pinned;}
 recomputeGroupBounds();camera={...cam};updateCaption();syncControls();if(data.selected&&byID.has(data.selected))selectNode(byID.get(data.selected));requestDraw();closeModal();toast('Saved positions, pins and filters restored.');
}
$('loadFile').onchange=async()=>{const file=$('loadFile').files[0];if(!file)return;try{if(file.size>12e6)throw new Error('View file exceeds the 12 MB safety limit.');restoreView(JSON.parse(await file.text()));}catch(err){toast('Could not load view: '+err.message);}};
document.addEventListener('keydown',ev=>{
 if(!$('modalBackdrop').hidden){if(ev.key==='Escape'){ev.preventDefault();closeModal();}if(ev.key==='Tab'){const items=[...$('modalBackdrop').querySelectorAll('button,a[href],input,select,summary')].filter(x=>!x.disabled),first=items[0],last=items.at(-1);if(ev.shiftKey&&document.activeElement===first){ev.preventDefault();last.focus();}else if(!ev.shiftKey&&document.activeElement===last){ev.preventDefault();first.focus();}}return;}
 if(ev.key==='Escape'){clearSelection();setMobile(false);tooltip(null,null,lastPointer);return;}
 if(ev.target.matches('input,select,textarea')||ev.ctrlKey||ev.metaKey||ev.altKey)return;
 if(ev.key==='/'){ev.preventDefault();$('search').focus();}
 if(ev.key.toLowerCase()==='f'){ev.preventDefault();fitGraph();}
 if(ev.key.toLowerCase()==='l'){ev.preventDefault();startLayout(true,true);}
 if(ev.key.toLowerCase()==='p'&&selected!==null){const n=nodes[selected];n.pinned=!n.pinned;updateCaption();renderNodeDetails(n,false);requestDraw();}
 if(ev.key==='+')zoom(1.2);if(ev.key==='-')zoom(1/1.2);
 if(document.activeElement===canvas&&['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(ev.key)){ev.preventDefault();if(ev.key==='ArrowLeft')camera.x+=40;if(ev.key==='ArrowRight')camera.x-=40;if(ev.key==='ArrowUp')camera.y+=40;if(ev.key==='ArrowDown')camera.y-=40;requestDraw();}
});
new ResizeObserver(()=>{const oldW=cw,oldH=ch;boardSize();if(oldW>1&&(Math.abs(cw-oldW)>50||Math.abs(ch-oldH)>60))fitGraph(false);}).observe($('board'));
buildControls();boardSize();rebuild();
// Read-only diagnostics for reproducible QA; no external calls or persistence.
window.atlasDiagnostics=()=>({version:D.meta.edition,sha256:D.meta.graphSha256,totalNodes:nodes.length,totalEdges:links.length,totalRelations:D.relations.length,visibleNodeIDs:visible.map(n=>n.id),visibleEdgeIDs:visibleLinks.map(e=>e.id),visibleSources:visible.filter(n=>n.r.collection).length,visibleContext:visible.filter(n=>!n.r.collection).length,grouping:S.grouping,chapterBasis:S.chapterBasis,groups:groups.map(g=>({id:g.id,count:g.nodes.length,x:g.x,y:g.y,w:g.w,h:g.h})),layoutRunning:isLayingOut,selected:selected!==null?nodes[selected].id:null,selectedEdge:selectedEdge!==null?links[selectedEdge].id:null,pinned:nodes.filter(n=>n.pinned).map(n=>n.id),camera:{...camera},positions:visible.map(n=>({id:n.id,x:n.x,y:n.y,w:n.w,h:n.h,pinned:n.pinned})),canvas:{width:cw,height:ch},nodeAttributeCount:D.nodes.reduce((s,n)=>s+Object.keys(n.attributes).length,0),edgeAttributeCount:D.edges.reduce((s,e)=>s+Object.keys(e.attributes).length,0),sourceCounts:Object.fromEntries(['W','O','P'].map(c=>[c,visible.filter(n=>n.r.collection===c).length]))});
})();
