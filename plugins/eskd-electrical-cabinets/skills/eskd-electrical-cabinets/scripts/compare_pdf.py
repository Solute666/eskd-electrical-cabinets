#!/usr/bin/env python3
"""Detect unintended changes on all PDF pages outside --allowed-pages."""
import argparse, hashlib, json
from pathlib import Path
import fitz

def compare(before, after, allowed=(), dpi=100):
    allowed = set(allowed)
    result = {'scope':'Unchanged page appearance, text and size only',
              'allowed_pages':sorted(allowed), 'checked_pages':[], 'errors':[]}
    with fitz.open(before) as a, fitz.open(after) as b:
        result['page_counts'] = [len(a), len(b)]
        if len(a) != len(b): result['errors'].append('Page count changed')
        for n in allowed:
            if n < 1 or n > min(len(a),len(b)):
                result['errors'].append(f'Allowed page outside both documents: {n}')
        for i in range(min(len(a),len(b))):
            if i+1 in allowed: continue
            pa,pb = a[i],b[i]
            detail = {'page':i+1,
                      'same_size':tuple(pa.rect)==tuple(pb.rect),
                      'same_text':pa.get_text()==pb.get_text()}
            xa,xb=pa.get_pixmap(dpi=dpi,alpha=False),pb.get_pixmap(dpi=dpi,alpha=False)
            detail['same_image'] = ((xa.width,xa.height)==(xb.width,xb.height) and
                 hashlib.sha256(xa.samples).digest()==hashlib.sha256(xb.samples).digest())
            result['checked_pages'].append(detail)
            if not all(detail[k] for k in ('same_size','same_text','same_image')):
                result['errors'].append(f'Unexpected change on page {i+1}')
    result['passed'] = not result['errors']
    result['changed_pages_validated'] = False
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('before',type=Path); ap.add_argument('after',type=Path)
    ap.add_argument('--allowed-pages',default='')
    ap.add_argument('--dpi',type=int,default=100)
    ap.add_argument('--report',type=Path)
    a=ap.parse_args()
    if not 36<=a.dpi<=300: ap.error('Use 36–300 dpi')
    allowed=[int(n) for n in a.allowed_pages.split(',') if n.strip()]
    result=compare(a.before,a.after,allowed,a.dpi)
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['passed'] else 2)

if __name__=='__main__': main()
