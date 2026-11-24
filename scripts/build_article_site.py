#!/usr/bin/env python3
"""Build a static GitHub Pages site from the article repository. Requires pandoc."""
import argparse, datetime as dt, html, json, os, pathlib as P, re, shutil, subprocess, tempfile, urllib.parse as U, xml.etree.ElementTree as ET
from html.parser import HTMLParser
ROOT=P.Path(__file__).resolve().parent.parent
BASE='https://popoloni.github.io/articles/'
REPO='https://github.com/popoloni/articles/'
CATS=[
('2026-05-16','evolution-of-spec-driven-development','Spec-driven development','20260516_TheEvolutionofSpec-DrivenDevelopment/medium.md','Architectures, methodologies and frameworks for specification-first AI-assisted engineering.'),
('2026-05-25','economics-of-generative-ai','AI economics','20260525_TheEconomicsofGenerativeAIFromSubsidyCrisistoAgenticWorkflowSustainability/medium.md','Why inference pricing and growing context change AI economics.'),
('2026-07-24','economics-of-ai-loops','AI economics','20260724_TheEconomicsofAILoops/article.md','From cheap tokens to independently verified outcomes.'),
('2026-07-30','local-llm-inference-on-apple-silicon','Local AI','270730_local_llm_mac_guide/local_llm_mac_guide_medium.md','Mac-native inference architectures, memory, serving and optimisation.'),
('2026-08-27','ai-summer-assignment','AI beyond coding','260827_AI_summer_assignement/article/Medium_Article_AI_Summer_Assignment_Enrico_Papalini.md','Disciplined AI workflows for writing and publishing a historical fantasy saga.'),
('2026-09-11','artifactory-and-agent-coordination','Agentic engineering','260911_artifactory-blackboard-medium/article.md','An accidental blackboard and the boundary between information and authority.'),
('2026-09-29','bigger-models-smaller-macs','Local AI','260929_bigger_models_smaller_macs_handwritten/article.md','Useful local coding systems, quantisation and reusable context.'),
('2026-09-30','jev-and-the-return-of-the-classifier','Local AI','260930_jev_complete_illustrated/essay.md','Reusable decision models and classifiers for agentic workflows.'),
('2026-10-11','local-llm-on-a-16gb-mac-mini','Local AI','20261011_M4_16GB_Model_Selection/article.md','Ten tested configurations for a 16 GB Mac mini.'),
('2026-10-16','coding-agents-infrastructure-or-lock-in','Spec-driven development','261016_Enterprise_SDD_Harness/ARTICLE_Medium_with_Figures_v3.md','OpenCode, Copilot and Claude Code: enterprise harnesses and engineering authority.'),
('2026-10-17','ai-wrote-the-patch','Books & research','261017_NDSE2_Launch_article/ARTICLE_MEDIUM_EN.md','The second edition and the evidence behind trustworthy change.'),
('2026-10-18','knowledge-atlas','Books & research','261018_Knowledge_Atlas_13_1/Medium_Article_Atlas_13_1.md','An illustrated tour of research, practices and the Knowledge Atlas.'),
('2026-10-28','testing-the-sdd-framework','Spec-driven development','261028_SDD_Testing_Complete_Companion/article.md','Testing the system that governs agent-produced software.'),
('2026-11-23','the-agent-wrote-the-fix','Books & research','261123_non-deterministic-trilogy/article.md','The evolution of the engineer’s role and the new Non-Deterministic trilogy.'),
('2026-11-24','reliable-software-with-ai-coding-agents','Agentic engineering','261124_ESA_Chapter_1_Medium_Article/How_to_Build_Reliable_Software_with_AI_Coding_Agents.md','Expect, Delegate, Observe, Decide: a practical walkthrough of accountable change.')]

def e(x): return html.escape(str(x),quote=True)
def run(*args): return subprocess.check_output(args,cwd=ROOT).decode()
def walk(x,fn):
 if isinstance(x,dict):
  fn(x)
  for v in x.values(): walk(v,fn)
 elif isinstance(x,list):
  for v in x: walk(v,fn)
