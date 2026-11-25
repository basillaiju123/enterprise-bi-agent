import unittest

from src.rag.relevance import (
    DEFAULT_MIN_SEMANTIC_SCORE,
    is_relevant_score,
)


class TestRagRelevance(unittest.TestCase):
    def test_calibrated_default_value(self):
        self.assertEqual(DEFAULT_MIN_SEMANTIC_SCORE, 0.302452)

    def test_calibration_positive_score_is_accepted(self):
        self.assertTrue(is_relevant_score(0.317616, 0.302452))

    def test_calibration_negative_score_is_rejected(self):
        self.assertFalse(is_relevant_score(0.287288, 0.302452))

    def test_threshold_boundary_is_inclusive(self):
        self.assertTrue(is_relevant_score(0.302452, 0.302452))

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            is_relevant_score(0.5, 1.1)


if __name__ == "__main__":
    unittest.main()
