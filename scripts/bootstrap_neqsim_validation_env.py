#!/usr/bin/env python3
"""Create a clean NeqSim validation environment from verified PyPI wheels.

The bootstrap separates two concerns:

1. Resolve immutable wheel artifacts from public PyPI when the package index is
   available, with bounded retries.
2. Create every validation environment from a hash-verified wheel snapshot,
   without using pip's mutable cache or requiring network access.

This prevents transient package-index failures from blocking notebook execution
after one trustworthy snapshot has been created for a Python runtime.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import time
import venv
import zipfile
from pathlib import Path
from typing import Any, Iterator, Sequence


SCHEMA_VERSION = 1
PUBLIC_PYPI_INDEX = "https://pypi.org/simple"
DEFAULT_PACKAGES = (
    "nbformat",
    "ipython",
    "matplotlib",
    "pandas",
    "numpy",
    "cairosvg",
)
SAFE_VENV_MARKER = "pyvenv.cfg"


class BootstrapError(RuntimeError):
    """Raised when no trustworthy validation environment can be created."""


class TransientBootstrapError(BootstrapError):
    """Raised when a later retry can reasonably resolve the blocker."""


def utc_now() -> str:
    """Return a UTC timestamp without fractional seconds."""
    return dt.datetime.now(dt.timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")


def runtime_key() -> str:
    """Return a wheel-compatibility key for the current interpreter."""
    implementation = platform.python_implementation().lower()
    python_tag = f"{sys.version_info.major}{sys.version_info.minor}"
    system = platform.system().lower()
    machine = re.sub(r"[^a-zA-Z0-9_.-]+", "-", platform.machine().lower())
    return f"{implementation}-{python_tag}-{system}-{machine}"


def sha256_file(path: Path) -> str:
    """Calculate a file SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_wheel_identity(path: Path) -> tuple[str, str]:
    """Read the normalized project name and version from wheel metadata."""
    with zipfile.ZipFile(path) as archive:
        metadata_names = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise BootstrapError(
                f"Expected one METADATA file in {path.name}, "
                f"found {len(metadata_names)}"
            )
        metadata = archive.read(metadata_names[0]).decode(
            "utf-8",
            errors="strict",
        )

    project_match = re.search(r"(?m)^Name:\s*(.+?)\s*$", metadata)
    version_match = re.search(r"(?m)^Version:\s*(.+?)\s*$", metadata)
    if project_match is None or version_match is None:
        raise BootstrapError(f"Missing project identity in {path.name}")

    project = re.sub(r"[-_.]+", "-", project_match.group(1).lower())
    return project, version_match.group(1)


def wheel_records(directory: Path) -> list[dict[str, Any]]:
    """Create deterministic wheel records for a snapshot manifest."""
    records = []
    identities = set()
    for wheel_path in sorted(directory.glob("*.whl")):
        project, version = read_wheel_identity(wheel_path)
        identity = (project, version)
        if identity in identities:
            raise BootstrapError(
                f"Duplicate wheel identity {project}=={version}"
            )
        identities.add(identity)
        records.append(
            {
                "filename": wheel_path.name,
                "project": project,
                "version": version,
                "size_bytes": wheel_path.stat().st_size,
                "sha256": sha256_file(wheel_path),
            }
        )
    if not records:
        raise BootstrapError("The downloaded wheel set is empty")
    return records


def neqsim_version_from_records(
    records: Sequence[dict[str, Any]],
) -> str:
    """Return the single NeqSim version in a wheel record set."""
    versions = {
        record["version"]
        for record in records
        if record["project"] == "neqsim"
    }
    if len(versions) != 1:
        raise BootstrapError(
            f"Expected one NeqSim wheel version, found {sorted(versions)}"
        )
    return next(iter(versions))


def manifest_requirements(
    neqsim_version: str,
    extra_packages: Sequence[str],
) -> list[str]:
    """Build root requirements used for both resolution and installation."""
    return [
        f"neqsim=={neqsim_version}",
        *extra_packages,
    ]


