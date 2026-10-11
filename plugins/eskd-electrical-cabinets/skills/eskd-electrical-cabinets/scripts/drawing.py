"""Paper-mm vector primitives following the accepted drawing profile.
Project metadata and routes are explicit; there is no inherited device or net map.
Requires reportlab, PyMuPDF and ezdxf. Review final PDF and DXF before release.
"""
from pathlib import Path
import math, json, re
import fitz, ezdxf
from ezdxf.enums import TextEntityAlignment
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / 'assets' / 'fonts'
for name, fn in [('F','DejaVuSans.ttf'),('FB','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS/fn)))
SHEETS, PINS, REFERENCES, SECTIONS = [], {}, [], set()
def resolve_refs(text):
    return str(text)  # Never infer or silently rewrite destination sections.
def section_for(value, net='', label=''):
    value = str(value)
    if not re.fullmatch(r'\d+\.\d+', value):
        raise ValueError('Explicit sheet.section reference required: '+value)
    return value

def register(pin,net,sheet):
    if not pin:return
    net=str(net)
    if pin in PINS and PINS[pin]['net']!=net:
        raise ValueError((pin,PINS[pin],net))
    PINS.setdefault(pin,{'net':net,'sheets':[]})
    if sheet not in PINS[pin]['sheets']:PINS[pin]['sheets'].append(sheet)

class Sheet:
    def __init__(self, n, title, size='A3', revision='', code='Э3', total=1,
                 *, out, metadata=None, terminal_style='circle', basename=None):
        self.meta = metadata or {}
        self.n, self.size, self.code, self.total = n, size, code, total
        self.W,self.H={'A0':(1189,841),'A1':(841,594),'A2':(594,420),
                       'A3':(420,297),'A4':(210,297)}[size]
        if terminal_style not in ('circle','rectangle'):
            raise ValueError('terminal_style must be circle or rectangle')
        self.terminal_style = terminal_style
        self.out = Path(out); self.out.mkdir(parents=True, exist_ok=True)
        self.designation = self.meta.get('designation','')
        self.revision, self.title = revision, title
        self.name = basename or f'sheet_{n:02d}'
        if Path(self.name).name != self.name:
            raise ValueError('basename must not contain directories')
        self.c=canvas.Canvas(str(self.out/(self.name+'.pdf')),pagesize=(self.W*mm,self.H*mm))
        self.c.setTitle(self.designation+' '+title)
        self.c.setAuthor(self.meta.get('author',''))
        self.c.setSubject(self.meta.get('subject',''))
        self.doc=ezdxf.new('R2013'); self.doc.units=4
        self.doc.header['$INSUNITS']=4; self.doc.header['$MEASUREMENT']=1
        for fn in ['F','FB']:
            self.doc.styles.new(fn,dxfattribs={'font':'DejaVuSans'+('-Bold' if fn=='FB' else '')+'.ttf'})
        self.doc.linetypes.new('SCHEME_DASH',dxfattribs={'description':'dashed','pattern':[5,3,-2]})
        for layer in ['FRAME','WIRE','PE','SYMBOL','TEXT','NOTES','MECHANICAL']:
            self.doc.layers.new(layer,dxfattribs={'color':7})
        self.msp=self.doc.modelspace()
        self.texts=[];self.segments=[];self.boxes=[];self.term_windows=[];self.rotated_text_count=0
        self.frame();SHEETS.append(self)
    def ln(self,x1,y1,x2,y2,w=.35,layer='WIRE',dash=False):
        parts=self.clip_line(x1,y1,x2,y2) if layer in ['WIRE','PE'] else [(x1,y1,x2,y2)]
        for p in parts:self.raw_line(*p,w,layer,dash)
    def raw_line(self,x1,y1,x2,y2,w=.35,layer='WIRE',dash=False):
        self.c.setLineWidth(w*mm);self.c.setDash([3*mm,2*mm] if dash else [])
        self.c.line(x1*mm,(self.H-y1)*mm,x2*mm,(self.H-y2)*mm)
        a={'layer':layer,'lineweight':round(100*w)}
        if dash:a['linetype']='SCHEME_DASH'
        self.msp.add_line((x1,self.H-y1),(x2,self.H-y2),dxfattribs=a)
        self.segments.append([x1,y1,x2,y2,layer])
    def clip_line(self,x1,y1,x2,y2):
        parts=[(x1,y1,x2,y2)]
        for a,b,c,d in self.term_windows:
            nxt=[]
            for u,v,w,z in parts:
                if abs(v-z)<1e-7 and b<v<d:
                    lo,hi=sorted([u,w])
                    if lo<c and hi>a:
                        if lo<a:nxt.append((lo,v,min(a,hi),v))
                        if hi>c:nxt.append((max(c,lo),v,hi,v))
                    else:nxt.append((u,v,w,z))
                elif abs(u-w)<1e-7 and a<u<c:
                    lo,hi=sorted([v,z])
                    if lo<d and hi>b:
                        if lo<b:nxt.append((u,lo,u,min(b,hi)))
                        if hi>d:nxt.append((u,max(d,lo),u,hi))
                    else:nxt.append((u,v,w,z))
                else:nxt.append((u,v,w,z))
            parts=nxt
        return parts
    def poly(self,pts,w=.35,layer='WIRE',dash=False):
        for a,b in zip(pts,pts[1:]):self.ln(*a,*b,w,layer,dash)
    def rect(self,x,y,w,h,lw=.35,layer='SYMBOL',dash=False):
        self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)],lw,layer,dash)
    def circle(self,x,y,r=1,fill=False):
        self.c.setDash([]);self.c.setLineWidth(.3*mm)
        self.c.circle(x*mm,(self.H-y)*mm,r*mm,stroke=not fill,fill=fill)
        if fill:
            p=[(x+r*math.cos(i*math.tau/16),self.H-y+r*math.sin(i*math.tau/16)) for i in range(16)]
            self.msp.add_hatch(color=7,dxfattribs={'layer':'WIRE'}).paths.add_polyline_path(p,is_closed=True)
        else:self.msp.add_circle((x,self.H-y),r,dxfattribs={'layer':'SYMBOL','lineweight':30})
    def dot(self,x,y):self.circle(x,y,.65,True)
    def width(self,s,h=2.5,b=False):return pdfmetrics.stringWidth(str(s),'FB' if b else 'F',h/.729*mm)/mm
    def t(self,x,y,s,h=2.5,b=False,a='left',rot=0,layer='TEXT'):
        s=resolve_refs(str(s));f='FB' if b else 'F';fs=h/.729
        for pg in re.findall(r'л\.\s*(\d+)',s):REFERENCES.append({'from':self.n,'to':int(pg.split('.')[0]),'section':pg,'label':s})
        m=re.match(r'^(?:PE|[ABC]\d+|N\d+|\d+)\s*/\s*(\d+\.\d+(?:,\d+\.\d+)*)\b',s)
        if m:
            for pg in m[1].split(','):REFERENCES.append({'from':self.n,'to':int(pg.split('.')[0]),'section':pg,'label':s})
        c=self.c;c.saveState();c.setFont(f,fs*mm);c.translate(x*mm,(self.H-y)*mm);c.rotate(rot)
        {'left':c.drawString,'right':c.drawRightString,'center':c.drawCentredString}[a](0,0,s);c.restoreState()
        e=self.msp.add_text(s,dxfattribs={'height':h,'style':f,'layer':layer,'rotation':rot})
        e.set_placement((x,self.H-y),align={'left':TextEntityAlignment.LEFT,'center':TextEntityAlignment.CENTER,'right':TextEntityAlignment.RIGHT}[a])
        if rot: self.rotated_text_count += 1
        if not rot:
            width=self.width(s,h,b);xx=x-({'left':0,'right':width,'center':width/2}[a])
            self.texts.append({'text':s,'bbox':[xx,y-h*1.1,xx+width,y+h*.29],'layer':layer,'height':h})
    def lines(self,x,y,ss,h=2.5,step=6,b=False):
        for i,s in enumerate(ss):self.t(x,y+i*step,s,h,b)
    def wrap(self,text,width,h=2.5,b=False):
        out=[]
        for para in str(text).split('\n'):
            line=''
            for word in para.split():
                nxt=(line+' '+word).strip()
                if line and self.width(nxt,h,b)>width:out.append(line);line=word
                else:line=nxt
            out.append(line)
        return out
    def paragraph(self,x,y,text,width,h=2.5,step=5.5,b=False):
        ss=self.wrap(text,width,h,b);self.lines(x,y,ss,h,step,b);return y+len(ss)*step
    def heading(self,x,y,text,width):
        m=re.match(r'(\d+\.\d+)\s',text)
        if m:SECTIONS.add(m[1])
        self.t(x,y,text,3.5,True);self.ln(x,y+3,x+width,y+3,.25,'NOTES')
    def arr(self,x,y,d='right'):
        q={'right':[(x-3,y-1.5),(x,y),(x-3,y+1.5)],'left':[(x+3,y-1.5),(x,y),(x+3,y+1.5)],'down':[(x-1.5,y-3),(x,y),(x+1.5,y-3)],'up':[(x-1.5,y+3),(x,y),(x+1.5,y+3)]}
        self.poly(q[d],.3,'SYMBOL')
    def link(self,x,y,net,ref='',to=False,length=20,page=None):
        self.ln(x,y,x+length,y)
        self.arr(x+length if to else x,y,'right' if to else 'right')
        self.t(x+length/2,y-3,str(net)+(f' /{section_for(page,net)}' if page else ''),2.5,a='center')
        if ref:self.t(x,y+6,ref,2.5)
    def cross(self,x,y,net,page,to=False,length=24):
        self.link(x,y,net,to=to,length=length,page=page)
    def term(self,x,y,label='',below=False,pin=None,net=None):
        if self.terminal_style == 'circle':
            r=1.15
            self.term_windows.append((x-r,y-r,x+r,y+r))
            self.c.saveState(); self.c.setFillColorRGB(1,1,1)
            self.c.circle(x*mm,(self.H-y)*mm,r*mm,stroke=0,fill=1)
            self.c.restoreState(); self.circle(x,y,r)
            if label:self.t(x,y+(8.8 if below else -3.2),label,2.5,a='center')
            if pin is not None:register(pin,net,self.n)
            return
        parts=str(label).rsplit(':',1)
        tag,num=(parts[0],parts[1]) if len(parts)==2 else ('',str(label))
        num=re.sub(r'^(\d+)[ab]$',r'\1',num)
        width=max(10,self.width(num,2.5)+3)
        box=(x-width/2,y-3.5,x+width/2,y+3.5)
        self.term_windows.append(box)
        self.c.saveState();self.c.setFillColorRGB(1,1,1)
        self.c.rect(box[0]*mm,(self.H-box[3])*mm,width*mm,7*mm,stroke=0,fill=1)
        self.c.restoreState()
        self.rect(box[0],box[1],width,7,.3)
        if num:self.t(x,y+1.25,num,2.5,a='center')
        if tag:self.t(x,y+(10 if below else -6),tag,2.5,a='center')
        if pin is not None:register(pin,net,self.n)
    def pin(self,x,y,pin,net,label=None,side='left',h=2.5):
        self.circle(x,y,.7);register(pin,net,self.n)
        if label is not None:self.t(x+(3 if side=='left' else -3),y+1,label,h,a='left' if side=='left' else 'right')
    def earth(self,x,y,label=''):
        self.ln(x,y,x,y+3,.5,'PE')
        for dy,half in [(3,3),(4.5,2),(6,1)]:self.ln(x-half,y+dy,x+half,y+dy,.4,'PE')
        if label:self.t(x+5,y+5,label)
    def contact(self,x,y,name,pins=('11','14'),nc=False,ref='',push=False):
        self.ln(x-12,y,x-4,y);self.ln(x+4,y,x+12,y)
        self.circle(x-4,y,.55)
        self.ln(x+4,y-2,x+4,y+2,.35,'SYMBOL')
        self.ln(x-4,y,x+4,y-1 if nc else y-5,.35,'SYMBOL')
        if push:
            self.ln(x,y-6,x,y-11,.25,'MECHANICAL');self.ln(x-3,y-11,x+3,y-11,.35,'SYMBOL')
        if name:self.t(x,y-(14 if push else 8),name,3,True,'center')
        for xx,p in [(x-8,pins[0]),(x+8,pins[1])]:self.t(xx,y+5.5,p,2.5,a='center')
        if ref:self.t(x,y+12,ref,2.5,a='center')
    def coil(self,x,y,tag,left='A1+',right='A2−',model='',internal=False):
        self.rect(x-8,y-4,16,8);self.ln(x-16,y,x-8,y);self.ln(x+8,y,x+16,y)
        self.t(x,y-8,tag,3,True,'center')
        self.t(x-20 if internal else x-11,y+6,left,2.5,a='right');self.t(x+20 if internal else x+11,y+6,right,2.5)
        if internal:
            self.rect(x-18,y-6,36,22,.2,'MECHANICAL',True)
            self.diode(x,y+10,x-14,x+14,y,left.startswith('A1'))
        if model:self.t(x,y+23,model,2.5,a='center')
    def diode(self,x,y,l,r,mainy,cathode_left=True):
        self.poly([(l,mainy),(l,y),(x-3,y)]);self.poly([(x+3,y),(r,y),(r,mainy)])
        sign=-1 if cathode_left else 1
        self.poly([(x-sign*2,y-2),(x+sign*2,y),(x-sign*2,y+2),(x-sign*2,y-2)],.3,'SYMBOL')
        self.ln(x+sign*2,y-2.5,x+sign*2,y+2.5,.3,'SYMBOL')
        self.dot(l,mainy);self.dot(r,mainy)
    def fuse(self,x,y,tag,rating):
        self.ln(x-14,y,x+14,y);self.rect(x-6,y-2.5,12,5)
        self.rect(x-14,y-5,28,10,.2,'MECHANICAL',True)
        self.t(x,y-9,tag,3,True,'center');self.t(x,y+11,rating,2.5,a='center')
        self.t(x-11,y-2,'1',2.5,a='right');self.t(x+11,y-2,'2',2.5)
    def vsw(self,x,y,breaker=False,pins=('1','2'),nc=False):
        self.ln(x,y-10,x,y-3);self.ln(x,y+3,x,y+10)
        self.circle(x,y+3,.55);self.ln(x,y+3,x+(0 if nc else 3),y-3,.35,'SYMBOL');self.ln(x-2,y-3,x+2,y-3,.35,'SYMBOL')
        if breaker:self.poly([(x-2,y-2),(x-4,y-2),(x-4,y+2),(x-2,y+2)],.3,'SYMBOL')
        if pins:
            self.t(x-2,y-6,pins[0],2.5,a='right');self.t(x-2,y+14,pins[1],2.5,a='right')
    def multipole(self,xs,y,breaker=True,pins=None):
        for i,x in enumerate(xs):self.vsw(x,y,breaker,pins[i] if pins else (str(2*i+1),str(2*i+2)))
        self.ln(xs[0],y,xs[-1],y,.2,'MECHANICAL',True)
    def table(self,x,y,widths,headers,rows,rh=9,h=2.5):
        wrapped=[]
        for i,row in enumerate([headers]+rows):
            cell=[self.wrap(v,w-4,h,i==0) for v,w in zip(row,widths)]
            wrapped.append((cell,max(rh,max(len(t) for t in cell)*5+3)))
        height=sum(v for _,v in wrapped);w=sum(widths);self.rect(x,y,w,height,.3,'NOTES')
        xx=x
        for cw in widths[:-1]:xx+=cw;self.ln(xx,y,xx,y+height,.2,'NOTES')
        yy=y
        for i,(cells,ch) in enumerate(wrapped):
            if i:self.ln(x,yy,x+w,yy,.2,'NOTES')
            xx=x
            for lines,cw in zip(cells,widths):self.lines(xx+2,yy+5.7,lines,h,5,i==0);xx+=cw
            yy+=ch
        return yy
    def ref(self,x,y,page,label='',a='left'):
        sec=section_for(page,label=label)
        assert 1<=int(sec.split('.')[0])<=self.total
        REFERENCES.append({'from':self.n,'to':int(sec.split('.')[0]),'section':sec,'label':label})
        self.t(x,y,(label+' ' if label else '')+f'/{sec}',2.5,a=a)
    def frame(self):
        W,H=self.W,self.H;self.rect(20,5,W-25,H-10,.5,'FRAME')
        # Additional graph 26: designation turned 180 degrees on landscape sheets.
        self.rect(20,5,70,14,.35,'FRAME');self.t(55,10,self.designation,3.5,a='center',rot=180,layer='FRAME')
        # Inventory fields; handwritten entries intentionally blank.
        yy=H-5
        for height,label in [(25,'Инв. № подл.'),(35,'Подп. и дата'),(25,'Взам. инв. №'),(25,'Инв. № дубл.'),(35,'Подп. и дата')]:
            yy-=height;self.rect(8,yy,12,height,.25,'FRAME');self.ln(13,yy,13,yy+height,.25,'FRAME')
            self.t(11.7,yy+height/2,label,2,a='center',rot=90,layer='FRAME')
        sx=W-190;sy=H-(60 if self.n==1 else 20);ht=55 if self.n==1 else 15
        self.rect(sx,sy,185,ht,.5,'FRAME')
        for xx in [7,17,40,55,65]:self.ln(sx+xx,sy,sx+xx,sy+(20 if self.n==1 else 15),.25,'FRAME')
        for yy in range(5,20 if self.n==1 else 15,5):self.ln(sx,sy+yy,sx+65,sy+yy,.25,'FRAME')
        for xx,lab in [(3.5,'Изм.'),(12,'Лист'),(28.5,'№ докум.'),(47.5,'Подп.'),(60,'Дата')]:
            self.t(sx+xx,sy+(18.5 if self.n==1 else 13.5),lab,1.8,a='center',layer='FRAME')
        if self.n==1:
            self.ln(sx+65,sy,sx+65,sy+55,.5,'FRAME')
            self.ln(sx+175,sy,sx+175,sy+15,.25,'FRAME');self.ln(sx+175,sy+5,sx+185,sy+5,.25,'FRAME')
            self.t(sx+180,sy+3.5,'Вер.',1.8,a='center',layer='FRAME');self.t(sx+180,sy+12,str(self.revision),3,a='center',layer='FRAME')
            self.t(sx+120,sy+10,self.designation,5,a='center',layer='FRAME')
            for yy in [15,40]:self.ln(sx+65,sy+yy,sx+185,sy+yy,.5,'FRAME')
            self.ln(sx+135,sy+15,sx+135,sy+55,.5,'FRAME')
            for yy in [20,35]:self.ln(sx+135,sy+yy,sx+185,sy+yy,.25,'FRAME')
            for xx in [150,167]:self.ln(sx+xx,sy+15,sx+xx,sy+35,.25,'FRAME')
            for xx in [140,145]:self.ln(sx+xx,sy+20,sx+xx,sy+35,.25,'FRAME')
            for xx,lab in [(142.5,'Лит.'),(158.5,'Масса'),(176,'Масштаб')]:self.t(sx+xx,sy+18.5,lab,1.8,a='center',layer='FRAME')
            self.t(sx+138,sy+38.6,'Лист 1',1.9,layer='FRAME');self.t(sx+160,sy+38.6,f'Листов {self.total}',1.9,layer='FRAME')
            # Name field is centered and fits its 70 mm width.
            self.t(sx+100,sy+21,self.meta.get('object',''),2.5,a='center',layer='FRAME')
            self.t(sx+100,sy+28,('Схема электрическая' if self.code in ['Э3','Э4'] else 'Перечень' if self.code=='ПЭ3' else 'Таблица'),2.5,a='center',layer='FRAME')
            self.t(sx+100,sy+35,('принципиальная' if self.code=='Э3' else 'соединений' if self.code in ['Э4','ТЭ4'] else 'элементов'),2.5,a='center',layer='FRAME')
            for yy in range(20,55,5):self.ln(sx,sy+yy,sx+65,sy+yy,.25,'FRAME')
            for xx in [17,40,55]:self.ln(sx+xx,sy+20,sx+xx,sy+55,.25,'FRAME')
            for i,lab in enumerate(['Разраб.','Пров.','Т.контр.','','Н.контр.','Утв.','']):
                if lab:self.t(sx+1,sy+23.5+5*i,lab,1.9,layer='FRAME')
        else:
            for xx in [165,175]:self.ln(sx+xx,sy,sx+xx,sy+15,.25,'FRAME')
            self.ln(sx+165,sy+5,sx+185,sy+5,.25,'FRAME')
            self.t(sx+115,sy+10,self.designation,5,a='center',layer='FRAME')
            for xx,lab,val in [(170,'Вер.',str(self.revision)),(180,'Лист',str(self.n))]:
                self.t(sx+xx,sy+3.5,lab,1.8,a='center',layer='FRAME');self.t(sx+xx,sy+12,val,3,a='center',layer='FRAME')
        self.t(W-7,H-1.5,'Формат '+self.size,1.8,a='right',layer='FRAME')
        self.t(28,31,f'{self.n}. {self.title}',4.5,True)
        self.t(W-10,13,self.meta.get('header',''),3,a='right')
        self.t(W-10,21,self.meta.get('date',''),2.5,a='right')
    def finish(self):
        self.c.showPage();self.c.save()
        # Remove line portions hidden by terminal cells from DXF and QA geometry.
        for e in list(self.msp.query('LINE')):
            if e.dxf.layer not in ['WIRE','PE']:continue
            a=e.dxf.start;b=e.dxf.end;orig=(a.x,self.H-a.y,b.x,self.H-b.y)
            parts=self.clip_line(*orig)
            if parts!=[orig]:
                attrs={k:e.dxf.get(k) for k in ['layer','lineweight','linetype'] if e.dxf.hasattr(k)}
                self.msp.delete_entity(e)
                for x1,y1,x2,y2 in parts:self.msp.add_line((x1,self.H-y1),(x2,self.H-y2),dxfattribs=attrs)
        self.segments=[[*p,seg[4]] for seg in self.segments for p in (self.clip_line(*seg[:4]) if seg[4] in ['WIRE','PE'] else [seg[:4]])]
        self.doc.saveas(self.out/(self.name+'.dxf'))
        d=fitz.open(self.out/(self.name+'.pdf'));(self.out/(self.name+'.svg')).write_text(d[0].get_svg_image(),encoding='utf-8');d.close()
        (self.out/(self.name+'_layout.json')).write_text(json.dumps({'format_mm':[self.W,self.H],'sheet':self.n,'texts':self.texts,'lines':self.segments,'rotated_text_count':self.rotated_text_count,'reserved_boxes':[{'name':'title_block','bbox':[self.W-190,self.H-(60 if self.n==1 else 20),self.W-5,self.H-5]}]},ensure_ascii=False,indent=2),encoding='utf-8')
