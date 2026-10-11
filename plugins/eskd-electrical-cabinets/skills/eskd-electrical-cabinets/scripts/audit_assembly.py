#!/usr/bin/env python3
"""Check declared enclosure, panel, placement and BOM consistency; no engineering ratings."""
import argparse,json,math
from collections import Counter
from pathlib import Path

def audit(data):
    errors=[];coverage={};indexes={}
    def number(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
    def rows(name,key='id'):
        a=data.get(name)
        if not isinstance(a,list) or not a:errors.append(f'{name}: no data to check');a=[]
        coverage[name]=len(a);idx={}
        for r in a:
            if not isinstance(r,dict) or not r.get(key):errors.append(f'{name}: missing {key}');continue
            ident=r[key]
            if ident in idx:errors.append(f'{name}: duplicate {ident}')
            idx[ident]=r
        indexes[name]=idx;return idx
    cabs=rows('cabinets');devices=rows('devices');bom=rows('bom','part')
    placements=data.get('placements',[]);mechanical=data.get('mechanical',[])
    coverage.update(placements=len(placements),mechanical=len(mechanical))
    if not placements:errors.append('placements: no dimensioned placements')
    def positive_dims(v,n):return isinstance(v,list) and len(v)==n and all(number(x) and x>0 for x in v)
    def box_ok(b):return isinstance(b,list) and len(b)==4 and all(number(x) for x in b) and b[2]>b[0] and b[3]>b[1]
    def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-6 and min(a[3],b[3])-max(a[1],b[1])>1e-6
    expected={};sources={}
    for cid,c in cabs.items():
        whd=c.get('enclosure_mm');panel=c.get('panel_mm');origin=c.get('panel_origin_mm')
        if not positive_dims(whd,3):errors.append(f'{cid}: invalid enclosure_mm');continue
        if not positive_dims(panel,2):errors.append(f'{cid}: invalid panel_mm');continue
        if not (isinstance(origin,list) and len(origin)==2 and all(number(x) and x>=0 for x in origin)):
            errors.append(f'{cid}: missing panel origin');continue
        if any(origin[i]+panel[i]>whd[i] for i in range(2)):errors.append(f'{cid}: panel outside enclosure')
        if c.get('door_mm')!=whd[:2]:errors.append(f'{cid}: door dimensions differ from enclosure face')
        if not c.get('source'):errors.append(f'{cid}: missing dimensional source')
        qty=c.get('quantity')
        if not number(qty) or qty<=0:errors.append(f'{cid}: invalid cabinet quantity');continue
        expected[cid]=(c.get('part'),qty)
    for ident,dev in devices.items():
        qty=dev.get('bom_quantity',1)
        if not number(qty) or qty<=0:errors.append(f'{ident}: invalid installed quantity');continue
        cab=dev.get('cabinet');factor=cabs.get(cab,{}).get('quantity',1)
        expected[ident]=(dev.get('part'),qty*factor)
    if data.get('bom_include_cables'):
        for cable in data.get('cables',[])+data.get('interfaces',[]):
            ident=cable.get('id');qty=cable.get('quantity')
            if not ident or ident in expected or not number(qty) or qty<=0:
                errors.append(f'{ident}: invalid cable BOM identity/quantity');continue
            expected[ident]=(cable.get('part'),qty)
        coverage['cables_in_bom']=len(data.get('cables',[]))+len(data.get('interfaces',[]))
    ids=set();valid=[]
    rails={v['id']:v for v in mechanical if isinstance(v,dict) and v.get('kind')=='rail' and v.get('id')}
    for p in placements:
        ident=p.get('device');cab=p.get('cabinet');surface=p.get('surface');b=p.get('bbox_mm')
        if ident in ids:errors.append(f'{ident}: duplicate placement')
        ids.add(ident)
        if ident not in devices:errors.append(f'{ident}: unknown placed device');continue
        if cab not in cabs or cab!=devices[ident].get('cabinet'):errors.append(f'{ident}: wrong cabinet');continue
        if surface not in ('panel','door') or not box_ok(b):errors.append(f'{ident}: invalid surface/bbox');continue
        dim=devices[ident].get('dimensions_mm')
        if not positive_dims(dim,2) or dim!=[b[2]-b[0],b[3]-b[1]]:errors.append(f'{ident}: footprint differs from device dimensions')
        extent=cabs[cab]['panel_mm' if surface=='panel' else 'door_mm']
        if b[0]<0 or b[1]<0 or b[2]>extent[0] or b[3]>extent[1]:errors.append(f'{ident}: outside {surface}')
        margin=p.get('clearance_mm')
        if not isinstance(margin,list) or len(margin)!=4 or not all(number(x) and x>=0 for x in margin):
            errors.append(f'{ident}: missing declared clearances');margin=[0]*4
        eb=[b[0]-margin[0],b[1]-margin[1],b[2]+margin[2],b[3]+margin[3]]
        if eb[0]<0 or eb[1]<0 or eb[2]>extent[0] or eb[3]>extent[1]:errors.append(f'{ident}: clearance outside {surface}')
        if not p.get('source'):errors.append(f'{ident}: missing mounting source')
        if p.get('rail'):
            r=rails.get(p['rail'])
            if not r or r.get('cabinet')!=cab:errors.append(f'{ident}: unknown rail')
            elif not (r['x_mm']<=b[0]<b[2]<=r['x_mm']+r['length_mm'] and b[1]<=r['y_mm']<=b[3]):errors.append(f'{ident}: not on declared rail')
        valid.append((p,b,eb))
    for i,(p,b,eb) in enumerate(valid):
        for q,c,ec in valid[i+1:]:
            if (p['cabinet'],p['surface'])==(q['cabinet'],q['surface']) and (overlap(eb,c) or overlap(b,ec)):
                errors.append(f'{p["device"]}/{q["device"]}: footprint or clearance collision')
        for duct in mechanical:
            if duct.get('kind')=='duct' and duct.get('cabinet')==p['cabinet'] and p['surface']=='panel' and box_ok(duct.get('bbox_mm')) and overlap(eb,duct['bbox_mm']):
                errors.append(f'{p["device"]}/{duct.get("id")}: duct collision')
    for v in mechanical:
        ident=v.get('id');cab=v.get('cabinet')
        if not ident or ident in expected:errors.append(f'mechanical: missing/duplicate id {ident}');continue
        if cab not in cabs:errors.append(f'{ident}: unknown cabinet');continue
        if v.get('kind')=='duct':b=v.get('bbox_mm')
        elif v.get('kind')=='rail':
            if not all(number(v.get(k)) for k in ('x_mm','y_mm','length_mm')) or v['length_mm']<=0:
                errors.append(f'{ident}: invalid rail');continue
            b=[v['x_mm'],v['y_mm']-1,v['x_mm']+v['length_mm'],v['y_mm']+1]
        else:errors.append(f'{ident}: unknown mechanical kind');continue
        if not box_ok(b):errors.append(f'{ident}: invalid mechanical bbox');continue
        w,h=cabs[cab]['panel_mm']
        if b[0]<0 or b[1]<0 or b[2]>w or b[3]>h:errors.append(f'{ident}: mechanical item outside panel')
        expected[ident]=(v.get('part'),cabs[cab]['quantity'])
    for cut in data.get('door_cutouts',[]):
        owner=next((p for p,b,e in valid if p['device']==cut.get('device') and p['surface']=='door'),None)
        b=cut.get('bbox_mm')
        if not owner or not box_ok(b):errors.append('Invalid or ownerless door cutout');continue
        a=owner['bbox_mm']
        if b[0]<a[0] or b[1]<a[1] or b[2]>a[2] or b[3]>a[3]:errors.append(f'{owner["device"]}: cutout outside bezel')
    members=Counter()
    for part,row in bom.items():
        installed=0
        for m in row.get('members',[]):
            ident=m.get('id');qty=m.get('quantity');members[ident]+=1
            if ident not in expected:errors.append(f'{part}: unknown BOM member {ident}');continue
            if expected[ident]!=(part,qty):errors.append(f'{part}: wrong article/quantity for {ident}')
            if number(qty):installed+=qty
            else:errors.append(f'{part}: non-numeric quantity')
        if installed!=row.get('installed_qty'):errors.append(f'{part}: installed quantity differs from members')
        nums=[row.get(k) for k in ('installed_qty','spare_qty','stock_qty','purchase_qty')]
        if not all(number(x) and x>=0 for x in nums):errors.append(f'{part}: invalid quantities')
        elif nums[3]!=max(0,nums[0]+nums[1]-nums[2]):errors.append(f'{part}: procurement arithmetic mismatch')
        if not row.get('unit'):errors.append(f'{part}: missing unit')
    for ident in expected:
        if members[ident]!=1:errors.append(f'{ident}: must occur exactly once in BOM')
    return {'passed_within_scope':not errors,'coverage':coverage,'errors':errors,
            'scope':'Declared dimensions, panel geometry and bill of materials',
            'limitations':['No verification of manufacturer data, thermal, strength, wiring capacity, depth or safety calculations.','Clearances are checked only against the explicitly supplied values.']}

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('model',type=Path);a.add_argument('--report',type=Path);p=a.parse_args()
    r=audit(json.loads(p.model.read_text(encoding='utf-8')))
    if p.report:p.report.parent.mkdir(parents=True,exist_ok=True);p.report.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed_within_scope'] else 2)
if __name__=='__main__':main()
