import importlib.util
import pathlib
import tempfile
import unittest
import json

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'p2b_binding.py'
VALIDATE = ROOT / 'validate_p2b.py'

class P2bContractTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location('p2b_binding', MODULE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_empty_object_policy(self):
        mod = self.load_module()
        self.assertEqual(mod.validate_request({}), None)
        self.assertEqual(mod.validate_request({'selector': 'x'}), 'request_representation')
        self.assertEqual(mod.validate_request(None), 'request_representation')

    def test_audit_skeleton_has_required_sections(self):
        mod = self.load_module()
        with tempfile.TemporaryDirectory() as td:
            audit = mod.new_audit('posting', pathlib.Path(td), 'unit')
            self.assertEqual(audit['INV']['track'], 'posting')
            for key in ['INV', 'RES', 'CAP', 'CONV', 'FAIL', 'STATE', 'RESP']:
                self.assertIn(key, audit)
            self.assertEqual(audit['INV']['request'], {})
            self.assertIn('technical smoke fixture', audit['RES']['fixture_policy'])

    def test_source_pins_include_full3track_programs(self):
        mod = self.load_module()
        pins = mod.load_expected_source_pins()
        self.assertEqual(set(pins['programs']), {'CBTRN02C', 'CBACT04C', 'CBTRN03C'})
        for rel in ['app/cbl/CBTRN02C.cbl', 'app/cbl/CBACT04C.cbl', 'app/cbl/CBTRN03C.cbl']:
            self.assertIn(rel, pins['files_by_path'])

    def test_reporting_detail_fields_follow_report_bytes_not_transaction_fixture_literals(self):
        mod = self.load_module()
        # Mutate every public report field away from known fixture/source-transaction literals.
        line = (
            b'RAWREPORTFIELD01' + b' ' +
            b'ACCTREPORT9' + b' ' +
            b'77' + b'-' +
            b'ReportOnlyDesc!' + b' ' +
            b'8888' + b'-' +
            b'Report category text bytes!!'.ljust(29) + b' ' +
            b'RPTSRC9999' + b'    ' +
            b'       321.09  '
        ).ljust(133, b' ')
        records, evidence = mod.parse_report_records(line)
        self.assertEqual(evidence['framing']['classification'], 'available')
        self.assertEqual(records, [{
            'kind': 'detail',
            'value': {
                'transactionId': 'RAWREPORTFIELD01',
                'accountReference': 'ACCTREPORT9',
                'typeCode': '77',
                'typeDescription': 'ReportOnlyDesc!',
                'categoryCode': '8888',
                'categoryDescription': 'Report category text bytes!!',
                'source': 'RPTSRC9999',
                'amountText': '321.09',
            },
        }])

    def test_reporting_preserves_order_multiplicity_and_classifies_unknown_lines(self):
        mod = self.load_module()
        header = (b'DALYREPT'.ljust(38) + b'Daily Transaction Report'.ljust(41) + b'Date Range: ' + b'2026-01-01' + b' to ' + b'2026-01-31').ljust(133, b' ')
        detail = (b'TXN0000000000001 00000000001 01-System transact 0005-Interest charge'.ljust(83) + b'System'.ljust(10) + b'    ' + b'        100.00  ').ljust(133, b' ')
        page_total = (b'Page Total'.ljust(11, b'.') + (b'.' * 86) + b'       +100.00').ljust(133, b' ')
        unknown = b'Transaction ID    Account ID  Transaction Type   Tran Category                      Tran Source          Amount'.ljust(133, b' ')
        records, evidence = mod.parse_report_records(header + detail + detail + page_total + unknown)
        self.assertEqual([r['kind'] for r in records], ['header', 'detail', 'detail', 'total'])
        self.assertEqual(records[0]['value']['startText'], '2026-01-01')
        self.assertEqual(records[3]['value'], {'label': 'page', 'valueText': '+100.00'})
        self.assertEqual(evidence['records'][4]['classification'], 'known_unmapped_header_row')
        self.assertIn('Transaction ID', evidence['records'][4]['rawText'])

    def test_unknown_meaningful_report_only_is_not_silent_available_empty_200(self):
        mod = self.load_module()
        unknown = b'MEANINGFUL BUSINESS RECORD THAT DOES NOT MATCH ANY KNOWN REPORT SHAPE'.ljust(133, b' ')
        records, evidence = mod.parse_report_records(unknown)
        self.assertEqual(records, [])
        self.assertEqual(evidence['records'][0]['classification'], 'unknown_unmapped')
        self.assertEqual(evidence['framing']['classification'], 'unmapped_meaningful')
        status, body = mod.status_for_capture_observation(
            'reporting',
            evidence['framing'],
            {'track': 'reporting', 'records': {'availability': 'available', 'items': records}},
        )
        self.assertEqual(status, 500)
        self.assertEqual(body['category'], 'technical_failure')
        self.assertNotEqual(body.get('records'), {'availability': 'available', 'items': []})

    def test_mixed_known_and_unknown_meaningful_report_returns_500_with_partial_content(self):
        mod = self.load_module()
        detail = (b'TXN0000000000001 00000000001 01-System transact 0005-Interest charge'.ljust(83) + b'System'.ljust(10) + b'    ' + b'        100.00  ').ljust(133, b' ')
        unknown = b'MEANINGFUL BUSINESS RECORD THAT DOES NOT MATCH ANY KNOWN REPORT SHAPE'.ljust(133, b' ')
        records, evidence = mod.parse_report_records(detail + unknown)
        self.assertEqual([ev['classification'] for ev in evidence['records']], ['detail', 'unknown_unmapped'])
        self.assertEqual(evidence['framing']['classification'], 'unmapped_meaningful')
        status, body = mod.status_for_capture_observation(
            'reporting',
            evidence['framing'],
            {'track': 'reporting', 'completeness': 'not_attested', 'durability': 'unknown', 'records': {'availability': 'available', 'items': records}},
        )
        self.assertEqual(status, 500)
        self.assertEqual(body['category'], 'technical_failure')
        self.assertEqual(body['availableContent']['records']['items'], records)

    def test_missing_truncated_malformed_empty_capture_status_mapping_all_tracks(self):
        mod = self.load_module()
        for track, size in [('posting', 350), ('interest', 350), ('reporting', 133)]:
            missing = mod.fixed_capture_status(track, None, size)
            self.assertEqual(missing['classification'], 'missing')
            self.assertEqual(mod.status_for_capture_observation(track, missing)[0], 503)

            empty = mod.fixed_capture_status(track, b'', size)
            self.assertEqual(empty['classification'], 'known_empty')
            status, body = mod.status_for_capture_observation(track, empty)
            self.assertEqual(status, 200)
            field = 'records' if track == 'reporting' else 'outputs'
            self.assertEqual(body[field], {'availability': 'available', 'items': []})

            truncated = mod.fixed_capture_status(track, b'X' * (size - 1), size)
            self.assertEqual(truncated['classification'], 'truncated')
            status, body = mod.status_for_capture_observation(track, truncated)
            self.assertEqual(status, 500)
            self.assertEqual(body['category'], 'technical_failure')

            malformed = mod.fixed_capture_status(track, b'\xff' * size, size)
            self.assertEqual(malformed['classification'], 'malformed')
            status, body = mod.status_for_capture_observation(track, malformed)
            self.assertEqual(status, 500)
            self.assertEqual(body['category'], 'technical_failure')

    def test_posting_interest_transaction_parser_requires_350_and_preserves_multiple_order(self):
        mod = self.load_module()
        one = mod.transaction(card=b'0000000000000001', amount=b'00000002500')
        two = mod.transaction(card=b'0000000000000002', amount=b'00000003000')
        items, evidence = mod.parse_transaction_records(one + two, 'posting')
        self.assertEqual(evidence['framing']['recordSize'], 350)
        self.assertEqual([i['cardReference'] for i in items], ['0000000000000001', '0000000000000002'])
        self.assertEqual([i['amount'] for i in items], ['00000002500', '00000003000'])

    def test_reason_109_and_internal_fields_are_not_public(self):
        mod = self.load_module()
        for body in [
            mod.empty_available_body('posting'),
            mod.empty_available_body('interest'),
            mod.empty_available_body('reporting'),
        ]:
            text = repr(body)
            self.assertNotIn('109', text)
            self.assertNotIn('fee', text.lower())
            self.assertNotIn('suffix', text.lower())

    def test_external_fixture_selection_is_local_config_not_public_request(self):
        mod = self.load_module()
        fixture = {
            'fixtureId': 'posting-local-tech',
            'track': 'posting',
            'materializer': {'kind': 'builtin_technical_smoke'},
            'provenance': {'class': 'local_synthetic_support'},
            'exposure': {'label': 'technical-only', 'notExtractionInput': True, 'notOracle': True},
            'reset': {'default': 'fresh_dir_per_run'},
        }
        fixture['contentSha256'] = mod.fixture_descriptor_sha256(fixture)
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / 'registry.json'
            path.write_text(__import__('json').dumps({'kind': 'p3-local-technical-fixture-selection', 'fixtures': [fixture]}))
            selected = mod.select_external_fixture('posting', path)
        self.assertEqual(selected['fixtureId'], 'posting-local-tech')
        self.assertEqual(selected['materializer']['kind'], 'builtin_technical_smoke')
        self.assertNotIn('fixtureId', mod.empty_available_body('posting'))

    def test_external_fixture_selection_rejects_hash_adulteration(self):
        mod = self.load_module()
        fixture = {
            'fixtureId': 'interest-local-tech',
            'track': 'interest',
            'materializer': {'kind': 'builtin_technical_smoke'},
            'contentSha256': '0' * 64,
            'provenance': {'class': 'local_synthetic_support'},
            'exposure': {'label': 'technical-only', 'notExtractionInput': True, 'notOracle': True},
            'reset': {'default': 'fresh_dir_per_run'},
        }
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / 'registry.json'
            path.write_text(__import__('json').dumps({'kind': 'p3-local-technical-fixture-selection', 'fixtures': [fixture]}))
            with self.assertRaises(mod.FixtureConfigError):
                mod.select_external_fixture('interest', path)

    def test_reset_state_evidence_uses_hashes_not_only_directory_names(self):
        mod = self.load_module()
        with tempfile.TemporaryDirectory() as td:
            wd = pathlib.Path(td)
            before = mod.capture_state_snapshot(wd)
            (wd / 'TRANFILE').write_bytes(b'abc')
            after = mod.capture_state_snapshot(wd)
        self.assertEqual(before['entryCount'], 0)
        self.assertEqual(after['entryCount'], 1)
        self.assertNotEqual(before['treeSha256'], after['treeSha256'])
        self.assertEqual(after['files'][0]['sha256'], __import__('hashlib').sha256(b'abc').hexdigest())

    def test_external_file_package_materializes_real_bytes_and_records_pre_cobol_snapshot(self):
        mod = self.load_module()
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            source = base / 'seeds'
            source.mkdir()
            dalytran = source / 'DALYTRAN.bin'
            dalytran.write_bytes(mod.transaction(amount=b'00000003000'))
            fixture = {
                'fixtureId': 'posting-file-package',
                'track': 'posting',
                'materializer': {'kind': 'local_file_package', 'files': {'DALYTRAN': 'seeds/DALYTRAN.bin'}},
                'provenance': {'class': 'local_synthetic_support', 'source': 'unit synthetic bytes'},
                'exposure': {'label': 'technical-only', 'notExtractionInput': True, 'notOracle': True, 'notPublicRequest': True},
                'reset': {'default': 'fresh_dir_per_run'},
            }
            fixture['contentSha256'] = mod.fixture_descriptor_sha256(fixture)
            registry = base / 'registry.json'
            registry.write_text(json.dumps({'kind': 'p3-local-technical-fixture-selection', 'fixtures': [fixture]}))
            selected = mod.select_external_fixture('posting', registry)
            workdir = base / 'work'
            workdir.mkdir()
            evidence = mod.materialize_fixture(selected, workdir)
            self.assertEqual(evidence['materializerKind'], 'local_file_package')
            self.assertEqual(evidence['files']['DALYTRAN']['sourceBytes'], 350)
            self.assertEqual(evidence['files']['DALYTRAN']['sourceSha256'], __import__('hashlib').sha256(mod.transaction(amount=b'00000003000')).hexdigest())
            self.assertEqual((pathlib.Path(evidence['files']['DALYTRAN']['materializedPath'])).read_bytes(), mod.transaction(amount=b'00000003000'))
            self.assertIn('preCobolMaterializationSnapshot', evidence)

    def test_external_file_package_rejects_unsafe_path_and_never_falls_back(self):
        mod = self.load_module()
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            fixture = {
                'fixtureId': 'posting-bad-package',
                'track': 'posting',
                'materializer': {'kind': 'local_file_package', 'files': {'DALYTRAN': '../outside.bin'}},
                'provenance': {'class': 'local_synthetic_support'},
                'exposure': {'label': 'technical-only', 'notExtractionInput': True, 'notOracle': True},
                'reset': {'default': 'fresh_dir_per_run'},
            }
            fixture['contentSha256'] = mod.fixture_descriptor_sha256(fixture)
            registry = base / 'registry.json'
            registry.write_text(json.dumps({'kind': 'p3-local-technical-fixture-selection', 'fixtures': [fixture]}))
            with self.assertRaises(mod.FixtureConfigError):
                mod.select_external_fixture('posting', registry)

    def test_materialized_fresh_reset_compares_second_preparation_to_first_original_after_mutation(self):
        mod = self.load_module()
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            source = base / 'seeds'
            source.mkdir()
            dalytran = source / 'DALYTRAN.bin'
            original = mod.transaction(amount=b'00000002500')
            dalytran.write_bytes(original)
            fixture = {
                'fixtureId': 'posting-reset-package',
                'track': 'posting',
                'materializer': {'kind': 'local_file_package', 'files': {'DALYTRAN': 'seeds/DALYTRAN.bin'}},
                'provenance': {'class': 'local_synthetic_support'},
                'exposure': {'label': 'technical-only', 'notExtractionInput': True, 'notOracle': True},
                'reset': {'default': 'fresh_dir_per_run'},
            }
            fixture['contentSha256'] = mod.fixture_descriptor_sha256(fixture)
            registry = base / 'registry.json'
            registry.write_text(json.dumps({'kind': 'p3-local-technical-fixture-selection', 'fixtures': [fixture]}))
            selected = mod.select_external_fixture('posting', registry)
            first = base / 'first'; first.mkdir()
            first_evidence = mod.materialize_fixture(selected, first)
            (first / 'DALYTRAN').write_bytes(b'STALE MUTATION')
            second = base / 'second'; second.mkdir()
            second_evidence = mod.materialize_fixture(selected, second)
            reset = mod.prove_fresh_materialization_reset(first_evidence, second_evidence)
            self.assertTrue(reset['resetVerified'])
            self.assertEqual(reset['materializedHashesMatchOriginal'], True)
            self.assertEqual((second / 'DALYTRAN').read_bytes(), original)
            self.assertNotEqual((first / 'DALYTRAN').read_bytes(), original)

if __name__ == '__main__':
    unittest.main()
