#!/usr/bin/env python3
"""Create local technical input packages only; never campaign/oracle data.

Usage: ../P2a/.venv/bin/python prepare_technical_packages.py NEW_OUTPUT_DIRECTORY
Prior P2b mutable build/manifests must be archived by the operator before build.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('binding', ROOT.parent / 'P2b/p2b_binding.py')
assert spec is not None and spec.loader is not None
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    b.build()
    fixtures = []
    for track in ('posting', 'interest', 'reporting'):
        wd = out / track
        wd.mkdir()
        if track == 'posting':
            seeds = {'TRANFILE': b'', 'TCATBALF': b'', 'ACCTFILE': b.account(),
                     'XREFFILE': b'0000000000000001' + b'000000001' + b'00000000001' + b' ' * 14}
            for dd, data in seeds.items():
                raw = wd / (dd + '.seed')
                raw.write_bytes(data)
                b.io_file(wd, dd, 'LOAD', raw)
            (wd / 'DALYTRAN').write_bytes(b.transaction())
            provenance = {'source': 'existing binding synthetic constructors and RAWIO', 'bindingSha256': b.sha256(ROOT.parent / "P2b/p2b_binding.py")}
        elif track == 'interest':
            b.run_cmd([b.BUILD / 'intcalc_fixture'], cwd=wd)
            (wd / 'PARMFILE').write_bytes(b'2022071800')  # explicit technical fixture, not API default
            provenance = {'source': 'existing technical seed executable, not expected outcomes',
                          'generatorSha256': b.sha256(b.BUILD / 'intcalc_fixture'),
                          'driverSha256': b.sha256(b.BUILD / 'CBACT04C_driver'),
                          'driverParameter': '2022071800',
                          'parameterLimitation': 'fixed technical support driver; not a public default or parameterization proof'}
        else:
            b.run_cmd([b.BUILD / 'report_fixture'], cwd=wd)
            source = b.RUNS / 'reporting-tkb0lzyk'
            sources = []
            for name in ('TRANFILE', 'DATEPARM'):
                shutil.copy2(source / name, wd / name)
                sources.append({'path': str(source / name), 'sha256': b.sha256(source / name)})
            provenance = {'source': 'prior technical smoke INPUT resources, not expected outputs', 'files': sources,
                          'lookupGeneratorSha256': b.sha256(b.BUILD / 'report_fixture'),
                          'selection': 'exact prior technical input sequence; no upstream SORT/JCL execution claim'}
        files = {dd: f'{track}/{dd}' for dd in sorted(b.RESOURCE_NAMES[track])}
        pins = {dd: {'sha256': b.sha256(out / rel), 'bytes': (out / rel).stat().st_size} for dd, rel in files.items()}
        fx = {'fixtureId': f'{track}-native-technical-v2', 'track': track,
              'materializer': {'kind': 'local_file_package', 'files': files, 'filePins': pins},
              'provenance': {'class': 'local_synthetic_support', 'officialFixture': False, **provenance},
              'exposure': {'label': 'technical-only', 'notOracle': True, 'notExtractionInput': True, 'notPublicRequest': True},
              'reset': {'default': 'fresh_dir_per_run', 'statefulSequence': 'not_used'}}
        fx['contentSha256'] = b.fixture_descriptor_sha256(fx)
        fixtures.append(fx)
    registry = out / 'registry.json'
    registry.write_text(json.dumps({'kind': 'p3-local-technical-fixture-selection', 'status': 'technical_local_only', 'fixtures': fixtures}, indent=2) + '\n')
    print(registry)


if __name__ == '__main__':
    main()
