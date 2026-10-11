#!/usr/bin/env python3
"""Check explicit connection data; never claim electrical safety or full design validation."""
import argparse,json,re
from collections import Counter,defaultdict
from pathlib import Path

def natural(value):
    return tuple((1,int(s)) if s.isdigit() else (0,s) for s in re.split(r'(\d+)',value))

def audit(data):
    errors=[]; notes=[];coverage={}
    tables={}
    required=('sheets','devices','ports','connections')
    for name in required+('terminals','cables','references','wire_labels'):
        rows=data.get(name,[])
        if not isinstance(rows,list):
            errors.append(f'{name}: expected array');rows=[]
        tables[name]=rows;coverage[name]=len(rows)
        if name in required and not rows:errors.append(f'{name}: no data to check')
    def index(name):
        result={}
        for n,r in enumerate(tables[name]):
            ident=r.get('id')
            if not ident: errors.append(f'{name}[{n}]: missing id')
            elif ident in result: errors.append(f'{name}: duplicate id {ident}')
            else:result[ident]=r
        return result
    sheets=index('sheets');devices=index('devices');ports=index('ports')
    connections=index('connections');terminals=index('terminals');cables=index('cables')
    if not isinstance(data.get('project'),dict) or not data['project'].get('name'):
        errors.append('Missing project.name')
    sections=set()
    for s in sheets.values():
        for z in s.get('sections',[]):
            if not re.fullmatch(r'\d+\.\d+',z):errors.append(f'Invalid section {z}')
            if z in sections:errors.append(f'Duplicate section {z}')
            sections.add(z)
    if not sections:errors.append('No declared sheet sections')
    positions=set();port_nets=defaultdict(set)
    for p in ports.values():
        if p.get('device') not in devices:errors.append(f"{p['id']}: unknown device")
        if not p.get('factory_label'):errors.append(f"{p['id']}: missing factory_label")
        if all(k in p for k in ('device','side','order')):
            pos=(p['device'],p['side'],p['order'])
            if pos in positions:errors.append(f'Duplicate physical position {pos}')
            positions.add(pos)
    for wire in connections.values():
        ident=wire['id']; net=str(wire.get('net',''))
        if not net:errors.append(f'{ident}: missing net')
        if wire.get('from')==wire.get('to'):errors.append(f'{ident}: identical ends')
        for endpoint in ('from','to'):
            pid=wire.get(endpoint)
            if pid not in ports:errors.append(f'{ident}: unknown {endpoint} {pid}')
            else:port_nets[pid].add(net)
        if wire.get('scope')=='internal':
            if not wire.get('cabinet'):errors.append(f'{ident}: missing cabinet')
            for field in ('section_mm2','color'):
                if wire.get(field) in (None,''):errors.append(f'{ident}: missing {field}')
            for endpoint in ('from','to'):
                device=devices.get(ports.get(wire.get(endpoint),{}).get('device'),{})
                if device.get('cabinet')!=wire.get('cabinet'):
                    errors.append(f'{ident}: internal wire crosses cabinet boundary')
        elif wire.get('scope')=='external':
            cid=wire.get('cable');core=str(wire.get('core',''))
            if cid not in cables:errors.append(f'{ident}: unknown cable {cid}')
            elif core not in [str(c['id']) for c in cables[cid].get('cores',[])]:
                errors.append(f'{ident}: cable core {core} not declared')
        else:errors.append(f'{ident}: scope must be internal or external')
    for pid,nets in port_nets.items():
        if len(nets)>1:errors.append(f'{pid}: conflicting nets {sorted(nets)}')
        declared=ports[pid].get('net')
        if declared is not None and nets!={str(declared)}:
            errors.append(f'{pid}: declared net differs from connections')
    for c in cables.values():
        ids=[str(x['id']) for x in c.get('cores',[])]
        if len(ids)!=len(set(ids)):errors.append(f"{c['id']}: duplicate core")
        used=Counter(str(w['core']) for w in connections.values() if w.get('cable')==c['id'])
        for core in c.get('cores',[]):
            count=used[str(core['id'])]
            if core.get('spare') and count:errors.append(f"{c['id']}:{core['id']}: reserve is connected")
            if not core.get('spare') and count!=1:
                errors.append(f"{c['id']}:{core['id']}: active core must have one end-to-end record")
    listed=set();order=defaultdict(list)
    for t in terminals.values():
        group=t.get('group');cab=t.get('cabinet')
        if not group or not cab:errors.append(f"{t['id']}: missing cabinet/group")
        if group not in order[cab]:order[cab].append(group)
        for pid in t.get('ports',[]):
            listed.add(pid)
            if pid not in ports:errors.append(f"{t['id']}: unknown terminal port {pid}")
            if t.get('spare') and pid in port_nets:errors.append(f"{t['id']}: spare terminal is connected")
    for pid,p in ports.items():
        if p.get('kind')=='terminal' and pid not in listed:
            errors.append(f'{pid}: terminal missing from overview')
    for cab,groups in order.items():
        xt=[g for g in groups if re.fullmatch(r'XT\d+',g or '')]
        if xt!=sorted(xt,key=natural):errors.append(f'{cab}: XT groups not in natural order')
    for r in tables['references']:
        for field in ('from','to'):
            if r.get(field) not in sections:errors.append(f'Unresolved reference {field}: {r.get(field)}')
        for field in ('source_port','destination_port'):
            if field in r:
                pid=r[field]
                if pid not in ports:errors.append(f'Unknown reference endpoint {pid}')
                elif str(r.get('net','')) not in port_nets.get(pid,{str(ports[pid].get('net'))}):
                    errors.append(f'Reference net mismatch at {pid}')
    labels=defaultdict(list)
    for lab in tables['wire_labels']:
        cid=lab.get('connection');labels[cid].append(lab)
        if cid not in connections:errors.append(f'Label refers to unknown connection {cid}');continue
        wire=connections[cid]
        if wire.get('scope')=='internal' and str(lab.get('text',''))!=str(wire.get('net')):
            errors.append(f'{cid}: wire label is not the local net')
        if lab.get('segment_from')!=wire.get('from') or lab.get('segment_to')!=wire.get('to'):
            errors.append(f'{cid}: label attached to a different segment')
    if data.get('require_wire_labels',False):
        for cid,w in connections.items():
            if w.get('scope')=='internal' and cid not in labels:
                errors.append(f'{cid}: no local wire label declared')
    if not tables['wire_labels']:notes.append('Placement of wire labels not checked: no annotations supplied')
    interface_ids=set();interfaces=data.get('interfaces',[])
    coverage['interfaces']=len(interfaces)
    for link in interfaces:
        ident=link.get('id')
        if not ident or ident in interface_ids or ident in cables:errors.append(f'Invalid/duplicate interface {ident}')
        interface_ids.add(ident)
        for endpoint in ('from','to'):
            if link.get(endpoint) not in ports:errors.append(f'{ident}: unknown interface {endpoint}')
        if link.get('from')==link.get('to'):errors.append(f'{ident}: identical interface ends')
        if not link.get('protocol'):errors.append(f'{ident}: missing interface protocol')
    notes.append('Use audit_assembly.py for declared BOM/dimensions; terminal ratings and safety require separate checks')
    return {'passed_within_scope':not errors,'scope':'Explicit model consistency only',
            'coverage':coverage,'errors':errors,'limitations':notes,'electrical_safety_validated':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('model',type=Path)
    ap.add_argument('--report',type=Path);a=ap.parse_args()
    result=audit(json.loads(a.model.read_text(encoding='utf-8')))
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['passed_within_scope'] else 2)

if __name__=='__main__':main()
