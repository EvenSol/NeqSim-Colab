from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys
import tokenize


def fail(message: str) -> None:
    raise SystemExit(message)


def check_markdown(source: str, cell_index: int) -> tuple[int, int]:
    if "\\(" in source or "\\)" in source or "\\[" in source or "\\]" in source:
        fail(f"Markdown cell {cell_index}: unsupported math delimiter")
    for command in (
        "frac",
        "mathrm",
        "mathbf",
        "Delta",
        "sum",
        "eta",
        "overline",
    ):
        if f"\\\\{command}" in source:
            fail(f"Markdown cell {cell_index}: doubled LaTeX command \\\\{command}")

    lines = source.splitlines()
    display_delimiters = [index for index, line in enumerate(lines) if line.strip() == "$$"]
    if len(display_delimiters) % 2:
        fail(f"Markdown cell {cell_index}: unmatched display delimiter")
    for index in display_delimiters:
        if lines[index].strip() != "$$":
            fail(f"Markdown cell {cell_index}: display delimiter is not standalone")

    text_without_display = re.sub(r"\$\$.*?\$\$", "", source, flags=re.DOTALL)
    inline_markers = len(re.findall(r"(?<!\$)\$(?!\$)", text_without_display))
    if inline_markers % 2:
        fail(f"Markdown cell {cell_index}: unmatched inline math delimiter")

    return len(display_delimiters) // 2, inline_markers // 2


def check_code(source: str, cell_index: int) -> None:
    try:
        ast.parse(source)
    except SyntaxError as error:
        fail(f"Code cell {cell_index}: {error}")

    tokens = tokenize.generate_tokens(iter(source.splitlines(True)).__next__)
    for token in tokens:
        if token.type == tokenize.OP and token.string == ";":
            fail(f"Code cell {cell_index}: semicolon-compressed statement")

    for line_number, line in enumerate(source.splitlines(), start=1):
        if len(line) <= 100:
            continue
        if "http://" in line or "https://" in line:
            continue
        fail(
            f"Code cell {cell_index}, line {line_number}: "
            f"{len(line)} characters exceeds 100"
        )


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: check_notebook.py PATH")
    path = Path(sys.argv[1])
    notebook = json.loads(path.read_text(encoding="utf-8"))
    if notebook.get("nbformat") != 4:
        fail("Notebook must use nbformat 4")

    code_cells = 0
    markdown_cells = 0
    display_equations = 0
    inline_expressions = 0
    all_markdown = ""
    for index, cell in enumerate(notebook["cells"]):
        source = "".join(cell.get("source", []))
        if cell["cell_type"] == "code":
            code_cells += 1
            if not source.strip():
                fail(f"Code cell {index}: empty")
            check_code(source, index)
        elif cell["cell_type"] == "markdown":
            markdown_cells += 1
            all_markdown += source
            display_count, inline_count = check_markdown(source, index)
            display_equations += display_count
            inline_expressions += inline_count

    if "process_coupled_offshore_electrification" in path.name:
        required_text = (
            "colab.research.google.com",
            "equinor/neqsim.git",
            "comparesimulations.ipynb",
            "export compressor",
            "addPowerConsumer",
            "EnergyTimeSeriesSimulator",
            "EnergyBus",
            "BatteryStorage",
            "Hywind Tampen",
            "Limitations",
            "Validation gates",
        )
    else:
        required_text = (
            "colab.research.google.com",
            "equinor/neqsim.git",
            "EnergyTimeSeriesSimulator",
            "EnergyBus",
            "BatteryStorage",
            "Hywind Tampen",
            "Limitations",
            "Validation gates",
        )
    for text in required_text:
        if text not in path.read_text(encoding="utf-8"):
            fail(f"Required notebook content missing: {text}")

    forbidden = ("TODO", "FIXME", "YOUR_TOKEN", "api_key")
    for text in forbidden:
        if text in path.read_text(encoding="utf-8"):
            fail(f"Forbidden temporary or sensitive marker: {text}")

    print(
        json.dumps(
            {
                "path": str(path),
                "code_cells": code_cells,
                "markdown_cells": markdown_cells,
                "display_equations": display_equations,
                "inline_expressions": inline_expressions,
                "status": "passed",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
