"""Governed data helpers for the Northern Lights NeqSim notebook series.

The bundled CSV files are small, licensed snapshots used for reproducible
teaching. They are not a replacement for the full Equinor Northern Lights
Databricks Marketplace package. The formation table is an external
interpretation derived from that package and must not be presented as a raw
operator record.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


MARKETPLACE_URL = (
    "https://marketplace.databricks.com/details/"
    "ea296770-0ee0-4b74-a202-a2c0873add7c/"
    "Equinor-ASA_Northern-Lights"
)
EQUINOR_DISCLOSURE_URL = (
    "https://www.equinor.com/news/archive/20201019-sharing-data-northern-lights"
)
SODIR_EOS_URL = (
    "https://factpages.sodir.no/en/storage/PageView/Wellbores/All/8951"
)
SNAPSHOT_REPOSITORY = (
    "https://github.com/GeoArkadeep/"
    "supporting-data-for-EOS-Northern-Lights"
)
SNAPSHOT_COMMIT = "4d24c01cb893a3d80d1c4e25a3dde0ebbf178839"
DATA_LICENSE_URL = (
    "https://github.com/GeoArkadeep/"
    "supporting-data-for-EOS-Northern-Lights/blob/main/LICENSE"
)
MODULE_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = MODULE_DIR / "data"

EXPECTED_SNAPSHOT_SHA256 = {
    "31_5-7_Image.csv": (
        "1a3cf3d79d7644c1d3471cc35ea723fd3d75f00fe0cc9b1c161eef56805e26a7"
    ),
    "Deviation.csv": (
        "2a5758a50acb3f806069d4c379f7f06bcced04fdbd7d3d091d1fdc26fc51ee83"
    ),
    "NorthernLights-31_5-7.csv": (
        "db5611c7e0b2351cc3edefee99be92951ca383732768196f19c8d4f8aa998e2a"
    ),
    "UCSdata.csv": (
        "780f451f1a2808c5a7518974efc5b1f2c9dce153e33c8c49823d83e8577c6442"
    ),
}


@dataclass(frozen=True)
class NorthernLightsSource:
    """Resolved input boundary without storing or exposing credentials."""

    mode: str
    root: str
    authoritative_boundary: str
    measured_or_interpreted_data_loaded: bool
    claim_boundary: str


def file_sha256(path: Path, block_size: int = 1024 * 1024) -> str:
    """Return a SHA-256 digest without retaining file contents in memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def verify_snapshot_hashes() -> pd.DataFrame:
    """Verify every bundled snapshot and return a traceable manifest."""

    rows: list[dict[str, object]] = []
    for name, expected in EXPECTED_SNAPSHOT_SHA256.items():
        path = SNAPSHOT_DIR / name
        actual = file_sha256(path)
        rows.append(
            {
                "file": name,
                "bytes": path.stat().st_size,
                "sha256": actual,
                "hash_matches": actual == expected,
                "origin_commit": SNAPSHOT_COMMIT,
                "evidence_class": (
                    "external interpretation"
                    if name in {"NorthernLights-31_5-7.csv", "UCSdata.csv"}
                    else "licensed open snapshot"
                ),
            }
        )
    result = pd.DataFrame(rows)
    if not result["hash_matches"].all():
        failed = result.loc[~result["hash_matches"], "file"].tolist()
        raise RuntimeError(f"Northern Lights snapshot hash mismatch: {failed}")
    return result


def resolve_source() -> NorthernLightsSource:
    """Resolve the reproducible snapshot or a local Marketplace volume.

    ``open-snapshot`` is the default because it is credential-free and can be
    executed in Colab and CI. ``marketplace`` requires an explicitly mounted or
    exported volume and never falls back silently.
    """

    requested = os.environ.get(
        "NORTHERN_LIGHTS_DATA_MODE", "open-snapshot"
    ).strip().lower()
    if requested == "open-snapshot":
        return NorthernLightsSource(
            mode="open-snapshot",
            root=str(SNAPSHOT_DIR),
            authoritative_boundary=MARKETPLACE_URL,
            measured_or_interpreted_data_loaded=True,
            claim_boundary=(
                "Small licensed and interpreted Eos snapshots only; full raw "
                "logs, pressure, fluid, core, and well-test files are not loaded."
            ),
        )
    if requested != "marketplace":
        raise ValueError(
            "NORTHERN_LIGHTS_DATA_MODE must be 'open-snapshot' or 'marketplace'."
        )
    root_text = os.environ.get("NORTHERN_LIGHTS_VOLUME_ROOT", "").strip()
    if not root_text:
        raise RuntimeError(
            "Marketplace mode requires NORTHERN_LIGHTS_VOLUME_ROOT to point "
            "to an installed, mounted, or exported Marketplace volume."
        )
    root = Path(root_text).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Marketplace volume does not exist: {root}")
    return NorthernLightsSource(
        mode="marketplace-local-volume",
        root=str(root),
        authoritative_boundary=MARKETPLACE_URL,
        measured_or_interpreted_data_loaded=True,
        claim_boundary=(
            "Files below the explicitly supplied Marketplace volume may be "
            "inventoried; no credentials or full package are retained."
        ),
    )


