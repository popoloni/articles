"""Synthetic protocol fixtures only: these tests do not measure model accuracy."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from decision_contract import ContractError, normalize_answer, normalize_result

CHOICE = {"type": "choice", "criteria": {"a": "one", "b": "two"}}
SCORE = {"type": "score", "criteria": ["low", "middle", "high"]}
NOUL = {"type": "noul"}


class ContractTests(unittest.TestCase):
    def test_choice(self):
        r = normalize_answer({"type": "choice", "choice": "a", "probabilities": {"a": .8, "b": .2}}, CHOICE)
        self.assertEqual(r["top_options"], ["a"])
        self.assertEqual(r["top_probability"], .8)

    def test_tie_is_preserved(self):
        r = normalize_answer({"type": "choice", "probabilities": {"a": .5, "b": .5}}, CHOICE)
        self.assertEqual(r["top_options"], ["a", "b"])

    def test_score_native_and_wire_match(self):
        native = {"type": "score", "score": 1, "expected": 1.1,
                  "probabilities": {"0": .2, "1": .5, "2": .3}}
        wire = {"type": "score", "level": 1, "score": 1.1,
                "probabilities": {"0": .2, "1": .5, "2": .3}}
        self.assertEqual(normalize_answer(native, SCORE), normalize_answer(wire, SCORE))
        self.assertAlmostEqual(normalize_answer(native, SCORE)["expected_level"], 1.1)

    def test_integer_score_keys(self):
        self.assertEqual(normalize_answer({"type": "score", "probabilities": {0: 0, 1: 1, 2: 0}}, SCORE)["expected_level"], 1)

    def test_noul(self):
        self.assertEqual(normalize_answer({"type": "noul", "noul": .7}, NOUL)["yes_probability"], .7)

    def test_confidence_is_not_imported(self):
        r = normalize_answer({"type": "choice", "confidence": .99,
                              "probabilities": {"a": .7, "b": .3}}, CHOICE)
        self.assertEqual(r["top_probability"], .7)
        self.assertNotIn("confidence", r)

    def test_nonfinite_rejected(self):
        for p in (float("nan"), float("inf"), -.1, 1.1, True, ".5"):
            with self.subTest(p=p), self.assertRaises(ContractError):
                normalize_answer({"type": "noul", "noul": p}, NOUL)

    def test_bad_sum_rejected(self):
        with self.assertRaises(ContractError):
            normalize_answer({"type": "choice", "probabilities": {"a": .8, "b": .8}}, CHOICE)

    def test_missing_option_rejected(self):
        with self.assertRaises(ContractError):
            normalize_answer({"type": "choice", "probabilities": {"a": 1.0}}, CHOICE)

    def test_contradictory_choice_rejected(self):
        with self.assertRaises(ContractError):
            normalize_answer({"type": "choice", "choice": "b", "probabilities": {"a": .9, "b": .1}}, CHOICE)

    def test_wrong_type_rejected(self):
        with self.assertRaises(ContractError):
            normalize_answer({"type": "noul", "noul": .5}, CHOICE)

    def test_truncation_rejected(self):
        with self.assertRaises(ContractError):
            normalize_answer({"type": "noul", "noul": .5, "truncated": True}, NOUL)

    def test_warning_rejected(self):
        with self.assertRaises(ContractError):
            normalize_result({"answers": {"q": {"type": "noul", "noul": .5}}, "warnings": ["truncated"]}, {"q": NOUL})

    def test_missing_question_rejected(self):
        with self.assertRaises(ContractError):
            normalize_result({"answers": {}}, {"q": NOUL})

    def test_noul_distribution_disagreement_rejected(self):
        with self.assertRaises(ContractError):
            normalize_answer({"type": "noul", "noul": .7, "probabilities": {"true": .8, "false": .2}}, NOUL)

    def test_advisory_result(self):
        original = {"model": "synthetic-fixture", "answers": {"q": {"type": "noul", "noul": .5}}}
        before = copy.deepcopy(original)
        r = normalize_result(original, {"q": NOUL})
        self.assertTrue(r["advisory_only"])
        self.assertEqual(original, before)


if __name__ == "__main__":
    unittest.main()
