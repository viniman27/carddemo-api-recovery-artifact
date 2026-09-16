import unittest
from pathlib import Path
from stream_result import parse_result

class StreamTests(unittest.TestCase):
    def test_real_stream_with_empty_final_output(self):
        result = parse_result(Path(__file__).with_name('baseline-response.txt').read_text())
        self.assertEqual(result['text'], 'ISOLATED_OK')
        self.assertEqual(result['model'], 'gpt-6-astra')
        self.assertEqual(result['tools'], [])

    def test_missing_completion_is_not_success(self):
        with self.assertRaises(ValueError):
            parse_result('data: {"type":"response.output_text.done","text":"ISOLATED_OK","output_index":0,"content_index":0}\n')

    def test_provider_error_is_not_success(self):
        with self.assertRaises(ValueError):
            parse_result('data: {"type":"response.failed","response":{"status":"failed"}}\n')

if __name__ == '__main__':
    unittest.main()
