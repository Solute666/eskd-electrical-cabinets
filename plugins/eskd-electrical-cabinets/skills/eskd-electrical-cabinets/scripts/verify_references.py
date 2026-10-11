#!/usr/bin/env python3
"""Verify the frozen reference files, NOT their engineering correctness."""
import hashlib,json
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((root/'assets/reference-manifest.json').read_text(encoding='utf-8'))
    errors=[]
    for row in manifest['files']:
        p=root/row['file']
        if not p.is_file(): errors.append('Missing '+row['file'])
        elif hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            errors.append('Changed '+row['file'])
    print(json.dumps({'checked_files':len(manifest['files']), 'errors':errors,
                      'engineering_validation':False},ensure_ascii=False,indent=2))
    raise SystemExit(2 if errors else 0)

if __name__=='__main__': main()
