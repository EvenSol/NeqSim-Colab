import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import bootstrap_neqsim_validation_env as bootstrap


def create_test_wheel(
    directory: Path,
    project: str,
    version: str,
) -> Path:
    wheel_name = f"{project}-{version}-py3-none-any.whl"
    wheel_path = directory / wheel_name
    metadata_path = f"{project}-{version}.dist-info/METADATA"
    with zipfile.ZipFile(wheel_path, "w") as archive:
        archive.writestr(
            metadata_path,
            f"Metadata-Version: 2.1\nName: {project}\nVersion: {version}\n",
        )
    return wheel_path


class BootstrapManifestTest(unittest.TestCase):
    def test_snapshot_hash_verification_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            snapshot = Path(temp_directory)
            create_test_wheel(snapshot, "neqsim", "3.16.0")
            create_test_wheel(snapshot, "numpy", "2.5.1")
            bootstrap.write_manifest(
                snapshot,
                "3.16.0",
                ["numpy"],
                ["python", "-m", "pip", "download"],
            )

            manifest = bootstrap.load_and_verify_manifest(snapshot)
            self.assertEqual(
                manifest["resolved_neqsim_version"],
                "3.16.0",
            )

            wheel_path = next(snapshot.glob("neqsim-*.whl"))
            wheel_path.write_bytes(wheel_path.read_bytes() + b"tampered")
            with self.assertRaises(bootstrap.BootstrapError):
                bootstrap.load_and_verify_manifest(snapshot)

    def test_duplicate_wheel_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            snapshot = Path(temp_directory)
            first = create_test_wheel(snapshot, "neqsim", "3.16.0")
            duplicate = snapshot / "neqsim-3.16.0-1-py3-none-any.whl"
            duplicate.write_bytes(first.read_bytes())
            with self.assertRaises(bootstrap.BootstrapError):
                bootstrap.wheel_records(snapshot)

    def test_manifest_is_public_pypi_provenance(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            snapshot = Path(temp_directory)
            create_test_wheel(snapshot, "neqsim", "3.16.0")
            manifest = bootstrap.write_manifest(
                snapshot,
                "latest",
                [],
                ["python", "-m", "pip", "download"],
            )
            self.assertEqual(
                manifest["source_index"],
                bootstrap.PUBLIC_PYPI_INDEX,
            )
            self.assertTrue(manifest["pip_cache_disabled"])
            parsed = json.loads(
                (snapshot / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(parsed["artifact_origin"], "public-pypi")

    def test_existing_non_venv_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            target = root / "not-a-venv"
            target.mkdir()
            with self.assertRaises(bootstrap.BootstrapError):
                bootstrap.validate_venv_target(
                    target,
                    root / "wheelhouse",
                )

    def test_snapshot_selection_requires_all_root_packages(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            wheelhouse_root = Path(temp_directory)
            snapshot = (
                wheelhouse_root
                / f"schema-{bootstrap.SCHEMA_VERSION}"
                / bootstrap.runtime_key()
                / "neqsim-3.16.0"
                / "snapshot"
            )
            snapshot.mkdir(parents=True)
            create_test_wheel(snapshot, "neqsim", "3.16.0")
            create_test_wheel(snapshot, "numpy", "2.5.1")
            bootstrap.write_manifest(
                snapshot,
                "3.16.0",
                ["numpy"],
                ["python", "-m", "pip", "download"],
            )

            selected = bootstrap.select_verified_snapshot(
                wheelhouse_root,
                "3.16.0",
                ["numpy"],
            )
            self.assertIsNotNone(selected)
            missing_extra = bootstrap.select_verified_snapshot(
                wheelhouse_root,
                "3.16.0",
                ["numpy", "cairosvg"],
            )
            self.assertIsNone(missing_extra)

    def test_only_network_resolution_error_is_marked_transient(self):
        transient = bootstrap.TransientBootstrapError("network")
        permanent = bootstrap.BootstrapError("unsafe target")
        self.assertIsInstance(transient, bootstrap.BootstrapError)
        self.assertNotIsInstance(
            permanent,
            bootstrap.TransientBootstrapError,
        )


if __name__ == "__main__":
    unittest.main()
