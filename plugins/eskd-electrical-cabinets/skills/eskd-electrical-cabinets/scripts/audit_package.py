#!/usr/bin/env python3
"""Inspect filenames, text and PDF metadata for explicitly supplied forbidden patterns."""
import argparse,json,re
from pathlib import Path
import fitz

def audit(root,pattern):
    errors=[];count=0;rx=re.compile(pattern,re.I) if pattern else None
    if not rx:return {'passed':False,'errors':['Explicit forbidden-pattern list required'],'checked_files':0}
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        rel=str(p.relative_to(root));count+=1
        if '.git' in p.parts or '__pycache__' in p.parts or p.suffix in ('.pyc','.zip','.7z'):
            errors.append({'file':rel,'reason':'Cache/history/archive requires removal or separate inspection'});continue
        if rx.search(rel):errors.append({'file':rel,'reason':'Forbidden filename'})
        if p.suffix=='.ttf':continue
        if p.suffix=='.pdf':
            with fitz.open(p) as doc:text=json.dumps(doc.metadata,ensure_ascii=False)+'\n'+'\n'.join(page.get_text() for page in doc)
        else:
            try:text=p.read_text(encoding='utf-8')
            except UnicodeDecodeError:errors.append({'file':rel,'reason':'Uninspected binary'});continue
        if rx.search(text):errors.append({'file':rel,'reason':'Forbidden content or metadata'})
    return {'passed':not errors,'checked_files':count,'errors':errors,
            'limitations':['Checks supplied patterns; visual content and unlisted identities need separate review.','Run on a clean export, not the parent Git repository.']}
def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('root',type=Path);a.add_argument('--forbidden',required=True);p=a.parse_args()
    r=audit(p.root,p.forbidden);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed'] else 2)
if __name__=='__main__':main()
