"""Shared pen-and-crayon primitives for exact editorial book-coverage diagrams."""
from pathlib import Path
from html import escape
import math, random, subprocess, os, tempfile
from PIL import Image, ImageFont

HERE = Path(__file__).resolve().parent
INK = '#243544'
BLUE = '#397ba1'
ORANGE = '#d77c39'
MUTED = '#4c6575'
W, H = 1400, 900

class Canvas:
    def __init__(self, name, description, seed=20261125):
        self.name, self.description = name, description
        self.r = random.Random(seed)
        self.s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="2800" height="1800" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
                  f'<title id="title">{escape(name.replace("-", " "))}</title>',
                  f'<desc id="desc">{escape(description)}</desc>',
                  '<rect width="1400" height="900" fill="white"/>']
        self.fonts = {}

    def line(self, path, width=2, color=INK, opacity=1, dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ''
        self.s.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}"{extra}/>')

    def text(self, x, y, value, size=28, color=INK, anchor='start', bold=False, max_width=None):
        if max_width:
            while size >= 18:
                key=round(size*10)
                if key not in self.fonts:
                    self.fonts[key]=ImageFont.truetype(str(HERE/'type/SketchHand.ttf'),key)
                if self.fonts[key].getlength(value)/10 <= max_width:
                    break
                size -= .25
            if size < 18:
                raise ValueError(f'Text too wide: {value}')
        self.s.append(f'<text x="{x}" y="{y}" font-family="SketchHand" font-size="{size}" text-anchor="{anchor}" fill="{color}" stroke="{color}" stroke-width="{.45 if bold else .12}" stroke-linejoin="round" paint-order="stroke">{escape(value)}</text>')

    def lines(self, x, y, values, size=28, leading=35, **kw):
        for i,value in enumerate(values):
            self.text(x,y+i*leading,value,size=size,**kw)

    def swatch(self, x,y,w,h,color=BLUE,opacity=.16):
        self.s.append(f'<path d="M{x-2} {y+2} L{x+w+3} {y-1} L{x+w} {y+h+2} L{x+1} {y+h-1} Z" fill="{color}" opacity="{opacity*.6}"/>')
        for _ in range(int(h*1.5)):
            yy=y+self.r.uniform(0,h)
            self.line(f'M{x+self.r.uniform(-3,8):.2f} {yy:.2f} Q{x+w*.45:.2f} {yy+self.r.uniform(-1.3,1.3):.2f} {x+w+self.r.uniform(-7,3):.2f} {yy+self.r.uniform(-1.3,1.3):.2f}',self.r.uniform(.45,1.05),color,opacity*self.r.uniform(.5,1))

    def box(self,x,y,w,h,color=INK,fill=None):
        if fill:
            self.s.append(f'<rect x="{x+3}" y="{y+2}" width="{w-5}" height="{h-5}" fill="{fill}"/>')
        self.line(f'M{x} {y+3} Q{x+w*.4} {y-1} {x+w-3} {y+1} L{x+w+1} {y+h-3} Q{x+w*.54} {y+h+1} {x+1} {y+h-1} Z',2.1,color)
        self.line(f'M{x+6} {y+h+2} Q{x+w*.55} {y+h+5} {x+w+5} {y+h+2} L{x+w+6} {y+9}',.9,color,.6)

    def ellipse(self,x,y,rx,ry,color=INK):
        self.line(f'M{x-rx} {y} C{x-rx-5} {y-ry*.9} {x-rx*.3} {y-ry-4} {x} {y-ry} C{x+rx*.7} {y-ry-3} {x+rx+3} {y-ry*.5} {x+rx} {y} C{x+rx+4} {y+ry*.8} {x+rx*.2} {y+ry+5} {x} {y+ry} C{x-rx*.8} {y+ry+3} {x-rx-3} {y+ry*.4} {x-rx} {y} Z',2.1,color)

    def arrow(self,path,end,direction=(1,0),color=BLUE,width=2.3):
        self.line(path,width,color,.9)
        x,y=end; dx,dy=direction
        norm=math.hypot(dx,dy); dx,dy=dx/norm,dy/norm
        bx,by=x-dx*12,y-dy*12
        px,py=-dy*5,dx*5
        self.line(f'M{bx+px} {by+py} L{x} {y} L{bx-px} {by-py}',width,color)

    def header(self,kicker,title_lines,subtitle):
        self.swatch(54,28,850,31,ORANGE,.17)
        self.text(64,53,kicker,size=24,bold=True,max_width=1260)
        self.lines(55,111,title_lines,size=42,leading=49,bold=True,max_width=1280)
        last=111+(len(title_lines)-1)*49
        self.text(56,last+43,subtitle,size=28,color=MUTED,max_width=1270)
        self.line(f'M55 {last+63} Q700 {last+61} 1344 {last+63}',.85,INK,.4)
        return last+84

    def footer(self,text):
        self.line('M55 841 Q700 839 1344 841',.8,INK,.4)
        self.text(700,879,text,size=26,anchor='middle',bold=True,max_width=1280)

    def save(self,render=True):
        svg=HERE/(self.name+'.svg')
        svg.write_text('\n'.join(self.s+['</svg>']),encoding='utf-8')
        if render:
            with tempfile.TemporaryDirectory(prefix=self.name+'-') as temp:
                temp=Path(temp)
                config=temp/'fonts.conf'
                config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><include>/etc/fonts/fonts.conf</include><dir>'+escape(str(HERE/'type'))+'</dir><cachedir>'+escape(str(temp/'font-cache'))+'</cachedir></fontconfig>')
                env=os.environ.copy();env['FONTCONFIG_FILE']=str(config)
                png=temp/(self.name+'.png')
                subprocess.run(['inkscape',str(svg),'--export-filename='+str(png),'--export-width=2800'],check=True,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                jpg=HERE.parent/'assets'/(self.name+'.jpg')
                Image.open(png).convert('RGB').save(jpg,quality=96,subsampling=0,dpi=(240,240))
                print(jpg)
        return svg
