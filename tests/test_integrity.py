import json
import tempfile
import unittest
from pathlib import Path

from tools.check_integrity import validate


def entry(entry_id, kind, status, path, source_ids=None, related_ids=None):
    return {
        "id": entry_id, "kind": kind, "status": status,
        "title": entry_id, "path": path, "summary": "Example for validation",
        "tags": [], "source_ids": source_ids or [], "related_ids": related_ids or [],
        "created": "2026-09-17", "updated": "2026-09-17",
    }


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "index").mkdir()
        (self.root / "planning").mkdir()
        self.entries = [
            entry("SRC-0001", "source", "recorded", "planning/source.md"),
            entry("SPEC-0001", "spec", "confirmed", "planning/spec.md", ["SRC-0001"]),
        ]
        self.write("planning/source.md", "# User input\n")
        self.write("planning/spec.md", "# Specification\n")

    def write(self, path, contents):
        (self.root / path).write_text(contents, encoding="utf-8")

    def check(self):
        self.write("index/catalog.json", json.dumps({"schema_version": 1, "entries": self.entries}))
        return validate(self.root)

    def assert_error(self, fragment):
        self.assertTrue(any(fragment in error for error in self.check()), fragment)

    def add_dataset(self, suffix, contents):
        path = f"planning/data.{suffix}"
        self.write(path, contents)
        self.entries.append(entry("DATA-0001", "dataset", "draft", path, related_ids=["SPEC-0001"]))

    def test_valid_repository(self):
        self.assertEqual([], self.check())

    def test_missing_and_unindexed_files(self):
        (self.root / "planning/spec.md").unlink()
        self.write("planning/forgotten.md", "# Unindexed\n")
        errors = self.check()
        self.assertTrue(any("missing file" in error for error in errors))
        self.assertTrue(any("Unindexed" in error for error in errors))

    def test_duplicate_ids_and_paths(self):
        self.entries.append(dict(self.entries[0]))
        errors = self.check()
        self.assertTrue(any("duplicate ID" in error for error in errors))
        self.assertTrue(any("duplicate path" in error for error in errors))

    def test_invalid_references(self):
        self.entries[1]["related_ids"] = ["IDEA-0001"]
        self.entries[1]["source_ids"] = ["SPEC-0001"]
        errors = self.check()
        self.assertTrue(any("missing reference" in error for error in errors))
        self.assertTrue(any("self reference" in error for error in errors))
        self.assertTrue(any("source_ids must refer" in error for error in errors))

    def test_confirmed_requires_source(self):
        self.entries[1]["source_ids"] = []
        self.assert_error("confirmed entries require source_ids")

    def test_invalid_status_and_dates(self):
        self.entries[1]["status"] = "recorded"
        self.entries[1]["updated"] = "2026-09-16"
        errors = self.check()
        self.assertTrue(any("invalid status" in error for error in errors))
        self.assertTrue(any("updated precedes" in error for error in errors))

    def test_path_escape(self):
        self.entries[1]["path"] = "planning/../README.md"
        self.assert_error("canonical relative")

    def test_malformed_metadata_does_not_crash(self):
        self.entries[1].update({"kind": [], "status": {}, "source_ids": [None], "created": 17})
        self.assertGreaterEqual(len(self.check()), 4)

    def test_json_duplicate_keys_and_nonstandard_numbers(self):
        self.add_dataset("json", '{"value": 1, "value": 2}')
        self.assert_error("Duplicate JSON key")
        self.write("planning/data.json", '{"value": NaN}')
        self.assert_error("Invalid JSON constant")
        self.write("planning/data.json", '{"value": null}')
        self.assertEqual([], self.check())

    def test_csv_quotes_newlines_and_invalid_rows(self):
        self.add_dataset("csv", 'id,description\nrow-1,"line one,\nline two"\n')
        self.assertEqual([], self.check())
        self.write("planning/data.csv", "id,description\nrow-1,one,extra\n")
        self.assert_error("wrong field count")
        self.write("planning/data.csv", "id,id\nrow-1,one\n")
        self.assert_error("headers must be nonempty and unique")

    def test_dataset_requires_explanation(self):
        self.add_dataset("json", "{}")
        self.entries[-1]["related_ids"] = []
        self.assert_error("dataset requires a related spec")

    def test_catalog_parse_errors(self):
        self.write("index/catalog.json", '{"schema_version": 1, "schema_version": 2}')
        self.assertTrue(any("Duplicate JSON key" in error for error in validate(self.root)))


if __name__ == "__main__":
    unittest.main()
