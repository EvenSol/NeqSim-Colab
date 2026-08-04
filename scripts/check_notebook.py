#!/usr/bin/env python3
"""Validate NeqSim-Colab notebooks, catalog links, and maintenance evidence.

The default repository-wide check is intentionally compatible with the existing
maintenance backlog: structural corruption and false ``passed`` claims fail,
while valid notebooks that have not yet been executed are reported as warnings.
Use ``--require-main-source`` for new advanced notebooks; it makes the current
NeqSim ``master`` source-build provenance contract mandatory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


CATALOG_LINK = re.compile(r"\[[^\]]+\]\(([^)]+\.ipynb)(?:#[^)]*)?\)")
MAIN_SOURCE_MARKERS = (
    "NEQSIM_SOURCE_REF",
    "equinor/neqsim",
    "rev-parse",
    "NEQSIM_JVM_AUTOSTART",
    "addClassPath",
    "getProtectionDomain",
)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked: int = 0

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def load_json(path: Path) -> Any:
    """Load strict UTF-8 JSON and retain useful path context on failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: invalid UTF-8 JSON: {error}") from error


def source_text(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def code_cells(notebook: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        cell
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]


def stored_errors(cells: Iterable[dict[str, Any]]) -> list[str]:
    errors = []
    for cell_number, cell in enumerate(cells, start=1):
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                name = output.get("ename", "stored error")
                value = output.get("evalue", "")
                errors.append(f"code cell {cell_number}: {name}: {value}")
    return errors


def git_blob_sha1(path: Path) -> str:
    """Return the Git blob identity for the current file bytes."""
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def validate_notebook(
    path: Path,
    report: Report,
    *,
    strict_execution: bool = False,
    expected_code_cells: int | None = None,
    require_main_source: bool = False,
    allow_stored_errors: bool = False,
) -> dict[str, Any] | None:
    """Validate one notebook and append findings to ``report``."""
    report.checked += 1
    try:
        notebook = load_json(path)
    except ValueError as error:
        report.error(str(error))
        return None

    if not isinstance(notebook, dict):
        report.error(f"{path}: notebook root must be an object")
        return None
    if notebook.get("nbformat") != 4:
        report.error(f"{path}: expected nbformat 4")
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        report.error(f"{path}: cells must be a list")
        return notebook

    codes = code_cells(notebook)
    if expected_code_cells is not None and len(codes) != expected_code_cells:
        report.error(
            f"{path}: ledger records {expected_code_cells} code cells, "
            f"notebook has {len(codes)}"
        )

    errors = stored_errors(codes)
    for error in errors:
        message = f"{path}: {error}"
        if allow_stored_errors:
            report.warn(f"legacy baseline: {message}")
        else:
            report.error(message)

    missing_counts = [
        number
        for number, cell in enumerate(codes, start=1)
        if cell.get("execution_count") is None
    ]
    if strict_execution and missing_counts:
        report.error(
            f"{path}: ledger says passed but execution counts are missing "
            f"for code cells {missing_counts}"
        )
    elif missing_counts:
        report.warn(
            f"{path}: {len(missing_counts)} code cells require execution"
        )

    markdown = [
        source_text(cell)
        for cell in cells
        if cell.get("cell_type") == "markdown"
    ]
    if not any(re.search(r"(?m)^#\s+\S", text) for text in markdown):
        report.warn(f"{path}: no level-one Markdown title")

    all_source = "\n".join(source_text(cell) for cell in cells)
    obsolete_math = [token for token in (r"\(", r"\)", r"\[", r"\]") if token in all_source]
    if obsolete_math:
        report.warn(
            f"{path}: review non-Colab-safe math delimiters "
            f"{', '.join(obsolete_math)}"
        )

    if require_main_source:
        missing = [marker for marker in MAIN_SOURCE_MARKERS if marker not in all_source]
        if missing:
            report.error(
                f"{path}: missing NeqSim master-source provenance markers: "
                f"{', '.join(missing)}"
            )
    return notebook


def ledger_entries(path: Path, report: Report) -> dict[str, dict[str, Any]]:
    try:
        ledger = load_json(path)
    except ValueError as error:
        report.error(str(error))
        return {}
    if not isinstance(ledger, dict):
        report.error(f"{path}: expected a ledger object")
        return {}

    entry_groups: list[tuple[Path, list[Any]]] = []
    if isinstance(ledger.get("notebooks"), list):
        entry_groups.append((path, ledger["notebooks"]))
    elif isinstance(ledger.get("shards_glob"), str):
        shard_paths = sorted(path.parent.glob(ledger["shards_glob"]))
        if not shard_paths:
            report.error(
                f"{path}: shards_glob matched no files: "
                f"{ledger['shards_glob']}"
            )
        for shard_path in shard_paths:
            try:
                shard = load_json(shard_path)
            except ValueError as error:
                report.error(str(error))
                continue
            if not isinstance(shard, dict) or not isinstance(
                shard.get("notebooks"), list
            ):
                report.error(
                    f"{shard_path}: expected an object with a notebooks list"
                )
                continue
            entry_groups.append((shard_path, shard["notebooks"]))
    else:
        report.error(
            f"{path}: expected notebooks or a string shards_glob"
        )
        return {}

    entries: dict[str, dict[str, Any]] = {}
    for source_path, source_entries in entry_groups:
        for entry in source_entries:
            notebook_path = entry.get("path") if isinstance(entry, dict) else None
            if not isinstance(notebook_path, str):
                report.error(
                    f"{source_path}: every notebook entry needs a string path"
                )
                continue
            if notebook_path in entries:
                report.error(
                    f"{source_path}: duplicate notebook entry {notebook_path}"
                )
            entries[notebook_path] = entry

    active_count = ledger.get("active_notebook_count")
    if isinstance(active_count, int) and active_count != len(entries):
        report.error(
            f"{path}: active_notebook_count is {active_count}, "
            f"loaded {len(entries)}"
        )

    retired = ledger.get("retired_notebooks", [])
    if not isinstance(retired, list):
        report.error(f"{path}: retired_notebooks must be a list")
    else:
        retired_paths = [
            item.get("path") for item in retired if isinstance(item, dict)
        ]
        duplicates = set(entries).intersection(path for path in retired_paths if path)
        for duplicate in sorted(duplicates):
            report.error(f"{path}: active and retired entries overlap: {duplicate}")
    return entries


def catalog_targets(path: Path, report: Report) -> set[Path]:
    try:
        catalog = load_json(path)
    except ValueError as error:
        report.error(str(error))
        return set()
    targets: set[Path] = set()
    for cell in catalog.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        for raw_target in CATALOG_LINK.findall(source_text(cell)):
            if "://" in raw_target:
                continue
            target = (path.parent / raw_target).resolve()
            targets.add(target)
            if not target.is_file():
                report.error(f"{path}: broken notebook link {raw_target}")
    return targets


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--all", action="store_true", help="check notebooks/**/*.ipynb")
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("notebooks/notebook_maintenance_ledger.json"),
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("notebooks/examples_of_NeqSim_in_Colab.ipynb"),
    )
    parser.add_argument("--require-main-source", action="store_true")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("scripts/notebook_integrity_baseline.json"),
    )
    parser.add_argument("--quiet-warnings", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = Report()
    try:
        baseline = load_json(args.baseline)
    except ValueError as error:
        report.error(str(error))
        baseline = {}
    stored_error_baseline = baseline.get("stored_error_blob_sha1", {})
    if not isinstance(stored_error_baseline, dict):
        report.error(f"{args.baseline}: stored_error_blob_sha1 must be an object")
        stored_error_baseline = {}
    entries = ledger_entries(args.ledger, report)
    catalog_targets(args.catalog, report)

    selected = set(args.paths)
    if args.all:
        selected.update(Path("notebooks").rglob("*.ipynb"))
    if not selected:
        selected.update(Path(path) for path in entries)

    for path in sorted(selected):
        entry = entries.get(path.as_posix())
        strict = bool(entry and entry.get("execution_status") == "passed")
        expected = entry.get("code_cells") if strict else None
        expected_error_blob = stored_error_baseline.get(path.as_posix())
        allow_stored_errors = bool(
            isinstance(expected_error_blob, str)
            and path.is_file()
            and git_blob_sha1(path) == expected_error_blob
            and not strict
        )
        validate_notebook(
            path,
            report,
            strict_execution=strict,
            expected_code_cells=expected if isinstance(expected, int) else None,
            require_main_source=args.require_main_source,
            allow_stored_errors=allow_stored_errors,
        )

    for path_text in sorted(entries):
        if not Path(path_text).is_file():
            report.error(f"{args.ledger}: active entry target is missing: {path_text}")

    if not args.quiet_warnings:
        for warning in report.warnings:
            print(f"WARNING: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(
        f"Checked {report.checked} notebooks: "
        f"{len(report.errors)} errors, {len(report.warnings)} warnings"
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