def write_manifest(
    directory: Path,
    requested_neqsim_version: str,
    extra_packages: Sequence[str],
    download_command: Sequence[str],
) -> dict[str, Any]:
    """Write and return an immutable snapshot manifest."""
    records = wheel_records(directory)
    resolved_neqsim_version = neqsim_version_from_records(records)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now(),
        "artifact_origin": "public-pypi",
        "source_index": PUBLIC_PYPI_INDEX,
        "runtime_key": runtime_key(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "sysconfig_platform": sysconfig.get_platform(),
        },
        "requested_neqsim_version": requested_neqsim_version,
        "resolved_neqsim_version": resolved_neqsim_version,
        "root_requirements": manifest_requirements(
            resolved_neqsim_version,
            extra_packages,
        ),
        "download_command": list(download_command),
        "pip_cache_disabled": True,
        "wheels": records,
    }
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_and_verify_manifest(snapshot: Path) -> dict[str, Any]:
    """Verify runtime compatibility, file inventory, sizes, and hashes."""
    manifest_path = snapshot / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BootstrapError(
            f"Invalid snapshot manifest at {manifest_path}: {error}"
        ) from error

    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise BootstrapError(
            f"Unsupported manifest schema in {manifest_path}"
        )
    if manifest.get("runtime_key") != runtime_key():
        raise BootstrapError(
            f"Snapshot runtime {manifest.get('runtime_key')} does not match "
            f"{runtime_key()}"
        )
    if manifest.get("artifact_origin") != "public-pypi":
        raise BootstrapError("Snapshot origin is not public PyPI")
    if manifest.get("source_index") != PUBLIC_PYPI_INDEX:
        raise BootstrapError("Snapshot index is not the configured PyPI index")

    expected_files = {
        record["filename"]
        for record in manifest.get("wheels", [])
    }
    actual_files = {
        path.name
        for path in snapshot.glob("*.whl")
    }
    if actual_files != expected_files:
        raise BootstrapError(
            f"Wheel inventory mismatch in {snapshot}: "
            f"expected {sorted(expected_files)}, got {sorted(actual_files)}"
        )

    for record in manifest["wheels"]:
        wheel_path = snapshot / record["filename"]
        if wheel_path.stat().st_size != record["size_bytes"]:
            raise BootstrapError(f"Wheel size mismatch: {wheel_path.name}")
        if sha256_file(wheel_path) != record["sha256"]:
            raise BootstrapError(f"Wheel hash mismatch: {wheel_path.name}")

    resolved = neqsim_version_from_records(manifest["wheels"])
    if resolved != manifest.get("resolved_neqsim_version"):
        raise BootstrapError("Manifest NeqSim version is inconsistent")
    return manifest


def snapshot_candidates(
    wheelhouse_root: Path,
    requested_version: str,
) -> list[Path]:
    """Return newest compatible snapshot paths first."""
    runtime_root = wheelhouse_root / f"schema-{SCHEMA_VERSION}" / runtime_key()
    if requested_version == "latest":
        candidates = runtime_root.glob("neqsim-*/*")
    else:
        candidates = (
            runtime_root / f"neqsim-{requested_version}"
        ).glob("*")
    return sorted(
        (
            path
            for path in candidates
            if path.is_dir() and not path.name.startswith(".")
        ),
        reverse=True,
    )


def select_verified_snapshot(
    wheelhouse_root: Path,
    requested_version: str,
    extra_packages: Sequence[str],
) -> tuple[Path, dict[str, Any]] | None:
    """Select the newest snapshot that passes complete verification."""
    required_extras = set(extra_packages)
    for snapshot in snapshot_candidates(
        wheelhouse_root,
        requested_version,
    ):
        try:
            manifest = load_and_verify_manifest(snapshot)
        except (BootstrapError, OSError):
            continue
        if not required_extras.issubset(
            set(manifest.get("root_requirements", []))
        ):
            continue
        return snapshot, manifest
    return None


