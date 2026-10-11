#!/usr/bin/env python3
"""Build the independent educational reference from explicit data; never a project default."""
import argparse,hashlib,json
from pathlib import Path
import fitz
from drawing import Sheet
from audit_project import audit as audit_model
from audit_assembly import audit as audit_assembly

ROOT=Path(__file__).resolve().parents[1]

def build(model,out):
    raw=model.read_bytes();d=json.loads(raw);out.mkdir(parents=True,exist_ok=True)
    for fn in (audit_model,audit_assembly):
        r=fn(d)
        if not r['passed_within_scope']:raise ValueError(r['errors'])
    devices={x['id']:x for x in d['devices']};ports={x['id']:x for x in d['ports']}
    views=[];files=[];pdfs=[]
    total=len(d['sheets'])
    def sheet(n,size='A2',style='circle'):
        title=d['sheets'][n-1]['title']
        s=Sheet(n,title,size,revision='1',total=total,out=out,terminal_style=style,
            metadata={'designation':d['project']['name']+'.УЧ','object':'Учебный пример','header':'Условные аппараты и размеры'})
        s.heading(28,49,f'{n}.1  {title}',s.W-45)
        return s
    def finish(s):
        s.finish();pdfs.append(out/(s.name+'.pdf'))
        for ext in ('.pdf','.dxf','.svg','_layout.json'):files.append(s.name+ext)
    def wire(s,a,b,text='',caption=''):
        s.poly([a,b])
        cx=(a[0]+b[0])/2;cy=(a[1]+b[1])/2
        if text:s.t(cx,cy-3,str(text),2.5,a='center')
        if caption:s.t(cx,cy+6,caption,2.5,a='center')
    def boundary(s,x,y,w,h,label):
        s.rect(x,y,w,h,.25,'MECHANICAL',True);s.t(x+4,y+8,label,3,True)
    def dimensions(s,x,y,w,h,scale):
        s.ln(x,y-6,x+w/scale,y-6,.2,'MECHANICAL')
        for a in (x,x+w/scale):s.ln(a,y-9,a,y,.2,'MECHANICAL')
        s.t(x+w/scale/2,y-8,str(w),2.5,a='center')
        s.ln(x+w/scale+7,y,x+w/scale+7,y+h/scale,.2,'MECHANICAL')
        for b in (y,y+h/scale):s.ln(x+w/scale+3,b,x+w/scale+10,b,.2,'MECHANICAL')
        s.t(x+w/scale+12,y+h/scale/2,str(h),2.5)
    def table_proof(s,x,y,widths,headers,rows):
        yy=y;result=[]
        for ri,row in enumerate([headers]+rows):
            wrapped=[s.wrap(str(v),cw-4,2.5,ri==0) for v,cw in zip(row,widths)]
            height=max(9,max(len(v) for v in wrapped)*5+3)
            # Capture the text actually emitted, independently from the semantic rows.
            texts=s.texts
            if ri:
                first=str(row[0]);matches=[t for t in texts if t['text']==first and abs(t['bbox'][0]-(x+2))<.1]
                if matches:
                    yy=matches[0]['bbox'][1]+2.75-5.7
                cells=[];boxes=[];xx=x
                for cw,v in zip(widths,row):
                    lines=[t['text'] for t in texts if xx<=t['bbox'][0]<xx+cw and yy<t['bbox'][1]+2.75<yy+height]
                    cells.append(' '.join(lines));boxes.append([xx,yy,xx+cw,yy+height]);xx+=cw
                result.append({'values':[str(v) for v in row],'rendered':cells,'boxes_mm':boxes})
            yy+=height
        return result

    s=sheet(1,style='rectangle')
    boundary(s,150,70,330,260,'CAB1')
    s.rect(30,87,85,100,.35);s.t(72.5,100,'Питание',3,True,'center')
    for y,net,num,qp,glabel in [(120,'L',1,('1','2'),'L'),(150,'N',2,('3','4'),'N')]:
        s.pin(115,y,'FIELD.POWER:'+net,net,net,side='right')
        wire(s,(115,y),(170,y),f'W0/{num}')
        s.term(170,y,'XT1:'+str(num));wire(s,(170,y),(213,y),net)
        s.contact(225,y,'QF1' if num==1 else '',pins=qp)
        wire(s,(237,y),(280,y),net+'1')
    s.rect(280,107,55,60,.5);s.t(307.5,102,'G1',3,True,'center')
    s.ln(225,120,225,150,.2,'MECHANICAL',True)
    s.pin(280,120,'CAB1.G1:L','L1','L');s.pin(280,150,'CAB1.G1:N','N1','N')
    s.pin(335,120,'CAB1.G1:+V','+24','+V',side='right');s.pin(335,150,'CAB1.G1:-V','0V','-V',side='right')
    s.link(335,120,'+24',page='3.1',to=True,length=27)
    s.link(335,150,'0V',page='3.1',to=True,length=27)
    s.rect(385,100,48,100,.5);s.t(409,95,'D1',3,True,'center')
    s.poly([(280,120),(266,120),(266,87),(375,87),(375,120),(385,120)])
    s.t(321,84,'L1',2.5,a='center')
    s.poly([(280,150),(260,150),(260,218),(375,218),(375,150),(385,150)])
    s.t(316,215,'N1',2.5,a='center')
    s.pin(385,120,'CAB1.D1:L','L1','L');s.pin(385,150,'CAB1.D1:N','N1','N')
    s.rect(520,107,52,106,.35);s.t(546,102,'M1',3,True,'center')
    for i,(y,net) in enumerate([(120,'U'),(150,'V'),(180,'W')],1):
        s.pin(433,y,'CAB1.D1:'+net,net,net,side='right')
        wire(s,(433,y),(460,y),net);s.term(460,y,'XT2:'+str(i))
        wire(s,(460,y),(520,y),f'W1/{i}');s.pin(520,y,'FIELD.M1:'+net,net,net)
    # Protective bonds are independent of the control common.
    s.ln(115,180,170,180,layer='PE');s.t(142,177,'W0/3',2.5,a='center');s.term(170,180,'XT1:3')
    s.poly([(170,180),(188,180),(188,270),(438,270)],layer='PE');s.t(215,265,'PE1',3,True)
    for x,title in [(248,'Корпус'),(302,'Плита')]:
        s.ln(x,270,x,292,layer='PE');s.dot(x,270);s.earth(x,292);s.t(x,308,title,2.5,a='center')
    s.poly([(248,284),(356,284),(356,292)],layer='PE');s.dot(248,284);s.earth(356,292);s.t(356,308,'Дверь',2.5,a='center')
    s.poly([(418,270),(418,238),(385,238),(385,192)],layer='PE');s.t(390,235,'PE',2.5)
    s.ln(438,270,460,270,layer='PE');s.term(460,270,'XT2:4')
    s.poly([(460,270),(497,270),(497,204),(520,204)],layer='PE');s.t(479,267,'W1/4',2.5,a='center')
    s.pin(520,204,'FIELD.M1:PE','PE','PE')
    s.paragraph(28,335,'Сечения и цвета приведены в таблице соединений. Аппараты, выводы и размеры заданы для учебного примера; номиналы защиты здесь не выбираются.',520)
    finish(s)

    s=sheet(2)
    boundary(s,30,75,125,100,'CAB2');boundary(s,457,75,118,100,'CAB2')
    s.poly([(182,75),(442,75),(442,180),(575,180),(575,327),(182,327),(182,75)],.25,'MECHANICAL',True)
    s.t(186,83,'CAB1',3,True)
    s.rect(280,95,100,220,.5);s.t(330,109,'A1',3.5,True,'center')
    s.t(296,127,'DI',3,True);s.t(364,127,'DO',3,True,'right')
    s.contact(50,145,'SB2',pins=('1','2'),nc=True,push=True)
    s.contact(95,145,'SB1',pins=('3','4'),push=True)
    wire(s,(62,145),(83,145),'15')
    wire(s,(107,145),(135,145),'20');s.term(135,145,'XT1:2')
    wire(s,(135,145),(218,145),'W2/2');s.term(218,145,'XT3:2')
    wire(s,(218,145),(280,145),'20','Пуск')
    s.pin(280,145,'CAB1.A1:DI0','20','DI0');s.t(300,154,'X0',2.5)
    s.t(36,167,'Питание SB2:1: +24 /3.1',2.5)
    s.pin(380,145,'CAB1.A1:DO0','30','DO0',side='right');s.t(354,154,'Y0',2.5,a='right')
    wire(s,(380,145),(423,145),'30','Работа');s.term(423,145,'XT3:3')
    wire(s,(423,145),(478,145),'W2/3');s.term(478,145,'XT1:3')
    wire(s,(478,145),(535,145),'30');s.circle(540,145,5);s.t(540,133,'HL1',3,True,'center')
    s.ln(545,145,561,145);s.t(553,142,'0V',2.5,a='center')
    s.t(468,167,'Возврат: XT1:4, W2/4',2.5)
    s.poly([(390,145),(390,213),(478,213)]);s.dot(390,145);s.t(442,210,'30',2.5,a='center')
    s.coil(494,213,'K1',left='A1',right='A2');s.ref(494,235,'3.2',a='center')
    s.link(510,213,'0V',page='3.1',to=True,length=52)
    s.t(296,272,'AI',3,True);s.t(364,272,'AO',3,True,'right')
    s.rect(40,271,70,45,.35);s.t(75,283,'B1',3,True,'center')
    s.pin(110,295,'FIELD.B1:OUT','50','OUT',side='right')
    wire(s,(110,295),(218,295),'W4/2');s.term(218,295,'XT4:2')
    wire(s,(218,295),(280,295),'50','Измерение');s.pin(280,295,'CAB1.A1:AI+','50','AI+')
    s.t(44,310,'+ / -: W4/1, W4/3',2.5)
    s.pin(380,295,'CAB1.A1:AO+','60','AO+',side='right');wire(s,(380,295),(520,295),'60','Задание скорости')
    s.rect(520,270,55,48,.35);s.t(548,283,'D1',3,True,'center');s.pin(520,295,'CAB1.D1:AVI','60','AVI')
    s.t(534,311,'ACM: 0V',2.5)
    s.t(28,350,'DI/DO - дискретные входы/выходы; AI/AO - аналоговые входы/выходы.',2.5)
    s.t(28,360,'A1:ETH - W5 - A2:ETH: Ethernet. Питание и общие выводы: /3.1.',2.5)
    finish(s)

    s=sheet(3)
    s.t(42,72,'+24 В',3.5,True);s.t(322,72,'0 В',3.5,True)
    for x,net,src in [(42,'+24','CAB1.G1:+V'),(322,'0V','CAB1.G1:-V')]:
        targets=[c['to'] for c in d['connections'] if c['from']==src]
        s.t(x,86,src+' /1.1',2.5);s.ln(x+8,100,x+8,100+14*(len(targets)-1))
        for j,pid in enumerate(targets):
            y=100+j*14;s.dot(x+8,y);wire(s,(x+8,y),(x+165,y),net);s.t(x+170,y+1,pid,2.5)
    s.heading(28,252,'3.2  Контакт K1 и клапан',280)
    s.link(40,286,'+24',page='1.1',length=55)
    wire(s,(95,286),(128,286),'+24');s.contact(140,286,'K1',pins=('11','14'),ref='/2.1')
    wire(s,(152,286),(220,286),'40');s.term(220,286,'XT5:1')
    wire(s,(220,286),(318,286),'W3/1');s.rect(318,267,64,47,.35);s.t(350,280,'YV1',3,True,'center')
    s.pin(318,286,'FIELD.YV1:+','40','+');s.t(326,306,'-: W3/2, XT5:2, 0V',2.5)
    s.table(405,266,[75,85],['Кабель','Питание'],[['W2/1','+24'],['W2/4','0V'],['W4/1','+24'],['W4/3','0V']],rh=9)
    s.paragraph(28,336,'SB2 - обычная кнопка остановки. Схемы аварийного останова и функций безопасности в этот учебный пример не входят. Для реального оборудования требуется отдельное решение по его документации.',530)
    finish(s)

    s=sheet(4,style='rectangle');rows=[]
    for t in d['terminals']:
        pid=t['id'];cs=[c for c in d['connections'] if pid in (c['from'],c['to'])]
        local=[];external=[]
        for c in cs:
            peer=c['to'] if c['from']==pid else c['from']
            if c['scope']=='internal':local.append(peer)
            else:external.append(c['cable']+'/'+c['core']+' -> '+peer)
        rows.append([t['cabinet'],t['group'],t['number'],'Резерв' if t['spare'] else ports[pid].get('net',''),', '.join(local),', '.join(external)])
    tw=[37,28,20,35,175,244];th=['Шкаф','Группа','№','Цепь','Внутренний соседний конец','Внешний кабель/жила и соседний конец']
    s.table(28,62,tw,th,rows,rh=11)
    views.append({'kind':'terminals','ids':[t['id'] for t in d['terminals']]})
    finish(s)

    s=sheet(5);cab=d['cabinets'][0];scale=d['mounting_view']['scale'];x,y=52,71;w,h=cab['panel_mm']
    ox,oy=cab['panel_origin_mm'];cw,ch,_=cab['enclosure_mm']
    s.rect(x-ox/scale,y-oy/scale,cw/scale,ch/scale,.3,'MECHANICAL',True)
    s.rect(x,y,w/scale,h/scale,.5,'MECHANICAL');dimensions(s,x,y,w,h,scale)
    for v in d['mechanical']:
        if v['cabinet']!='CAB1':continue
        if v['kind']=='duct':
            a,b,c,e=v['bbox_mm'];s.rect(x+a/scale,y+b/scale,(c-a)/scale,(e-b)/scale,.3,'MECHANICAL')
        else:
            rx=x+v['x_mm']/scale;ry=y+v['y_mm']/scale;length=v['length_mm']/scale
            s.rect(rx,ry-35/scale/2,length,35/scale,.25,'MECHANICAL');s.ln(rx,ry,rx+length,ry,.15,'MECHANICAL',True)
    placed=[]
    for p in d['placements']:
        if p['cabinet']!='CAB1' or p['surface']!='panel':continue
        a,b,c,e=p['bbox_mm'];s.rect(x+a/scale,y+b/scale,(c-a)/scale,(e-b)/scale,.35,'SYMBOL')
        tag=p['device'].split('.')[1];s.t(x+(a+c)/2/scale,y+(b+e)/2/scale+1,tag,2.5,a='center')
        placed.append(p['device'])
    rows=[]
    for p in d['placements']:
        if p['device'] not in placed:continue
        a,b,c,e=p['bbox_mm'];rows.append([p['device'].split('.')[1],str(a),str(b),f'{c-a}×{e-b}',p.get('rail','Панель')])
    s.table(283,72,[38,33,33,65,95],['Аппарат','X, мм','Y, мм','Габарит, мм','Крепление'],rows,rh=11)
    dims=f'Корпус {ch}×{cw}×{cab["enclosure_mm"][2]} мм; панель {h}×{w} мм.'
    s.t(283,239,dims,2.5);s.t(283,250,f'Вид спереди. Масштаб 1:{scale}.',2.5)
    s.paragraph(283,262,d['mounting_view']['coordinate_origin'],175)
    duct_axes=[(v['bbox_mm'][1]+v['bbox_mm'][3])/2 for v in d['mechanical'] if v['kind']=='duct' and v['id'].startswith('D') and not v['id'].startswith('DV')]
    rail_axes=[v['y_mm'] for v in d['mechanical'] if v['kind']=='rail']
    s.paragraph(283,286,'Оси горизонтальных коробов: '+', '.join(f'{v:g}' for v in duct_axes)+' мм. Оси реек: '+', '.join(f'{v:g}' for v in rail_axes)+' мм.',175)
    s.paragraph(283,350,'Учебная раскладка. Габариты не определяют сверление; DXF содержит миллиметры бумаги.',260)
    views.append({'kind':'mounting','cabinet':'CAB1','enclosure_mm':cab['enclosure_mm'],'panel_mm':[w,h],'placements':placed,'page':5,'dimension_text':dims,
                  'scale':scale,'panel_paper_bbox':[x,y,x+w/scale,y+h/scale]})
    cab2=d['cabinets'][1];x2,y2,k2=487,267,8;w2,h2=cab2['panel_mm'];placed2=[]
    s.t(487,246,'CAB2',3,True);s.rect(x2,y2,w2/k2,h2/k2,.35,'MECHANICAL');dimensions(s,x2,y2,w2,h2,k2)
    for p in d['placements']:
        if p['cabinet']=='CAB2' and p['surface']=='panel':
            a,b,c,e=p['bbox_mm'];s.rect(x2+a/k2,y2+b/k2,(c-a)/k2,(e-b)/k2,.35)
            s.t(x2+(a+c)/2/k2,y2+(b+e)/2/k2+1,p['device'].split('.')[1],2.5,a='center');placed2.append(p['device'])
    s.t(487,344,'Масштаб 1:8',2.5)
    dims2=f'Панель CAB2: {h2}×{w2} мм.';s.t(283,377,dims2,2.5)
    views.append({'kind':'mounting','cabinet':'CAB2','enclosure_mm':cab2['enclosure_mm'],'panel_mm':[w2,h2],'placements':placed2,'page':5,
                  'dimension_text':dims2,'scale':k2,'panel_paper_bbox':[x2,y2,x2+w2/k2,y2+h2/k2]})
    finish(s)

    s=sheet(6,size='A3');cab=d['cabinets'][1];scale=3;x,y=60,75;w,h=cab['door_mm']
    s.rect(x,y,w/scale,h/scale,.5,'MECHANICAL');dimensions(s,x,y,w,h,scale)
    placed=[]
    for p in d['placements']:
        if p['cabinet']!='CAB2' or p['surface']!='door':continue
        a,b,c,e=p['bbox_mm'];tag=p['device'].split('.')[1]
        if tag=='A2':s.rect(x+a/scale,y+b/scale,(c-a)/scale,(e-b)/scale,.35)
        else:s.circle(x+(a+c)/2/scale,y+(b+e)/2/scale,(c-a)/2/scale)
        s.t(x+(a+c)/2/scale,y+e/scale+6,tag,2.5,a='center');placed.append(p['device'])
    for cut in d['door_cutouts']:
        a,b,c,e=cut['bbox_mm'];s.rect(x+a/scale,y+b/scale,(c-a)/scale,(e-b)/scale,.25,'MECHANICAL',True)
    rows=[]
    for p in d['placements']:
        if p['device'] not in placed:continue
        a,b,c,e=p['bbox_mm'];rows.append([p['device'].split('.')[1],str((a+c)/2),str((b+e)/2),f'{c-a}×{e-b}'])
    s.table(244,75,[32,32,32,59],['Аппарат','Xц','Yц','Габарит'],rows,rh=13)
    cut=d['door_cutouts'][0]['bbox_mm'];cutw,cuth=cut[2]-cut[0],cut[3]-cut[1]
    s.lines(244,161,[f'Дверь {h}×{w} мм.',f'Масштаб 1:{scale}.',f'A2: вырез {cutw}×{cuth} мм.','HL1 над A2; SB2 внизу.'],2.5,9)
    s.paragraph(244,209,'Xц, Yц - координаты центра от левого верхнего угла двери, мм. SB2 - обычный останов, без заявления о функции безопасности.',153)
    views.append({'kind':'door','cabinet':'CAB2','door_mm':[w,h],'placements':placed})
    finish(s)

    s=sheet(7);rows=[]
    for b in d['bom']:
        title=b['title']
        cab=next((c for c in d['cabinets'] if c['part']==b['part']),None)
        if cab:
            cw,ch,cd=cab['enclosure_mm'];pw,ph=cab['panel_mm'];title+=f' {ch}×{cw}×{cd}; панель {ph}×{pw}'
        members=', '.join(m['id'] for m in b['members'])
        rows.append([b['part'],title,members,str(b['installed_qty']),str(b['spare_qty']),str(b['stock_qty']),str(b['purchase_qty']),b['unit']])
    bw=[52,140,155,35,30,36,45,46];bh=['Артикул','Наименование','Позиции','Устан.','Запас','Наличие','Поставка','Ед.']
    s.table(28,62,bw,bh,rows,rh=11)
    views.append({'kind':'bom','rows':d['bom'],'cabinets':[{k:c[k] for k in ('id','enclosure_mm','panel_mm')} for c in d['cabinets']],
                  'page':7,'table_text':table_proof(s,28,62,bw,bh,rows)})
    finish(s)

    connections=[]
    for start,n in [(0,8),(30,9)]:
        s=sheet(n);rows=[];subset=d['connections'][start:start+30]
        for c in subset:
            section=str(c.get('section_mm2',''))
            cable=(c.get('cable','')+'/'+c.get('core','')).strip('/')
            rows.append([c['id'],c['net'],c['from'],c['to'],section,c.get('color',''),c.get('cabinet','Внешний'),cable])
        ww=[24,33,127,127,40,75,54,59];wh=['№ записи','Цепь','Откуда','Куда','мм²','Цвет','Шкаф','Кабель/жила']
        s.table(28,62,ww,wh,rows,rh=9)
        views.append({'kind':'connection_text','page':n,'table_text':table_proof(s,28,62,ww,wh,rows)})
        if n==9:s.t(28,365,'Интерфейс: W5; CAB1.A1:ETH -> CAB2.A2:ETH; Ethernet.',2.5)
        connections.extend(subset);finish(s)
    views.append({'kind':'connections','rows':connections,'interfaces':d['interfaces']})
    document=fitz.open()
    for p in pdfs:
        with fitz.open(p) as src:document.insert_pdf(src)
    document.set_metadata({'title':d['project']['name']+' Учебные схемы','author':'','subject':'Согласованный вымышленный пример оформления'})
    document.save(out/'demo.pdf');document.close();files.append('demo.pdf')
    release={'schema_version':1,'model_sha256':hashlib.sha256(raw).hexdigest(),'views':views,
             'artifacts':[{'file':fn,'sha256':hashlib.sha256((out/fn).read_bytes()).hexdigest()} for fn in files]}
    (out/'release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'out':str(out),'pages':total,'connections':len(connections)},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--model',type=Path,default=ROOT/'assets/demo/project.json');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();build(a.model,a.out)
if __name__=='__main__':main()