def source_table(source: NorthernLightsSource) -> pd.DataFrame:
    """Return the reader-facing source and claim boundary."""

    items = asdict(source)
    return pd.DataFrame(
        {"item": list(items), "value": [items[key] for key in items]}
    )


def _load_deviation(path: Path) -> pd.DataFrame:
    columns = [
        "MD_m",
        "inclination_deg",
        "azimuth_deg",
        "TVD_m",
        "x_offset_m",
        "y_offset_m",
        "UTM_easting_m",
        "UTM_northing_m",
        "dogleg_deg_per_30m",
        "empty",
    ]
    table = pd.read_csv(path, skiprows=1, header=None, names=columns)
    table = table.drop(columns="empty")
    return table.apply(pd.to_numeric, errors="raise")


def load_snapshot_tables() -> dict[str, pd.DataFrame]:
    """Load and normalize the four bundled licensed snapshot files."""

    verify_snapshot_hashes()
    deviation = _load_deviation(SNAPSHOT_DIR / "Deviation.csv")
    formations = pd.read_csv(
        SNAPSHOT_DIR / "NorthernLights-31_5-7.csv", encoding="utf-8-sig"
    )
    formations = formations.rename(
        columns={
            "Top TVD": "top_tvd_m",
            "Formation Name": "formation",
            "Struc.Top": "structural_top_m",
            "Struc.Bottom": "structural_bottom_m",
            "GR Cut": "gr_cut_api",
        }
    )
    numeric_columns = [
        "top_tvd_m",
        "structural_top_m",
        "structural_bottom_m",
        "gr_cut_api",
    ]
    for column in numeric_columns:
        formations[column] = pd.to_numeric(
            formations[column], errors="coerce"
        )
    formations["thickness_m"] = (
        formations["structural_bottom_m"] - formations["structural_top_m"]
    )
    formations["family"] = np.select(
        [
            formations["formation"].str.contains("Drake", case=False),
            formations["formation"].str.contains("Cook", case=False),
            formations["formation"].str.contains("Johansen", case=False),
        ],
        ["Drake seal", "Cook reservoir", "Johansen reservoir"],
        default="other",
    )
    ucs = pd.read_csv(
        SNAPSHOT_DIR / "UCSdata.csv",
        header=None,
        names=["depth_m", "ucs_mpa"],
    )
    image_markers = pd.read_csv(SNAPSHOT_DIR / "31_5-7_Image.csv")
    return {
        "deviation": deviation,
        "formations": formations,
        "ucs": ucs,
        "image_markers": image_markers,
    }


def classify_marketplace_asset(relative_path: str) -> str:
    """Conservatively classify a Marketplace asset from its path."""

    text = relative_path.lower()
    rules: list[tuple[Iterable[str], str]] = [
        (("dlis", "las", "wireline", "log"), "well logs"),
        (("core", "rcal", "scal", "rock"), "core and rock"),
        (("pressure", "mdt", "xpt", "dst", "well_test"), "pressure and test"),
        (("fluid", "pvt", "sample"), "fluid data"),
        (("trajectory", "deviation", "wellpath", "directional"), "trajectory"),
        (("seismic", "sgy", "segy"), "seismic"),
        (("formation", "top", "strat"), "stratigraphy"),
        (("report", "pdf"), "report"),
    ]
    for terms, label in rules:
        if any(term in text for term in terms):
            return label
    return "other"


def inventory_local_volume(
    root: Path, maximum_files: int = 30000
) -> pd.DataFrame:
    """Inventory an explicit local Marketplace export without copying it."""

    rows: list[dict[str, object]] = []
    for index, path in enumerate(sorted(root.rglob("*"))):
        if index >= maximum_files:
            break
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            rows.append(
                {
                    "relative_path": relative,
                    "suffix": path.suffix.lower(),
                    "bytes": path.stat().st_size,
                    "domain": classify_marketplace_asset(relative),
                }
            )
    if not rows:
        raise RuntimeError(f"No files found below Marketplace root {root}")
    return pd.DataFrame(rows)