def run_command(
    command: Sequence[str],
    *,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess without invoking a shell."""
    return subprocess.run(
        list(command),
        check=False,
        text=True,
        capture_output=capture,
    )


def download_snapshot(
    wheelhouse_root: Path,
    requested_version: str,
    extra_packages: Sequence[str],
    attempts: int,
    initial_backoff_seconds: float,
    timeout_seconds: int,
) -> tuple[Path, dict[str, Any]]:
    """Resolve wheels from public PyPI with bounded exponential backoff."""
    if attempts < 1:
        raise BootstrapError("Download attempts must be at least one")

    staging_root = wheelhouse_root / ".staging"
    staging_root.mkdir(parents=True, exist_ok=True)
    package_spec = (
        "neqsim"
        if requested_version == "latest"
        else f"neqsim=={requested_version}"
    )
    requirements = [package_spec, *extra_packages]
    errors = []

    for attempt in range(1, attempts + 1):
        attempt_path = Path(
            tempfile.mkdtemp(
                prefix="snapshot-",
                dir=staging_root,
            )
        )
        command = [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--dest",
            str(attempt_path),
            "--only-binary=:all:",
            "--no-cache-dir",
            "--disable-pip-version-check",
            "--index-url",
            PUBLIC_PYPI_INDEX,
            "--timeout",
            str(timeout_seconds),
            "--retries",
            "0",
            *requirements,
        ]
        result = run_command(command, capture=True)
        (attempt_path / "pip-download.log").write_text(
            result.stdout + result.stderr,
            encoding="utf-8",
        )
        if result.returncode == 0:
            try:
                manifest = write_manifest(
                    attempt_path,
                    requested_version,
                    extra_packages,
                    command,
                )
                resolved = manifest["resolved_neqsim_version"]
                timestamp = manifest["created_at_utc"].replace(
                    ":",
                    "",
                ).replace("-", "")
                manifest_digest = sha256_file(
                    attempt_path / "manifest.json"
                )[:12]
                snapshot_name = f"{timestamp}-{manifest_digest}"
                snapshot_parent = (
                    wheelhouse_root
                    / f"schema-{SCHEMA_VERSION}"
                    / runtime_key()
                    / f"neqsim-{resolved}"
                )
                snapshot_parent.mkdir(parents=True, exist_ok=True)
                snapshot_path = snapshot_parent / snapshot_name
                os.replace(attempt_path, snapshot_path)
                verified = load_and_verify_manifest(snapshot_path)
                return snapshot_path, verified
            except Exception:
                shutil.rmtree(attempt_path, ignore_errors=True)
                raise

        tail = (result.stdout + result.stderr)[-4000:]
        errors.append(
            {
                "attempt": attempt,
                "returncode": result.returncode,
                "tail": tail,
            }
        )
        shutil.rmtree(attempt_path, ignore_errors=True)
        if attempt < attempts:
            delay = initial_backoff_seconds * (2 ** (attempt - 1))
            time.sleep(delay)

    raise TransientBootstrapError(
        "Public PyPI wheel resolution failed after "
        f"{attempts} attempts: {json.dumps(errors)}"
    )


@contextlib.contextmanager
def wheelhouse_lock(wheelhouse_root: Path) -> Iterator[None]:
    """Serialize wheelhouse resolution across concurrent automation runs."""
    wheelhouse_root.mkdir(parents=True, exist_ok=True)
    lock_path = wheelhouse_root / ".bootstrap.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_stream:
        fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_stream.fileno(), fcntl.LOCK_UN)


def validate_venv_target(venv_path: Path, wheelhouse_root: Path) -> Path:
    """Reject broad or unrelated targets before allowing a clear rebuild."""
    resolved = venv_path.resolve()
    forbidden = {
        Path("/").resolve(),
        Path.home().resolve(),
        Path("/workspace").resolve(),
        wheelhouse_root.resolve(),
    }
    if resolved in forbidden:
        raise BootstrapError(f"Unsafe virtual environment target: {resolved}")
    if resolved.exists():
        if resolved.is_symlink():
            raise BootstrapError("Virtual environment target is a symlink")
        if not (resolved / SAFE_VENV_MARKER).is_file():
            raise BootstrapError(
                "Existing target is not a recognized virtual environment: "
                f"{resolved}"
            )
    return resolved


def create_clean_environment(
    venv_path: Path,
    snapshot: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Create a fresh venv, install offline, and run import smoke checks."""
    builder = venv.EnvBuilder(
        clear=venv_path.exists(),
        with_pip=True,
        symlinks=True,
    )
    builder.create(venv_path)
    if os.name == "nt":
        environment_python = venv_path / "Scripts" / "python.exe"
    else:
        environment_python = venv_path / "bin" / "python"

    install_command = [
        str(environment_python),
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        str(snapshot),
        "--no-cache-dir",
        "--disable-pip-version-check",
        *manifest["root_requirements"],
    ]
    install_result = run_command(install_command, capture=True)
    if install_result.returncode != 0:
        raise BootstrapError(
            "Offline installation from verified wheels failed: "
            f"{install_result.stdout}{install_result.stderr}"
        )

    smoke_code = """
import importlib.metadata
import json
import platform
import subprocess

packages = [
    "neqsim",
    "nbformat",
    "ipython",
    "matplotlib",
    "pandas",
    "numpy",
    "cairosvg",
]
versions = {
    package: importlib.metadata.version(package)
    for package in packages
}
java = subprocess.run(
    ["java", "-version"],
    check=True,
    capture_output=True,
    text=True,
).stderr.splitlines()[0]
print(json.dumps({
    "python": platform.python_version(),
    "java": java,
    "packages": versions,
}))
"""
    smoke_result = run_command(
        [str(environment_python), "-c", smoke_code],
        capture=True,
    )
    if smoke_result.returncode != 0:
        raise BootstrapError(
            "Validation environment smoke check failed: "
            f"{smoke_result.stdout}{smoke_result.stderr}"
        )
    smoke = json.loads(smoke_result.stdout)
    if (
        smoke["packages"]["neqsim"]
        != manifest["resolved_neqsim_version"]
    ):
        raise BootstrapError("Installed NeqSim version does not match manifest")

    return {
        "python": str(environment_python),
        "install_command": install_command,
        "smoke_check": smoke,
    }


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--venv",
        type=Path,
        required=True,
        help="Fresh virtual environment to create or safely rebuild.",
    )
    parser.add_argument(
        "--wheelhouse-root",
        type=Path,
        default=Path(
            os.environ.get(
                "NEQSIM_WHEELHOUSE_ROOT",
                "/workspace/.cache/neqsim-validation-wheelhouse",
            )
        ),
    )
    parser.add_argument(
        "--neqsim-version",
        default="latest",
        help="Exact version or 'latest'.",
    )
    parser.add_argument(
        "--extra-package",
        action="append",
        dest="extra_packages",
        default=[],
        help="Additional root package needed by validation.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Attempt a new public-PyPI resolution before local fallback.",
    )
    parser.add_argument(
        "--require-online-resolution",
        action="store_true",
        help="Fail instead of falling back when a refresh cannot reach PyPI.",
    )
    parser.add_argument(
        "--download-attempts",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--initial-backoff-seconds",
        type=float,
        default=5.0,
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=60,
    )
    return parser.parse_args()


