#!/usr/bin/env python3
"""Execute a notebook in a fresh process without Jupyter kernel sockets.

Some restricted validation environments prohibit local ZeroMQ/TCP kernel
connections. This runner preserves the important clean-process and ordered-cell
properties while capturing stdout, rich display data, execute results, and inline
Matplotlib figures directly through IPython. It writes the notebook only after
every code cell succeeds.
"""

from __future__ import annotations

import argparse
import base64
import sys
import time
from pathlib import Path
from typing import Any

import nbformat
import matplotlib
from IPython.core.displayhook import DisplayHook
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from matplotlib_inline.backend_inline import configure_inline_support


def notebook_data(data: dict[str, Any]) -> dict[str, Any]:
    """Convert binary rich-display payloads to notebook base64 strings."""
    normalized = dict(data)
    for mime_type, value in list(normalized.items()):
        if isinstance(value, bytes):
            normalized[mime_type] = base64.b64encode(value).decode("ascii")
    return normalized


class NotebookDisplayHook(DisplayHook):
    """Capture the final expression as a notebook ``execute_result``."""

    def __init__(self, shell: InteractiveShell) -> None:
        super().__init__(shell=shell)
        self.formatted: list[tuple[dict[str, Any], dict[str, Any]]] = []

    def write_output_prompt(self) -> None:
        return

    def write_format_data(
        self,
        format_dict: dict[str, Any],
        md_dict: dict[str, Any] | None = None,
    ) -> None:
        self.formatted.append((format_dict, md_dict or {}))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument(
        "--allow-stderr",
        action="store_true",
        help="retain stderr instead of treating it as a failed validation",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notebook = nbformat.read(args.notebook, as_version=4)
    matplotlib.use("module://matplotlib_inline.backend_inline", force=True)
    matplotlib.interactive(True)
    shell = InteractiveShell.instance()
    configure_inline_support(shell, "module://matplotlib_inline.backend_inline")
    display_hook = NotebookDisplayHook(shell)
    shell.displayhook = display_hook
    shell.display_trap.hook = display_hook
    sys.displayhook = display_hook

    execution_count = 0
    started = time.monotonic()
    for notebook_index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        execution_count += 1
        print(
            f"[{execution_count}] notebook cell {notebook_index}",
            flush=True,
        )
        cell.outputs = []
        cell.execution_count = None
        display_hook.formatted = []
        with capture_output(stdout=True, stderr=True, display=True) as captured:
            result = shell.run_cell(cell.source, store_history=True)

        error = result.error_before_exec or result.error_in_exec
        if error is not None:
            raise RuntimeError(
                f"notebook cell {notebook_index} failed: {error}"
            ) from error
        if captured.stderr and not args.allow_stderr:
            raise RuntimeError(
                f"notebook cell {notebook_index} wrote stderr: "
                f"{captured.stderr[:500]}"
            )

        outputs = []
        if captured.stdout:
            outputs.append(
                nbformat.v4.new_output(
                    output_type="stream",
                    name="stdout",
                    text=captured.stdout,
                )
            )
        if captured.stderr:
            outputs.append(
                nbformat.v4.new_output(
                    output_type="stream",
                    name="stderr",
                    text=captured.stderr,
                )
            )
        for rich_output in captured.outputs:
            outputs.append(
                nbformat.v4.new_output(
                    output_type="display_data",
                    data=notebook_data(rich_output.data),
                    metadata=rich_output.metadata,
                )
            )
        for data, metadata in display_hook.formatted:
            outputs.append(
                nbformat.v4.new_output(
                    output_type="execute_result",
                    execution_count=execution_count,
                    data=notebook_data(data),
                    metadata=metadata,
                )
            )

        cell.outputs = outputs
        cell.execution_count = execution_count

    nbformat.validate(notebook)
    nbformat.write(notebook, args.notebook)
    elapsed = time.monotonic() - started
    print(
        f"Executed {execution_count} code cells in {elapsed:.1f} s: "
        f"{args.notebook}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
