#!/usr/bin/env python3
"""Create an empty editable drawing workspace, without inheriting sample devices."""
import argparse,json,shutil
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('target',type=Path);ap.add_argument('--project',required=True)
    a=ap.parse_args();target=a.target.resolve();root=Path(__file__).resolve().parents[1]
    if target==root or root in target.parents:ap.error('Do not write a project into the installed skill')
    if target.exists() and any(target.iterdir()):ap.error('Target must be new or empty; existing files are preserved')
    for d in ('data','output','qa','scripts','assets/fonts'):(target/d).mkdir(parents=True,exist_ok=True)
    for name in ('drawing.py','audit_project.py','audit_layout.py','audit_assembly.py','audit_release.py','compare_pdf.py','render_reference.py'):
        shutil.copy2(root/'scripts'/name,target/'scripts'/name)
    for p in (root/'assets/fonts').iterdir():shutil.copy2(p,target/'assets/fonts'/p.name)
    model={'schema_version':2,'project':{'name':a.project},'sheets':[],
           'devices':[],'ports':[],'connections':[],'terminals':[],'cables':[],
           'references':[],'wire_labels':[],'require_wire_labels':True,'sheet_status':[],
           'cabinets':[],'placements':[],'mechanical':[],'bom':[],'door_cutouts':[],'interfaces':[]}
    (target/'data/project.json').write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'workspace':str(target),'status':'Empty data; not a validated design',
                      'next':'Fill data/project.json from actual sources; build with scripts/drawing.py'},ensure_ascii=False))

if __name__=='__main__':main()