def main() -> int:
    """Run the resilient bootstrap workflow."""
    arguments = parse_arguments()
    extras = list(dict.fromkeys([*DEFAULT_PACKAGES, *arguments.extra_packages]))
    wheelhouse_root = arguments.wheelhouse_root.resolve()
    venv_path = validate_venv_target(arguments.venv, wheelhouse_root)
    selected = None
    resolution_mode = None
    refresh_error = None

    with wheelhouse_lock(wheelhouse_root):
        existing = select_verified_snapshot(
            wheelhouse_root,
            arguments.neqsim_version,
            extras,
        )
        if arguments.refresh or existing is None:
            try:
                selected = download_snapshot(
                    wheelhouse_root,
                    arguments.neqsim_version,
                    extras,
                    arguments.download_attempts,
                    arguments.initial_backoff_seconds,
                    arguments.timeout_seconds,
                )
                resolution_mode = "online-new-snapshot"
            except BootstrapError as error:
                refresh_error = str(error)
                if arguments.require_online_resolution or existing is None:
                    raise
                selected = existing
                resolution_mode = "verified-snapshot-fallback"
        else:
            selected = existing
            resolution_mode = "verified-snapshot-reuse"

    if selected is None:
        raise BootstrapError("No verified wheel snapshot was selected")
    snapshot, manifest = selected
    environment = create_clean_environment(
        venv_path,
        snapshot,
        manifest,
    )
    summary = {
        "status": "passed",
        "fresh_environment": True,
        "pip_cache_disabled": True,
        "network_required_for_install": False,
        "wheel_hashes_verified": True,
        "resolution_mode": resolution_mode,
        "refresh_error": refresh_error,
        "wheelhouse_snapshot": str(snapshot),
        "wheel_count": len(manifest["wheels"]),
        "manifest_created_at_utc": manifest["created_at_utc"],
        "artifact_origin": manifest["artifact_origin"],
        "source_index": manifest["source_index"],
        "resolved_neqsim_version": manifest[
            "resolved_neqsim_version"
        ],
        "environment": environment,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BootstrapError as error:
        is_transient = isinstance(error, TransientBootstrapError)
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "transient": is_transient,
                    "error": str(error),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(75 if is_transient else 1)
