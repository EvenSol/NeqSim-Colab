import json
import tempfile
import unittest
from pathlib import Path

from check_notebook import Report, ledger_entries, validate_notebook


def notebook(*, executed: bool = True, error: bool = False, source: str = "# Title"):
    output = (
        [{"output_type": "error", "ename": "Boom", "evalue": "bad", "traceback": []}]
        if error
        else []
    )
    return {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [source]},
            {
                "cell_type": "code",
                "execution_count": 1 if executed else None,
                "metadata": {},
                "outputs": output,
                "source": ["value = 1"],
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


class CheckNotebookTests(unittest.TestCase):
    def write_json(self, root: Path, name: str, value) -> Path:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_passed_notebook_requires_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_json(Path(directory), "test.ipynb", notebook(executed=False))
            report = Report()
            validate_notebook(path, report, strict_execution=True, expected_code_cells=1)
            self.assertTrue(any("ledger says passed" in item for item in report.errors))

    def test_stored_error_is_always_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_json(Path(directory), "test.ipynb", notebook(error=True))
            report = Report()
            validate_notebook(path, report)
            self.assertTrue(any("Boom: bad" in item for item in report.errors))

    def test_invalid_utf8_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.ipynb"
            path.write_bytes(b'{"cells": ["\xff"]}')
            report = Report()
            validate_notebook(path, report)
            self.assertTrue(any("invalid UTF-8 JSON" in item for item in report.errors))

    def test_main_source_contract_lists_missing_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_json(Path(directory), "test.ipynb", notebook())
            report = Report()
            validate_notebook(path, report, require_main_source=True)
            self.assertTrue(any("NEQSIM_SOURCE_REF" in item for item in report.errors))

    def test_ledger_rejects_duplicate_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = {
                "schema_version": 1,
                "notebooks": [{"path": "a.ipynb"}, {"path": "a.ipynb"}],
            }
            path = self.write_json(Path(directory), "ledger.json", ledger)
            report = Report()
            ledger_entries(path, report)
            self.assertTrue(any("duplicate notebook entry" in item for item in report.errors))

    def test_sharded_ledger_loads_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_json(
                root,
                "parts/001.json",
                {"schema_version": 1, "notebooks": [{"path": "a.ipynb"}]},
            )
            index = self.write_json(
                root,
                "ledger.json",
                {
                    "schema_version": 3,
                    "active_notebook_count": 1,
                    "shards_glob": "parts/*.json",
                },
            )
            report = Report()
            entries = ledger_entries(index, report)
            self.assertEqual(set(entries), {"a.ipynb"})
            self.assertFalse(report.errors)


if __name__ == "__main__":
    unittest.main()
