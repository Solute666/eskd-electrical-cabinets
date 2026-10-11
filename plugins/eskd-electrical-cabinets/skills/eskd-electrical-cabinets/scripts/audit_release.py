#!/usr/bin/env python3
"""Check the export adapter's release.json against the current model and actual files."""
import argparse,hashlib,json
from pathlib import Path
import fitz
from audit_project import audit as model_audit
from audit_assembly import audit as assembly_audit
from audit_layout import audit as layout_audit

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normalized(s):return ' '.join(str(s).split())

def audit(model,bundle):
    d=json.loads(model.read_text(encoding='utf-8'));errors=[];coverage={}
    for prefix,fn in [('model',model_audit),('assembly',assembly_audit)]:
        r=fn(d);errors.extend(prefix+': '+str(e) for e in r['errors']);coverage[prefix]=r['coverage']
    manifest=bundle/'release.json'
    if not manifest.is_file():return {'passed_within_scope':False,'errors':errors+['Missing release.json'],'coverage':coverage}
    r=json.loads(manifest.read_text(encoding='utf-8'))
    if r.get('model_sha256')!=digest(model):errors.append('Release was not built from the current model')
    artifacts=r.get('artifacts',[]);views=r.get('views',[])
    if not artifacts:errors.append('No exported artifacts')
    paths=set();pdfs={};layout_count=0;dxf_count=0
    for a in artifacts:
        rel=a.get('file','');p=(bundle/rel).resolve()
        if not rel or p==bundle.resolve() or bundle.resolve() not in p.parents:errors.append('Unsafe artifact path');continue
        if rel in paths:errors.append('Duplicate artifact '+rel)
        paths.add(rel)
        if not p.is_file():errors.append('Missing artifact '+rel);continue
        if a.get('sha256')!=digest(p):errors.append('Changed artifact '+rel)
        if p.suffix=='.pdf':pdfs[rel]=p
        if rel.endswith('_layout.json'):
            qa=layout_audit(json.loads(p.read_text(encoding='utf-8')));layout_count+=1
            errors.extend(rel+': '+str(e) for e in qa['errors']+qa['candidates'])
        if p.suffix=='.dxf':
            import ezdxf
            drawing=ezdxf.readfile(p);q=drawing.audit();dxf_count+=1
            if q.errors or q.fixes:errors.append('Invalid/repaired DXF '+rel)
            if drawing.units!=4:errors.append('DXF not in declared millimetres '+rel)
    n=len(d.get('sheets',[]))
    coverage.update(artifacts=len(paths),layout_files=layout_count,dxf_files=dxf_count)
    if layout_count!=n or dxf_count!=n:errors.append('Missing sheet exports/geometry coverage')
    if 'demo.pdf' in pdfs:
        with fitz.open(pdfs['demo.pdf']) as doc:
            if len(doc)!=n:errors.append('Combined PDF page count differs from model')
    cabs={x['id']:x for x in d.get('cabinets',[])}
    def require(kind):
        v=[x for x in views if x.get('kind')==kind]
        if len(v)!=1:errors.append(f'{kind}: exactly one release view required');return None
        return v[0]
    v=require('connections')
    if v and (v.get('rows')!=d.get('connections') or v.get('interfaces')!=d.get('interfaces',[])):errors.append('Exported connections/interfaces differ from model')
    v=require('terminals')
    if v and v.get('ids')!=[x['id'] for x in d.get('terminals',[])]:errors.append('Exported terminal overview differs from model')
    v=require('bom')
    if v:
        if v.get('rows')!=d.get('bom'):errors.append('Exported BOM differs from model')
        if v.get('cabinets')!=[{k:c[k] for k in ('id','enclosure_mm','panel_mm')} for c in d.get('cabinets',[])]:errors.append('BOM enclosure/panel dimensions differ from model')
        if len(v.get('table_text',[]))!=len(d.get('bom',[])):errors.append('No complete BOM table evidence')
    mount_views=[v for v in views if v.get('kind') in ('mounting','door')]
    expected_placements={p['device'] for p in d.get('placements',[])};observed=[]
    for v in mount_views:
        c=cabs.get(v.get('cabinet'))
        if not c:errors.append('Unknown release-view cabinet');continue
        observed.extend(v.get('placements',[]))
        if v['kind']=='mounting':
            if v.get('enclosure_mm')!=c['enclosure_mm'] or v.get('panel_mm')!=c['panel_mm']:errors.append('Mounting enclosure/panel dimensions differ from model')
            scale=v.get('scale');b=v.get('panel_paper_bbox',[])
            if not isinstance(scale,(int,float)) or scale<=0 or len(b)!=4 or any(abs((b[i+2]-b[i])*scale-c['panel_mm'][i])>1e-5 for i in range(2)):errors.append('Drawn panel scale/dimensions differ from model')
        elif v.get('door_mm')!=c['door_mm']:errors.append('Door dimensions differ from model')
    if set(observed)!=expected_placements or len(observed)!=len(expected_placements):errors.append('Exported placements incomplete or duplicated')
    # Read cells back from the final PDF. An adapter's semantic snapshot alone is insufficient.
    text_rows=0
    for v in views:
        if not v.get('table_text') and not v.get('dimension_text'):continue
        fn=f'sheet_{v.get("page",0):02d}.pdf'
        if fn not in pdfs:errors.append('Missing evidence PDF '+fn);continue
        with fitz.open(pdfs[fn]) as doc:
            page=doc[0]
            if v.get('dimension_text') and normalized(v['dimension_text']) not in normalized(page.get_text()):errors.append('Dimension annotation differs in actual PDF '+fn)
            for row in v.get('table_text',[]):
                values=row.get('values',[]);boxes=row.get('boxes_mm',[])
                if not values or len(values)!=len(boxes):errors.append('Missing PDF cell coordinates '+fn);continue
                for value,box in zip(values,boxes):
                    rect=fitz.Rect(*(x*72/25.4 for x in box))
                    actual=page.get_textbox(rect)
                    if normalized(actual)!=normalized(value):errors.append(f'{fn}: actual table cell differs: {value!r} / {actual!r}')
                text_rows+=1
    coverage['readback_table_rows']=text_rows
    expected_rows=len(d.get('connections',[]))+len(d.get('bom',[]))
    if text_rows!=expected_rows:errors.append('Incomplete PDF table readback')
    return {'passed_within_scope':not errors,'coverage':coverage,'errors':errors,
            'limitations':['Checks explicit adapter evidence and exported cells, not electrical calculations or manufacturer compliance.','Manual visual review of every changed sheet remains required.']}

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('model',type=Path);a.add_argument('--bundle',type=Path,required=True);a.add_argument('--report',type=Path);p=a.parse_args()
    r=audit(p.model,p.bundle)
    if p.report:p.report.parent.mkdir(parents=True,exist_ok=True);p.report.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed_within_scope'] else 2)
if __name__=='__main__':main()
