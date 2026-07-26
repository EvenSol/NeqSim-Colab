# Resilient NeqSim notebook validation environments

Notebook validation must use a new isolated Python environment, but it should not
depend on a live package-index connection for every run. A transient proxy failure
is infrastructure noise; it is not evidence that the notebook or NeqSim is broken.

`bootstrap_neqsim_validation_env.py` separates artifact resolution from environment
creation:

1. When public PyPI is reachable, `pip download` resolves binary wheels with pip's
   cache disabled.
2. Every wheel is recorded in an immutable manifest with its project, version,
   byte size, SHA-256 digest, Python runtime, platform, source index, and UTC
   resolution time.
3. Every notebook run still gets a newly created virtual environment.
4. Installation into that environment uses only the verified snapshot with
   `--no-index`, `--find-links`, and `--no-cache-dir`.
5. A refresh uses bounded exponential retry. If the package index remains
   unavailable, an existing compatible snapshot is hash-verified before use.
6. Snapshot selection also verifies that every requested root package is present;
   an older snapshot cannot satisfy a larger validation toolchain by accident.
7. Concurrent automation runs share a file lock so they cannot corrupt the
   wheelhouse.

This preserves the important clean-runtime property while removing repeated PyPI
availability from the critical path. It does not use an unofficial mirror, copy an
existing environment, bypass TLS, or silently accept unverified packages.

## Standard validation command

```bash
python scripts/bootstrap_neqsim_validation_env.py \
  --venv /tmp/neqsim-notebook-validation \
  --neqsim-version 3.16.0 \
  --refresh
```

The default snapshot location is
`/workspace/.cache/neqsim-validation-wheelhouse`. Set
`NEQSIM_WHEELHOUSE_ROOT` when a different persistent writable workspace path is
needed.

The command attempts a new resolution first. On success it creates an immutable
snapshot and a fresh environment. If public PyPI remains unavailable and a
compatible snapshot already exists, it creates the fresh environment from that
verified snapshot and records `verified-snapshot-fallback` in its JSON evidence.
If neither route is available, it exits with code 75 and makes no repository
changes. Exit code 75 is reserved for retryable package-index resolution failure;
unsafe targets, corrupt artifacts, and failed offline installs are reported as
non-transient failures with exit code 1 so automation does not retry them forever.

Use `--require-online-resolution` only for a dedicated artifact-refresh job. Normal
notebook execution should permit the verified fallback. The validation ledger must
record the actual NeqSim, Python, and Java versions plus whether the snapshot was
newly resolved or reused.

The default toolchain includes notebook parsing, plotting, tabular analysis,
IPython display, and CairoSVG for equation-rendering review. Add another validation
dependency with repeated `--extra-package PACKAGE` options; the bootstrap will
resolve or select only a snapshot whose manifest includes every requested package.

## Trust and maintenance policy

- Populate snapshots only from `https://pypi.org/simple`.
- Never edit a snapshot after its manifest is written.
- Reject missing, additional, size-mismatched, or hash-mismatched wheel files.
- Keep old snapshots so a bad or incomplete refresh cannot destroy the last known
  good environment.
- Refresh after a new NeqSim release and periodically while PyPI is healthy.
- Treat an exact, verified fallback as clean execution evidence, but do not describe
  it as a new online resolution.
- Continue to execute the full notebook, retain outputs, run engineering checks,
  inspect figures, and validate MathJax rendering. The wheelhouse solves only the
  package-resolution failure mode.
