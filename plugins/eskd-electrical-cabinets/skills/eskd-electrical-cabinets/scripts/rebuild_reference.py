#!/usr/bin/env python3
"""Rebuild a selected frozen X2002 source in an isolated output directory."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from compare_pdf import compare


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--part', choices=['electrical', 'mounting'], required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    ref = root / 'assets/x2002-reference'
    out = args.out.resolve()
    if out == root or root in out.parents:
        ap.error('Write to a separate working directory, not inside the skill')
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        ap.error('Choose an empty output directory to avoid overwriting existing work')
    if args.part == 'electrical':
        archive = 'X2002_ШС1_Э3_Р27_Исходники.zip'
        project = out / 'X2002_R27'
        command = 'build.py'
        filename = 'X2002_ШС1_Э3_Р27_Комплект.pdf'
    else:
        archive = 'X2002_Монтаж_Р31_Исходники.zip'
        project = out / 'X2002_Монтаж_Р31'
        command = 'build_r31.py'
        filename = 'X2002_ШС1_Монтажная_схема_Р31.pdf'
    with ZipFile(ref / 'sources' / archive) as source:
        for name in source.namelist():
            dest = (out / name).resolve()
            if out not in dest.parents:
                raise ValueError('Unsafe archive member: ' + name)
        source.extractall(out)
    result = subprocess.run([sys.executable, command], cwd=project, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / 'build.log').write_text(result.stdout)
    if result.returncode:
        print(json.dumps({'build_returncode':result.returncode,'log':str(out/'build.log')}))
        raise SystemExit(result.returncode)
    report = compare(ref/'documents'/filename, project/'output'/filename, [])
    report['scope'] = ('Rebuilt electrical pages compared by text, page size and rendering.'
        if args.part == 'electrical' else
        'Page 1 rebuilt; pages 2–12 retained by the original source. All 12 pages compared.')
    (out / 'reproduction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'part':args.part,'errors':report['errors'],'report':str(out/'reproduction.json')},ensure_ascii=False))
    raise SystemExit(2 if report['errors'] else 0)


if __name__ == '__main__':
    main()
