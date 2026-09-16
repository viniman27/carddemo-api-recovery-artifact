import hashlib
import tempfile
import unittest
from pathlib import Path
from stage5_adapter import require_stage4_counterexample_review_pin

class ReviewReferenceTest(unittest.TestCase):
    def test_real_authorization_shape_root_review_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = 'Synthetic source-grounded review\n'
            path = 'STAGE4-COUNTEREXAMPLE-REVIEW.md'
            (root / path).write_text(text)
            pin = {'path': path, 'sha256': hashlib.sha256(text.encode()).hexdigest()}
            actual, content = require_stage4_counterexample_review_pin(root, {}, {'review_reference': pin})
            self.assertEqual(actual, pin)
            self.assertEqual(content, text)
