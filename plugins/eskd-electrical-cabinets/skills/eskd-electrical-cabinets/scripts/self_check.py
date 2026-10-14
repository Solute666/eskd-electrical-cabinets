#!/usr/bin/env python3
"""Regression checks for the reusable validators after editing this skill."""
import argparse,copy,json,shutil,tempfile
from pathlib import Path
from audit_project import audit
from audit_layout import audit as layout_audit
from audit_assembly import audit as assembly_audit
from audit_release import audit as release_audit

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--bundle',type=Path);args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    base=json.loads((root/'assets/templates/model-example.json').read_text(encoding='utf-8'))
    checks=[{'case':'valid_data','passed':audit(base)['passed_within_scope']},
            {'case':'empty_data_rejected','passed':not audit({})['passed_within_scope']}]
    def negative(name,change):
        model=copy.deepcopy(base);change(model)
        checks.append({'case':name,'passed':not audit(model)['passed_within_scope']})
    negative('unknown_pin',lambda d:d['connections'][2].update(to='CAB1.A1:UNKNOWN'))
    negative('label_before_local_terminal',lambda d:d['wire_labels'][1].update(segment_from='CAB2.XT1:1',segment_to='CAB1.XT1:1'))
    negative('external_disguised_as_local',lambda d:d['connections'][1].update(scope='internal',cabinet='CAB1',section_mm2=.75,color='red'))
    negative('terminal_missing_from_overview',lambda d:d['terminals'].pop())
    negative('nonexistent_reference',lambda d:d['references'].append({'from':'1.1','to':'9.9','net':'20'}))
    negative('connected_spare_core',lambda d:d['cables'][0]['cores'][0].update(spare=True))
    negative('duplicate_connection',lambda d:d['connections'].append(copy.deepcopy(d['connections'][0])))
    negative('different_nets_on_one_pin',lambda d:d['connections'][2].update(net='99'))
    negative('empty_connections',lambda d:d.update(connections=[]))
    geometry={'format_mm':[420,297], 'texts':[{'text':'20','bbox':[190,101,195,105],'layer':'TEXT'}],
              'lines':[[180,110,270,110,'WIRE']], 'reserved_boxes':[{'name':'stamp','bbox':[230,237,415,292]}]}
    checks.append({'case':'clear_geometry','passed':layout_audit(geometry)['clear_of_detected_conflicts']})
    geometry['texts'][0]['bbox']=[190,108,195,112]
    checks.append({'case':'wire_through_label','passed':not layout_audit(geometry)['clear_of_detected_conflicts']})
    geometry['texts'][0]['bbox']=[250,250,255,254]
    checks.append({'case':'text_in_stamp','passed':bool(layout_audit(geometry)['errors'])})
    demo_path=root/'scripts/test_fixtures/validator_project.json';demo=json.loads(demo_path.read_text(encoding='utf-8'))
    checks.append({'case':'complete_demo_model','passed':audit(demo)['passed_within_scope']})
    checks.append({'case':'complete_demo_assembly','passed':assembly_audit(demo)['passed_within_scope']})
    def bad_assembly(name,change):
        sample=copy.deepcopy(demo);change(sample)
        checks.append({'case':name,'passed':not assembly_audit(sample)['passed_within_scope']})
    bad_assembly('empty_assembly_rejected',lambda s:s.update(cabinets=[],bom=[],placements=[]))
    bad_assembly('panel_does_not_fit_changed_cabinet',lambda s:s['cabinets'][0].update(enclosure_mm=[800,1000,400]))
    bad_assembly('wrong_device_footprint',lambda s:s['devices'][0].update(dimensions_mm=[72,90]))
    bad_assembly('device_beyond_panel',lambda s:s['placements'][0].update(bbox_mm=[800,95,836,185]))
    bad_assembly('device_collision',lambda s:s['placements'][5].update(bbox_mm=[75,100,100,170]))
    bad_assembly('device_hits_duct',lambda s:s['placements'][0].update(bbox_mm=[75,25,111,115]))
    bad_assembly('missing_rail',lambda s:s['placements'][0].update(rail='unknown'))
    bad_assembly('wrong_BOM_total',lambda s:s['bom'][0].update(installed_qty=2))
    bad_assembly('wrong_procurement_total',lambda s:s['bom'][0].update(purchase_qty=2))
    bad_assembly('lost_BOM_member',lambda s:s['bom'][0].update(members=[]))
    bad_assembly('lost_cable_in_BOM',lambda s:s['bom'].pop())
    bad_assembly('door_cutout_outside_bezel',lambda s:s['door_cutouts'][0].update(bbox_mm=[80,100,298,248]))
    sample=copy.deepcopy(demo);sample['interfaces'][0]['to']='missing'
    checks.append({'case':'unknown_interface_port','passed':not audit(sample)['passed_within_scope']})
    if args.bundle:
        with tempfile.TemporaryDirectory(prefix='release-check-') as tmp:
            work=Path(tmp);bundle=work/'output';shutil.copytree(args.bundle,bundle)
            model=work/'project.json';shutil.copy2(demo_path,model)
            checks.append({'case':'actual_export_readback','passed':release_audit(model,bundle)['passed_within_scope']})
            changed=copy.deepcopy(demo);changed['cabinets'][0]['enclosure_mm'][1]=1400
            model.write_text(json.dumps(changed,ensure_ascii=False),encoding='utf-8')
            r=release_audit(model,bundle)
            checks.append({'case':'old_export_after_cabinet_change','passed':not r['passed_within_scope'] and any('Mounting enclosure' in e for e in r['errors'])})
            shutil.copy2(demo_path,model)
            release_path=bundle/'release.json';release=json.loads(release_path.read_text(encoding='utf-8'))
            next(v for v in release['views'] if v['kind']=='bom')['rows'][0]['purchase_qty']=999
            release_path.write_text(json.dumps(release,ensure_ascii=False),encoding='utf-8')
            r=release_audit(model,bundle)
            checks.append({'case':'mismatching_exported_BOM','passed':not r['passed_within_scope'] and 'Exported BOM differs from model' in r['errors']})
    print(json.dumps({'checks':checks,'passed':all(x['passed'] for x in checks)},ensure_ascii=False,indent=2))
    raise SystemExit(0 if all(x['passed'] for x in checks) else 2)

if __name__=='__main__':main()