def page(title,description,content,prefix='',canonical='',math=False):
 return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{e(description)}"><title>{e(title)} · Enrico Papalini</title><link rel="canonical" href="{e(BASE+canonical)}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><link rel="stylesheet" href="{prefix}assets/articles.css"><link rel="alternate" type="application/rss+xml" href="{prefix}feed.xml"><script defer src="{prefix}assets/articles.js"></script>{'<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>' if math else ''}</head><body><a class="skip" href="#main">Skip to content</a><header><nav><a class="brand" href="{prefix or './'}"><b>EP<span>.</span></b><span>Enrico Papalini<small>Writing on software &amp; AI</small></span></a><div><a href="{prefix or './'}">Articles</a><a href="https://popoloni.github.io/">Knowledge Atlas</a><a href="https://popoloni.github.io/catalogues/volumes.html">Books</a><a href="https://github.com/popoloni/articles">GitHub</a><a href="https://medium.com/@enrico.papalini">Medium</a></div></nav></header><main id="main">{content}</main><footer>Independent writing by Enrico Papalini · <a href="{prefix}feed.xml">RSS</a> · <a href="https://popoloni.github.io/about.html">About</a></footer></body></html>'''

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preview-fixtures',action='store_true',help=argparse.SUPPRESS);args=ap.parse_args()
 if not shutil.which('pandoc'): raise SystemExit('Install pandoc first (macOS: brew install pandoc).')
 if not args.preview_fixtures and not (ROOT/'Medium').is_dir(): raise SystemExit(f'ERROR: {ROOT}/Medium is missing. Extract the package into the articles Git checkout, or use setup_article_site.command.')
 print(f'Building articles from {ROOT}', flush=True)
 catalog=ROOT/'scripts/article_catalog.json'
 if not catalog.exists(): catalog.write_text(json.dumps([dict(date=d,slug=s,topic=t,source='Medium/'+p,description=z) for d,s,t,p,z in CATS],indent=2,ensure_ascii=False)+'\n')
 records=json.loads(catalog.read_text()); records.sort(key=lambda a:a['date'],reverse=True)
 if len({a['slug'] for a in records})!=len(records): raise ValueError('Duplicate slugs')
 ref=run('git','rev-parse','HEAD').strip() if not args.preview_fixtures else 'main'
 missing=[]; checked=set(); rendered={}; raw='https://raw.githubusercontent.com/popoloni/articles/'+ref+'/'
 for a in records:
  assert re.fullmatch('[a-z0-9-]+',a['slug']);dt.date.fromisoformat(a['date']);src=P.PurePosixPath(a['source']);assert src.parts[0]=='Medium'
  try:
   text=run('git','show',ref+':'+str(src)) if not args.preview_fixtures else (ROOT/src).read_text()
  except (subprocess.CalledProcessError,FileNotFoundError) as exc:
   raise SystemExit(f'ERROR: cannot read committed article {src} at {ref}. Check that your checkout is current. No new site was published.') from exc
  print(f'  {a["date"]}  {a["slug"]}', flush=True)
  # Parse with a real Markdown parser, retaining tables, equations, links and code.
  ast=json.loads(subprocess.check_output(['pandoc','-f','markdown+tex_math_dollars','-t','json'],input=text.encode()))
  def plain(inlines):
   return subprocess.check_output(['pandoc','-f','json','-t','plain'],input=json.dumps({'pandoc-api-version':ast['pandoc-api-version'],'meta':{},'blocks':[{'t':'Para','c':inlines}]}).encode()).decode().strip()
  first=next((i for i,b in enumerate(ast['blocks']) if b['t']=='Header' and b['c'][0]==1),None)
  if first is None: raise ValueError('No title: '+str(src))
  a['title']=plain(ast['blocks'].pop(first)['c'][2]);a['image']='';a['minutes']=max(1,round(len(text.split())/220));a['source_url']=REPO+'blob/'+ref+'/'+U.quote(str(src));a['folder_url']=REPO+'tree/'+ref+'/'+U.quote('/'.join(src.parts[:2]));a['url']='read/'+a['slug']+'/'
  math=[False]
  def rewrite(n):
   kind=n.get('t');c=n.get('c')
   if kind in ('RawBlock','RawInline') and c[0]=='html':
    # Allow only explicit empty anchors; other raw HTML is rendered as text.
    if not re.fullmatch(r'\s*<a id="[A-Za-z0-9_.:-]+">\s*</a>\s*',c[1]): n.update(t='Str' if kind=='RawInline' else 'Para',c=c[1] if kind=='RawInline' else [{'t':'Str','c':c[1]}])
   if kind=='Header' and c[0]==1:c[0]=2
   if kind=='Math':math[0]=True
   if kind not in ('Link','Image'):return
   target=c[-1];url=target[0];parts=U.urlsplit(url);path=None
   own=re.match(r'https://raw\.githubusercontent\.com/popoloni/articles/(?:main|[0-9a-f]{40})/(.*)',url)
   if own:path=U.unquote(U.urlsplit(own[1]).path)
   elif not parts.scheme and not parts.netloc and parts.path and not parts.path.startswith('/'):
    path=os.path.normpath(str(src.parent/U.unquote(parts.path)))
   if path is not None:
    if path.startswith('../') or path.startswith('/'):raise ValueError('Unsafe path '+path)
    checked.add(path);exists=(ROOT/path).exists() if args.preview_fixtures else subprocess.run(['git','cat-file','-e',ref+':'+path],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
    if not exists:missing.append((str(src),path))
    target[0]=(raw if kind=='Image' else REPO+('tree/' if (ROOT/path).is_dir() else 'blob/')+ref+'/')+U.quote(path)+('?' + parts.query if parts.query else '')+('#'+parts.fragment if parts.fragment else '')
   elif parts.scheme and parts.scheme not in ('https','http','mailto'): raise ValueError('Unsafe link '+url)
   if kind=='Image' and not a['image']:a['image']=target[0]
  walk(ast,rewrite)
  body=subprocess.check_output(['pandoc','-f','json','-t','html5','--mathjax'],input=json.dumps(ast).encode()).decode()
  rendered[a['slug']]=(body,math[0])
 if missing:raise ValueError('Unresolved paths: '+str(missing))
 with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
  out=P.Path(tmp);(out/'assets').mkdir();shutil.copyfile(ROOT/'scripts/articles.css',out/'assets/articles.css');shutil.copyfile(ROOT/'scripts/articles.js',out/'assets/articles.js');(out/'.nojekyll').touch()
  for a in records:
   related=''.join(f'<a href="../{e(b["slug"])}/">{e(b["title"])}</a>' for b in records if b['slug']!=a['slug'] and b['topic']==a['topic'])
   body,math=rendered[a['slug']];content=f'<div class="reader"><a href="../../">← All articles</a><div class="article-head"><p class="eyebrow">{e(a["topic"])}</p><h1>{e(a["title"])}</h1><p class="meta">Enrico Papalini · {e(a["date"])} · {a["minutes"]} min read</p><p class="lede">{e(a["description"])}</p><p class="sources"><a href="{e(a["source_url"])}">Original Markdown ↗</a> · <a href="{e(a["folder_url"])}">Article files &amp; companion ↗</a></p></div><div class="reading-layout"><aside id="toc" hidden><details open><summary>On this page</summary><nav id="toc-links"></nav></details></aside><article class="prose" id="article-body">{body}</article></div><section class="related"><h2>Keep reading</h2>{related}<a href="../../">Browse all articles →</a></section></div>'
   p=out/a['url'];p.mkdir(parents=True);(p/'index.html').write_text(page(a['title'],a['description'],content,'../../',a['url'],math))
  latest=records[0];topics=sorted({a['topic'] for a in records});options=''.join(f'<option>{e(t)}</option>' for t in topics);rows=''.join(f'<article class="row" data-topic="{e(a["topic"])}" data-search="{e(a["title"]+" "+a["description"]+" "+a["topic"])}"><time datetime="{a["date"]}">{dt.date.fromisoformat(a["date"]).strftime("%d %b %Y")}</time><div><p class="meta">{e(a["topic"])} · {a["minutes"]} min read</p><h3><a href="{a["url"]}">{e(a["title"])}</a></h3><p>{e(a["description"])}</p></div></article>' for a in records)
  featured_image = '<img src="'+e(latest["image"])+'" alt="Illustration from the latest article">' if latest["image"] else ""
  content=f'<div class="wrap"><section class="intro"><div><p class="eyebrow">The writing archive</p><h1>Engineering in the age of AI<span>.</span></h1><p class="lede">Essays, practical guides and research notes on building reliable software with artificial intelligence.</p></div><aside><img src="https://popoloni.github.io/assets/enrico-papalini.jpg" alt="Enrico Papalini"><b>Enrico Papalini</b><p>Software engineering leader and author of the Non-Deterministic series.</p></aside></section><section class="feature"><div><p class="eyebrow">Latest article · {latest["date"]}</p><h2><a href="{latest["url"]}">{e(latest["title"])}</a></h2><p>{e(latest["description"])}</p><a href="{latest["url"]}">Read the article →</a></div>{featured_image}</section><h2>All articles</h2><div id="filters" hidden><label>Search<input id="search" type="search" placeholder="Verification, local AI, specifications…"></label><label>Topic<select id="topic"><option value="">All topics</option>{options}</select></label><button id="clear">Clear</button></div><p id="count" aria-live="polite">{len(records)} articles · newest first</p>{rows}<p class="meta">Dates reflect archive collection dates, not independently verified Medium publication dates. The Apple Silicon guide uses its stated July 2026 evidence date. Reading times are estimates.</p><section class="more"><h2>Continue reading</h2><a href="https://popoloni.github.io/">Knowledge Atlas →</a><a href="https://popoloni.github.io/catalogues/volumes.html">Books →</a><a href="https://medium.com/@enrico.papalini">Medium →</a></section></div>'
  (out/'index.html').write_text(page('Articles','Essays and guides on AI-assisted software engineering.',content));(out/'404.html').write_text(page('Page not found','Article not found',f'<div class="wrap"><h1>Article not found</h1><a href="{BASE}">All articles →</a></div>',BASE))
  rss=ET.Element('rss',version='2.0');ch=ET.SubElement(rss,'channel');
  for k,v in [('title','Enrico Papalini — Articles'),('link',BASE),('description','Software engineering and AI')]:ET.SubElement(ch,k).text=v
  for a in records:
   item=ET.SubElement(ch,'item')
   for k,v in [('title',a['title']),('link',BASE+a['url']),('guid',BASE+a['url']),('description',a['description']),('category',a['topic'])]:ET.SubElement(item,k).text=v
  ET.ElementTree(rss).write(out/'feed.xml',encoding='utf-8',xml_declaration=True)
  sm=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9');
  for u in ['']+[a['url'] for a in records]:ET.SubElement(ET.SubElement(sm,'url'),'loc').text=BASE+u
  ET.ElementTree(sm).write(out/'sitemap.xml',encoding='utf-8',xml_declaration=True);(out/'articles.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
  dest=ROOT/'docs';
  if dest.exists() and not dest.is_dir():raise ValueError('docs exists but is not a directory')
  if dest.exists() and any(dest.iterdir()) and not (dest/'.article-site-generated').exists():raise ValueError('Existing non-empty docs directory not owned by generator; refusing replacement')
  expected=['index.html','feed.xml','sitemap.xml','assets/articles.css','assets/articles.js']+[a['url']+'index.html' for a in records]
  for filename in expected:
   if not (out/filename).is_file() or (out/filename).stat().st_size==0:raise ValueError('Missing generated file: '+filename)
  (out/'.article-site-generated').touch();
  if dest.exists():shutil.rmtree(dest)
  shutil.copytree(out,dest)
 print(f'Generated {len(records)} articles; checked {len(checked)} distinct relative repository targets. Source: {ref}')
 print(f'Homepage: {ROOT / "docs/index.html"}')
 print('Preview with: python3 scripts/preview_article_site.py')
if __name__=='__main__':main()
