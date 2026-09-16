#!/usr/bin/env python3
import json, hashlib, sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
cat_path = Path(__file__).with_name('scenario-catalog.json')
cat = json.loads(cat_path.read_text(encoding='utf-8'))
errors=[]
def err(x): errors.append(x)
if cat.get('kind')!='aws-carddemo-complementary-validation-catalog': err('kind inválido')
if len(cat.get('obligations',[])) != 25: err('obrigações != 25')
if len(cat.get('contracts',[])) != 7: err('contratos != 7')
if len(cat.get('operations',[])) != 21: err('operações != 21')
if len(cat.get('obligationOperationMapping',[])) != 525: err('mapping != 525')
if len({o['id'] for o in cat['obligations']}) != 25: err('ids de obrigação duplicados')
if sum(c.get('operationCount',0) for c in cat['contracts']) != 21: err('soma operationCount != 21')
pairs={(m['obligationId'],m['contractId'],m['operationId']) for m in cat['obligationOperationMapping']}
if len(pairs)!=525: err('pares obrigação/contrato/operação duplicados ou ausentes')
source_base=Path(cat['sourceBase'])
if not source_base.is_dir(): err(f'sourceBase ausente: {source_base}')
for ob in cat['obligations']:
    if not ob.get('sourceAnchors'): err(f'obrigação sem anchors: {ob.get("id")}')
    for a in ob.get('sourceAnchors',[]):
        p=source_base/a['path']
        if not p.is_file(): err(f'anchor ausente {ob["id"]}: {a["path"]}'); continue
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        if h != a['sha256']: err(f'sha mismatch {a["path"]}: {h} != {a["sha256"]}')
        lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
        lo,hi=a['lines']
        if not (1 <= lo <= hi <= len(lines)): err(f'linhas inválidas {a["path"]}:{lo}-{hi}/{len(lines)}')
for sp in cat.get('sourcePins',[]):
    p=root/sp['path']
    if not p.is_file(): err(f'source pin ausente: {sp["path"]}'); continue
    if p.stat().st_size != sp['bytes']: err(f'bytes source pin mudou: {sp["path"]}')
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h != sp['sha256']: err(f'sha source pin mudou: {sp["path"]}')
pre=cat['denominators']['pre_execution_results']
if pre != {'achieved':0,'failed':0,'unobservable':525}: err(f'pré-execução inválido: {pre}')
print(json.dumps({'status':'FAIL' if errors else 'PASS','errors':errors,'checked':{'obligations':25,'contracts':7,'operations':21,'mappingCells':525,'sourceBase':str(source_base)}}, ensure_ascii=False, indent=2))
sys.exit(1 if errors else 0)
