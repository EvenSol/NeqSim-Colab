import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import unquote


def cell_source_text(source):
    if isinstance(source, list):
        return "\n".join(str(line) for line in source)
    return str(source or "")


def extract_linked_notebooks(index_path):
    with index_path.open("r", encoding="utf-8") as handle:
        notebook = json.load(handle)

    links = []
    seen = set()
    pattern = re.compile(r"\(([^)]+\.ipynb[^)]*)\)", re.IGNORECASE)
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        text = cell_source_text(cell.get("source", ""))
        for match in pattern.finditer(text):
            raw = match.group(1).strip()
            if raw.startswith(("http://", "https://")):
                continue
            cleaned = raw.split("#", 1)[0].strip().replace("\\", "/")
            cleaned = unquote(cleaned)
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            links.append(cleaned)
    return links


def summarize_failure(stderr, stdout):
    combined = (stderr or "") + "\n" + (stdout or "")
    interesting = []
    for line in combined.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if (
            "Traceback" in stripped
            or "CellExecutionError" in stripped
            or "UsageError" in stripped
            or "ModuleNotFoundError" in stripped
            or "ImportError" in stripped
            or "NameError" in stripped
            or "AttributeError" in stripped
            or "TypeError" in stripped
            or "FileNotFoundError" in stripped
            or "No such file" in stripped
            or "Exception" in stripped
            or "Error" in stripped
            or "Timeout" in stripped
        ):
            interesting.append(stripped)
    if interesting:
        return "\n".join(interesting[-20:])
    tail = combined.splitlines()[-20:]
    return "\n".join(tail)


def write_report(repo, output, args, total_available, results, started_at):
    elapsed = round(time.time() - started_at, 2)
    counts = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    report = {
        "index": args.index,
        "total_available": total_available,
        "executed_count": len(results),
        "start": args.start,
        "limit": args.limit,
        "timeout_s": args.timeout,
        "elapsed_s": elapsed,
        "counts": counts,
        "results": results,
    }
    with (repo / output).open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return counts


def main():
    parser = argparse.ArgumentParser(description="Execute notebooks linked from examples_of_NeqSim_in_Colab.ipynb")
    parser.add_argument("--index", default="notebooks/examples_of_NeqSim_in_Colab.ipynb")
    parser.add_argument("--output", default="_tmp_linked_notebook_execution_report.json")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only-failed-from", default="")
    args = parser.parse_args()

    repo = Path.cwd()
    index_path = repo / args.index
    linked = extract_linked_notebooks(index_path)
    if args.only_failed_from:
        with (repo / args.only_failed_from).open("r", encoding="utf-8") as handle:
            previous = json.load(handle)
        wanted = {item["path"] for item in previous.get("results", []) if item.get("status") != "passed"}
        linked = [path for path in linked if path in wanted]

    total_available = len(linked)
    if args.start:
        linked = linked[args.start:]
    if args.limit:
        linked = linked[: args.limit]

    python = sys.executable
    output_dir = Path(tempfile.mkdtemp(prefix="neqsim_colab_exec_"))
    results = []
    started_at = time.time()

    print(f"Executing {len(linked)} linked notebooks (from {total_available} available)")
    print(f"Temporary executed-notebook output: {output_dir}")
    print(f"Per-notebook timeout: {args.timeout}s")

    try:
        for index, relative in enumerate(linked, start=1 + args.start):
            notebook_path = repo / "notebooks" / relative
            display = relative
            if not notebook_path.exists():
                result = {
                    "path": display,
                    "status": "missing",
                    "duration_s": 0.0,
                    "summary": f"Missing file: {notebook_path}",
                }
                results.append(result)
                print(f"[{index}/{total_available}] MISSING {display}")
                continue

            out_name = notebook_path.stem + ".executed.ipynb"
            command = [
                python,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                str(notebook_path),
                "--output",
                out_name,
                "--output-dir",
                str(output_dir),
                "--ExecutePreprocessor.kernel_name=python3",
                f"--ExecutePreprocessor.timeout={args.timeout}",
            ]
            print(f"[{index}/{total_available}] RUN {display}", flush=True)
            notebook_started = time.time()
            try:
                completed = subprocess.run(
                    command,
                    cwd=str(repo),
                    text=True,
                    capture_output=True,
                    timeout=args.timeout,
                )
                duration = round(time.time() - notebook_started, 2)
                if completed.returncode == 0:
                    status = "passed"
                    summary = ""
                    print(f"[{index}/{total_available}] PASS {display} ({duration}s)", flush=True)
                else:
                    status = "failed"
                    summary = summarize_failure(completed.stderr, completed.stdout)
                    print(f"[{index}/{total_available}] FAIL {display} ({duration}s)", flush=True)
                results.append(
                    {
                        "path": display,
                        "status": status,
                        "duration_s": duration,
                        "returncode": completed.returncode,
                        "summary": summary,
                    }
                )
                write_report(repo, args.output, args, total_available, results, started_at)
            except subprocess.TimeoutExpired as exc:
                duration = round(time.time() - notebook_started, 2)
                summary = summarize_failure(exc.stderr or "", exc.stdout or "")
                if summary:
                    summary = "Timed out.\n" + summary
                else:
                    summary = "Timed out."
                results.append(
                    {
                        "path": display,
                        "status": "timeout",
                        "duration_s": duration,
                        "returncode": None,
                        "summary": summary,
                    }
                )
                write_report(repo, args.output, args, total_available, results, started_at)
                print(f"[{index}/{total_available}] TIMEOUT {display} ({duration}s)", flush=True)
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)

    counts = write_report(repo, args.output, args, total_available, results, started_at)
    print("SUMMARY", json.dumps(counts, sort_keys=True))
    print(f"Report written to {args.output}")
    return 1 if any(item["status"] != "passed" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
