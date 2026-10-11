#!/usr/bin/env python3
"""Find geometry conflicts in drawing.py layout JSON. Review candidates visually."""
import argparse,json
from pathlib import Path

def intersection(a,b):
    return min(a[2],b[2])-max(a[0],b[0]), min(a[3],b[3])-max(a[1],b[1])

def audit(data):
    width,height=data.get('format_mm',[0,0])
    out={'scope':'Recorded text bounding boxes and orthogonal wire segments',
         'errors':[], 'candidates':[], 'visual_review_required':True,
         'rotated_texts_not_collision_checked':data.get('rotated_text_count',0)}
    if not width or not height:
        out['errors'].append('Missing physical format_mm')
    texts=[t for t in data.get('texts',[]) if t.get('layer')!='FRAME' and t.get('text')]
    if not texts:out['errors'].append('No content text recorded')
    out['checked_texts']=len(texts)
    for i,t in enumerate(texts):
        a=t['bbox']
        if a[0]<20 or a[1]<5 or a[2]>width-5 or a[3]>height-5:
            out['errors'].append({'type':'bounds','text':t['text'],'bbox':a})
        for reserved in data.get('reserved_boxes',[]):
            dx,dy=intersection(a,reserved['bbox'])
            if dx>.2 and dy>.2:
                out['errors'].append({'type':'reserved','text':t['text'],'area':reserved['name']})
        for other in texts[i+1:]:
            dx,dy=intersection(a,other['bbox'])
            if dx>.6 and dy>.6:
                out['candidates'].append({'type':'text_overlap','a':t['text'],'b':other['text']})
        x0,y0,x1,y1=a[0]+.35,a[1]+.25,a[2]-.35,a[3]-.25
        for seg in data.get('lines',[]):
            x,y,u,v,layer=seg[:5]
            if layer not in ('WIRE','PE'):continue
            hit=(abs(y-v)<1e-6 and y0<y<y1 and min(x1,max(x,u))-max(x0,min(x,u))>.8)
            hit |= (abs(x-u)<1e-6 and x0<x<x1 and min(y1,max(y,v))-max(y0,min(y,v))>.8)
            if hit:
                out['candidates'].append({'type':'wire_text','text':t['text'],'segment':seg})
    out['recorded_lines']=len(data.get('lines',[]))
    out['clear_of_detected_conflicts']=not(out['errors'] or out['candidates'])
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('layout',type=Path)
    ap.add_argument('--report',type=Path);a=ap.parse_args()
    result=audit(json.loads(a.layout.read_text(encoding='utf-8')))
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['clear_of_detected_conflicts'] else 2)

if __name__=='__main__': main()
