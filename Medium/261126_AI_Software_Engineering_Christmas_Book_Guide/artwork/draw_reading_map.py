#!/usr/bin/env python3
"""Generate the editable vector reading map; typography uses bundled SketchHand."""
from pathlib import Path
from html import escape
import random

HERE=Path(__file__).resolve().parent
OUT=HERE/'reading-map.svg'
W,H=1300,850
r=random.Random(20261125)
INK='#243544'; BLUE='#397ba1'; ORANGE='#d77c39'; MUTED='#4c6575'
s=[]
s.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="2600" height="1700" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">A reading map for AI software engineering</title>
<desc id="desc">Start with your next engineering question. The current Non-Deterministic trilogy is: 1, Non-Deterministic Software Engineering, Second Edition, to understand which practices deserve trust; 2, Non-Deterministic Spec-Driven Development: Enterprise Edition, Second Edition, to specify what a change must do; 3, Engineering Software with Agentic AI: Reliable Change with Coding Agents, to practise directing and judging a change. The separately published Packt companion, Loop Engineering for AI Agents, helps build the runtime that controls an agent. Each book stands alone. Arrows identify possible starting points, not prerequisites.</desc>
<rect width="1300" height="850" fill="white"/>
''')

def line(d,w=2,color=INK,opacity=1,dash=None):
    s.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')

def text(x,y,t,size=28,color=INK,anchor='start',bold=False):
    s.append(f'<text x="{x}" y="{y}" font-family="SketchHand" font-size="{size}" text-anchor="{anchor}" fill="{color}" stroke="{color}" stroke-width="{.48 if bold else .13}" stroke-linejoin="round" paint-order="stroke">{escape(t)}</text>')

def swatch(x,y,w,h,color,opacity=.15):
    # Uneven translucent strokes create a crayon mark while keeping the paper white.
    s.append(f'<path d="M{x-2} {y+2} L{x+w+3} {y-1} L{x+w} {y+h+2} L{x+1} {y+h-1} Z" fill="{color}" opacity="{opacity*.62}"/>')
    for j in range(int(h*1.65)):
        yy=y+r.uniform(0,h)
        line(f'M{x+r.uniform(-3,9):.2f} {yy:.2f} Q{x+w*.45:.2f} {yy+r.uniform(-1.3,1.3):.2f} {x+w+r.uniform(-8,4):.2f} {yy+r.uniform(-1.2,1.2):.2f}',r.uniform(.45,1.1),color,opacity*r.uniform(.5,1))

def book(x,y,w,h):
    # A restrained hand-inked book outline, including the page edge.
    line(f'M{x} {y+3} Q{x+w*.4} {y-1} {x+w-4} {y+1} L{x+w+1} {y+h-8} Q{x+w*.52} {y+h-4} {x+1} {y+h-7} Z',2.1)
    line(f'M{x+8} {y+h-5} Q{x+w*.51} {y+h+2} {x+w+5} {y+h-2} L{x+w+6} {y+8}',1.15,INK,.75)
    line(f'M{x+14} {y+5} Q{x+12} {y+h*.5} {x+14} {y+h-10}',.9,INK,.42)
    line(f'M{x-2} {y+2} L{x+w*.18} {y-1} M{x+w*.79} {y+h-8} L{x+w+3} {y+h-6}',.6,INK,.8)

def arrow_tip(x,y,dx=0,dy=-1,color=BLUE):
    # Two pen strokes, no filled synthetic triangle.
    if dy==-1: line(f'M{x-5} {y+10} L{x} {y} L{x+5} {y+10}',2.1,color)
    elif dx==-1: line(f'M{x+10} {y-5} L{x} {y} L{x+10} {y+5}',2.1,color)

text(45,67,'A READING MAP FOR AI SOFTWARE ENGINEERING',43,bold=True)
text(47,106,'Choose the book that answers the question in front of you.',29,color=MUTED)
swatch(46,134,470,29,BLUE,.18)
text(55,157,'THE CURRENT NON-DETERMINISTIC TRILOGY',24,bold=True)
line('M50 177 L50 187 M50 181 Q645 177 1248 181 L1248 187',1.15,BLUE,.75)

# Three numbered current volumes, kept in the established series order.
xs=[48,470,892]; bw=360; by=202; bh=287
for x in xs: book(x,by,bw,bh)
swatch(74,220,281,37,BLUE,.22)
text(82,247,'1  UNDERSTAND',31,bold=True)
text(77,292,'Non-Deterministic',29,bold=True)
text(77,327,'Software Engineering',29,bold=True)
text(77,362,'Second Edition',25,color=MUTED)
line('M77 386 Q229 384 379 386',1,BLUE,.7)
text(77,419,'Which practices',28)
text(77,452,'deserve trust?',28)

swatch(496,220,281,37,ORANGE,.23)
text(504,247,'2  SPECIFY',31,bold=True)
text(499,288,'Non-Deterministic',28,bold=True)
text(499,321,'Spec-Driven Development:',24.2,bold=True)
text(499,354,'Enterprise Edition',28,bold=True)
text(499,385,'Second Edition',24,color=MUTED)
line('M499 402 Q651 400 802 402',1,ORANGE,.7)
text(499,435,'What must the',28)
text(499,465,'change do?',28)

swatch(918,220,281,37,BLUE,.22)
text(926,247,'3  PRACTISE',31,bold=True)
text(921,292,'Engineering Software',29,bold=True)
text(921,327,'with Agentic AI',29,bold=True)
text(921,361,'Reliable Change',24,color=MUTED)
text(921,390,'with Coding Agents',24,color=MUTED)
line('M921 408 Q1074 406 1225 408',1,BLUE,.7)
text(921,439,'How do I direct',28)
text(921,469,'and judge a change?',28)

# Deliberately branch from the question to all volumes: no prerequisite chain.
line('M909 593 Q847 540 634 540 Q292 539 229 499',2.6,BLUE,.88)
arrow_tip(229,499,color=BLUE)
line('M909 593 Q879 562 799 557 Q697 552 651 500',2.6,ORANGE,.88)
arrow_tip(651,500,color=ORANGE)
line('M909 593 Q1022 558 1072 500',2.6,BLUE,.88)
arrow_tip(1072,500,color=BLUE)
# Tiny junction circles carry the visual map language.
for x,y in [(909,593),(651,500),(229,499),(1072,500)]:
    s.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="white" stroke="{BLUE}" stroke-width="1.5"/>')

# A separately published complementary volume, not a fourth series number.
book(49,580,518,196)
swatch(76,598,451,31,ORANGE,.20)
text(83,621,'COMPANION  /  BUILD THE RUNTIME',26,bold=True)
text(77,660,'Loop Engineering for AI Agents',29.5,bold=True)
text(78,690,'Separate Packt volume',23,color=MUTED)
text(78,725,'How will the agent be controlled?',28)
text(78,754,'State · budgets · stopping rules',23,color=MUTED)

# Central question uses an informal circled note, not a mandatory entry step.
swatch(693,618,526,101,ORANGE,.10)
line('M671 662 C670 594 812 581 958 592 C1130 589 1243 616 1247 668 C1248 735 1081 758 903 749 C760 752 672 723 671 662 Z',2.2)
line('M695 620 C727 598 789 594 835 594 M1174 738 Q1220 727 1242 700',.75,INK,.6)
text(958,646,'YOUR NEXT',33,anchor='middle',bold=True)
text(958,684,'ENGINEERING QUESTION',33,anchor='middle',bold=True)
text(958,718,'Follow the next unresolved decision.',25,anchor='middle',color=MUTED)
line('M671 672 Q619 669 581 672',2.5,ORANGE,.9)
arrow_tip(581,672,dx=-1,dy=0,color=ORANGE)

line('M49 803 Q647 801 1247 803',.8,INK,.45)
text(650,833,'Each book stands alone. Follow the question you need to answer.',29,anchor='middle',bold=True)
s.append('</svg>')
OUT.write_text('\n'.join(s),encoding='utf-8')
print(OUT)

if '--render' in __import__('sys').argv:
    import os, subprocess, tempfile
    from PIL import Image
    with tempfile.TemporaryDirectory(prefix='reading-map-render-') as temp:
        temp=Path(temp)
        config=temp/'fonts.conf'
        config.write_text('''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig><include>/etc/fonts/fonts.conf</include>
<dir>'''+escape(str(HERE/'type'))+'''</dir><cachedir>'''+escape(str(temp/'font-cache'))+'''</cachedir></fontconfig>''')
        env=os.environ.copy()
        env['FONTCONFIG_FILE']=str(config)
        png=temp/'reading-map.png'
        subprocess.run(['inkscape',str(OUT),'--export-filename='+str(png),'--export-width=2600'],check=True,env=env)
        target=HERE.parent/'assets'/'reading-map.jpg'
        target.parent.mkdir(parents=True,exist_ok=True)
        Image.open(png).convert('RGB').save(target,quality=96,subsampling=0,dpi=(220,220))
        print(target)
