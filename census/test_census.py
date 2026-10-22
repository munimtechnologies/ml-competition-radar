# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Consistency checks for the AI-rules census (stdlib only)."""
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = ("name", "scope", "url", "read_how", "ai_assisted_code_clause", "automl_clause",
        "commercial_llm_api_inside_solution", "external_data", "pretrained_models",
        "legal_entities_may_enter", "age_or_sanctions", "winner_code_terms", "reproducibility")


def load():
    with open(os.path.join(HERE, "ai-rules-census.json"), encoding="utf-8") as f:
        return json.load(f)


def quote_lists(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("quotes", "description_quotes") and isinstance(value, list):
                yield from value
            else:
                yield from quote_lists(value)
    elif isinstance(node, list):
        for item in node:
            yield from quote_lists(item)


class CensusTest(unittest.TestCase):
    def test_version_matches_readme_and_tables(self):
        version = load()["version"]
        for name in ("README.md", "ai-rules-census.md"):
            with open(os.path.join(HERE, name), encoding="utf-8") as f:
                self.assertIn("ersion " + version, f.read(), name)
        self.assertEqual(load()["changes"][0]["version"], version)

    def test_every_record_has_the_same_keys(self):
        for record in load()["platforms"]:
            for key in KEYS:
                self.assertIn(key, record, record["name"])

    def test_quotes_are_short_fragments(self):
        quotes = list(quote_lists(load()))
        self.assertTrue(quotes)
        for quote in quotes:
            self.assertLessEqual(len(quote), 125, quote)

    def test_no_mit_claim_for_this_repository(self):
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("Apache-2.0", text)
        self.assertIsNone(re.search(r"Code in this repository: MIT", text))

    def test_doe_comparison_matches_headline(self):
        census = load()
        documents = census["doe_template_check_2026_10_22"]["documents"]
        hits = [d["id"] for d in documents if d["generative_ai_clause"]]
        self.assertEqual(hits, ["D1", "D2"])
        self.assertEqual(len(documents), 3)
        self.assertIn("2 of 3", census["headline"])


if __name__ == "__main__":
    unittest.main()
