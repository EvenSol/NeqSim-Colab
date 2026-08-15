"""Shared data, lineage, and engineering helpers for the Volve notebook series.

The module never downloads the full Volve package. It either reads an installed
Databricks Marketplace volume or creates an explicitly labelled, deterministic
teaching fixture for clean notebook validation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Iterable

import numpy as np
import pandas as pd


MARKETPLACE_URL = (
    "https://marketplace.databricks.com/details/"
    "5c3558ef-315c-44dd-baef-7062ac301f22/"
    "Equinor-ASA_Volve-Data-Village"
)
EQUINOR_DATA_URL = "https://www.equinor.com/energy/volve-data-sharing"
EQUINOR_LICENSE_URL = (
    "https://www.equinor.com/content/dam/statoil/documents/"
    "what-we-do/Equinor-HRS-Terms-and-conditions-for-licence-to-data-Volve.pdf"
)
NEQSIM_REPOSITORY = "https://github.com/equinor/neqsim"
SERIES_SCHEMA_VERSION = "1.0"
RANDOM_SEED = 20260815
SECONDS_PER_DAY = 86400.0


@dataclass(frozen=True)
class VolveSource:
    """Describe one resolved input boundary without retaining credentials."""

    mode: str
    marketplace_url: str
    volume_root: str | None
    credential_route: str
    measured_data_loaded: bool
    limitation: str


def _colab_secret(name: str) -> str | None:
    """Read a Colab secret when available without printing its value."""

    try:
        from google.colab import userdata
    except ImportError:
        return None
    try:
        value = userdata.get(name)
    except Exception:
        return None
    return value or None


def secret_value(name: str) -> str | None:
    """Resolve a secret from the environment or Colab secret storage."""

    return os.environ.get(name) or _colab_secret(name)


def resolve_source() -> VolveSource:
    """Resolve Marketplace, downloaded-volume, or deterministic teaching mode."""

    validation_mode = os.environ.get("VOLVE_VALIDATION_MODE") == "1"
    default_mode = "demo" if validation_mode else "marketplace"
    requested_mode = os.environ.get("VOLVE_DATA_MODE", default_mode).strip().lower()
    local_root_text = os.environ.get("VOLVE_VOLUME_ROOT", "").strip()
    remote_root_text = os.environ.get("VOLVE_REMOTE_VOLUME_ROOT", "").strip()
    local_root = Path(local_root_text).expanduser() if local_root_text else None

    if requested_mode == "marketplace" and local_root and local_root.exists():
        return VolveSource(
            mode="marketplace-local-volume",
            marketplace_url=MARKETPLACE_URL,
            volume_root=str(local_root.resolve()),
            credential_route="Databricks volume mounted or exported locally",
            measured_data_loaded=True,
            limitation="Files are selected from the installed Marketplace volume.",
        )
    if requested_mode == "marketplace" and remote_root_text:
        has_auth = bool(secret_value("DATABRICKS_HOST"))
        has_auth = has_auth and bool(secret_value("DATABRICKS_TOKEN"))
        if has_auth:
            return VolveSource(
                mode="marketplace-remote-volume",
                marketplace_url=MARKETPLACE_URL,
                volume_root=remote_root_text,
                credential_route="Databricks SDK with Colab or environment secrets",
                measured_data_loaded=True,
                limitation="Only explicitly selected volume files are downloaded.",
            )
        raise RuntimeError(
            "Marketplace mode needs DATABRICKS_HOST and DATABRICKS_TOKEN "
            "as secrets, or an existing VOLVE_VOLUME_ROOT."
        )
    if requested_mode == "marketplace":
        raise RuntimeError(
            "Marketplace mode needs VOLVE_REMOTE_VOLUME_ROOT plus Databricks "
            "secrets, or an existing VOLVE_VOLUME_ROOT."
        )
    if requested_mode not in {"demo", "marketplace"}:
        raise ValueError("VOLVE_DATA_MODE must be 'demo' or 'marketplace'.")
    return VolveSource(
        mode="demonstration-fallback",
        marketplace_url=MARKETPLACE_URL,
        volume_root=None,
        credential_route="none",
        measured_data_loaded=False,
        limitation=(
            "Deterministic teaching fixtures are used. Results are not measured "
            "Volve values and are not a history match."
        ),
    )


def source_table(source: VolveSource) -> pd.DataFrame:
    """Return a reader-facing source and claim-boundary table."""

    return pd.DataFrame(
        {
            "item": [
                "resolved mode",
                "Marketplace listing",
                "volume root",
                "credentials",
                "measured Volve data loaded",
                "claim boundary",
            ],
            "value": [
                source.mode,
                source.marketplace_url,
                source.volume_root or "not mounted",
                source.credential_route,
                source.measured_data_loaded,
                source.limitation,
            ],
        }
    )


def file_sha256(path: Path, block_size: int = 1024 * 1024) -> str:
    """Calculate a file digest without loading a large asset into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def classify_inventory(inventory: pd.DataFrame) -> pd.DataFrame:
    """Classify Volve assets conservatively from names and extensions."""

    classified = inventory.copy()
    path_text = classified["relative_path"].str.lower()
    suffix = classified["suffix"].str.lower()
    conditions = [
        suffix.isin([".sgy", ".segy"]),
        suffix.isin([".las", ".dlis"]),
        suffix.isin([".data", ".egrid", ".grdecl", ".unrst", ".init"]),
        suffix.isin([".xlsx", ".xls", ".csv"])
        & path_text.str.contains("prod|inject|allocation|daily|monthly"),
        path_text.str.contains("trajector|deviation|survey|wellpath"),
        path_text.str.contains("pvt|fluid|composition|sample"),
        path_text.str.contains("tops|horizon|surface|grid"),
        path_text.str.contains("facility|process|separator|compressor|platform"),
        suffix.eq(".pdf"),
    ]
    labels = [
        "seismic",
        "well-log",
        "reservoir-model",
        "production-history",
        "well-trajectory",
        "pvt",
        "static-model",
        "facilities-document",
        "report",
    ]
    classified["domain"] = np.select(conditions, labels, default="other")
    return classified


def inventory_local_volume(
    root: Path,
    *,
    maximum_entries: int = 20000,
) -> pd.DataFrame:
    """Inventory a mounted or downloaded Marketplace volume."""

    root = root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Volve volume root does not exist: {root}")
    rows: list[dict[str, object]] = []
    for index, path in enumerate(sorted(root.rglob("*"))):
        if index >= maximum_entries:
            break
        if not path.is_file():
            continue
        rows.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "suffix": path.suffix.lower(),
                "bytes": path.stat().st_size,
            }
        )
    if not rows:
        raise RuntimeError(f"No files were found below {root}.")
    return classify_inventory(pd.DataFrame(rows))


def demonstration_inventory() -> pd.DataFrame:
    """Return a synthetic manifest whose paths explain the expected interfaces."""

    rows = [
        ("Seismic/ST0202/stacked_volume.sgy", ".sgy", 3_200_000_000),
        ("Well_logs/15_9-F-1_C/composite.las", ".las", 4_200_000),
        ("Well_logs/15_9-F-14/formation_eval.dlis", ".dlis", 320_000_000),
        ("Reservoir_model/VOLVE.DATA", ".data", 1_800_000),
        ("Reservoir_model/VOLVE.EGRID", ".egrid", 210_000_000),
        ("Reservoir_model/VOLVE.UNRST", ".unrst", 2_700_000_000),
        ("Production/volve_daily_production.xlsx", ".xlsx", 2_400_000),
        ("Wells/well_trajectories.csv", ".csv", 640_000),
        ("PVT/representative_fluid_composition.xlsx", ".xlsx", 120_000),
        ("Static_model/top_hugin_surface.txt", ".txt", 8_500_000),
        ("Facilities/process_description.pdf", ".pdf", 5_300_000),
    ]
    inventory = pd.DataFrame(
        rows,
        columns=["relative_path", "suffix", "bytes"],
    )
    return classify_inventory(inventory)


def remote_volume_client():
    """Create an authenticated Databricks client without logging secrets."""

    try:
        from databricks.sdk import WorkspaceClient
    except ImportError as error:
        raise RuntimeError(
            "Install databricks-sdk before reading a remote Marketplace volume."
        ) from error
    host = secret_value("DATABRICKS_HOST")
    token = secret_value("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError("Databricks host and token secrets are required.")
    return WorkspaceClient(host=host, token=token)


def list_remote_directory(
    remote_root: str,
    *,
    maximum_entries: int = 20000,
) -> pd.DataFrame:
    """Recursively list a volume with a bounded breadth-first walk."""

    client = remote_volume_client()
    queue = [remote_root.rstrip("/")]
    rows: list[dict[str, object]] = []
    while queue and len(rows) < maximum_entries:
        current = queue.pop(0)
        for entry in client.files.list_directory_contents(current):
            path = str(entry.path)
            if entry.is_directory:
                queue.append(path)
                continue
            rows.append(
                {
                    "relative_path": path.removeprefix(remote_root).lstrip("/"),
                    "suffix": Path(path).suffix.lower(),
                    "bytes": int(entry.file_size or 0),
                    "remote_path": path,
                }
            )
            if len(rows) >= maximum_entries:
                break
    if not rows:
        raise RuntimeError(f"No files were found in {remote_root}.")
    return classify_inventory(pd.DataFrame(rows))


def download_remote_file(remote_path: str, local_path: Path) -> Path:
    """Download one selected volume file; never recurse or bulk-download."""

    client = remote_volume_client()
    local_path.parent.mkdir(parents=True, exist_ok=True)
    client.files.download_to(remote_path, str(local_path))
    return local_path


def select_asset(
    inventory: pd.DataFrame,
    domain: str,
    *,
    environment_name: str,
) -> str:
    """Select an explicit path or a single unambiguous domain candidate."""

    explicit = os.environ.get(environment_name, "").strip()
    candidates = inventory.loc[
        inventory["domain"].eq(domain),
        "relative_path",
    ].tolist()
    if explicit:
        if explicit not in inventory["relative_path"].tolist():
            raise FileNotFoundError(
                f"{environment_name}={explicit!r} is not in the Marketplace manifest."
            )
        return explicit
    if len(candidates) == 1:
        return candidates[0]
    preview = "\n".join(f"- {path}" for path in candidates[:20])
    raise RuntimeError(
        f"Set {environment_name}; found {len(candidates)} candidates:\n{preview}"
    )


def demo_seismic(
    *,
    inline_count: int = 36,
    crossline_count: int = 44,
    sample_count: int = 220,
) -> dict[str, np.ndarray]:
    """Create a deterministic faulted post-stack cube with known horizons."""

    random = np.random.default_rng(RANDOM_SEED)
    inline = np.arange(inline_count)
    crossline = np.arange(crossline_count)
    time_ms = np.arange(sample_count, dtype=float) * 4.0 + 1400.0
    ii, xx = np.meshgrid(inline, crossline, indexing="ij")
    top_ms = (
        1770.0
        + 0.8 * (ii - inline_count / 2.0)
        + 0.45 * (xx - crossline_count / 2.0)
        + 15.0 * np.sin(ii / 7.0)
    )
    fault_mask = xx > crossline_count * 0.56
    top_ms = top_ms + fault_mask * 28.0
    thickness_ms = 42.0 + 7.0 * np.cos(xx / 6.0) + 4.0 * np.sin(ii / 5.0)
    base_ms = top_ms + thickness_ms
    cube = random.normal(0.0, 0.035, (inline_count, crossline_count, sample_count))
    wavelet_samples = np.arange(-12, 13)
    wavelet = (
        1.0 - 2.0 * (math.pi * 0.22 * wavelet_samples) ** 2
    ) * np.exp(-(math.pi * 0.22 * wavelet_samples) ** 2)
    for inline_index in range(inline_count):
        for crossline_index in range(crossline_count):
            top_index = int(round((top_ms[inline_index, crossline_index] - 1400.0) / 4.0))
            base_index = int(
                round((base_ms[inline_index, crossline_index] - 1400.0) / 4.0)
            )
            for event_index, polarity in [(top_index, -0.75), (base_index, 0.55)]:
                start = event_index - len(wavelet) // 2
                stop = start + len(wavelet)
                if start >= 0 and stop <= sample_count:
                    cube[inline_index, crossline_index, start:stop] += (
                        polarity * wavelet
                    )
    return {
        "cube": cube.astype(np.float32),
        "inline": inline,
        "crossline": crossline,
        "time_ms": time_ms,
        "top_ms": top_ms,
        "base_ms": base_ms,
        "thickness_ms": thickness_ms,
    }


def demo_well_logs() -> pd.DataFrame:
    """Create deterministic multiwell petrophysical teaching curves."""

    random = np.random.default_rng(RANDOM_SEED + 1)
    well_names = ["15/9-F-1 C", "15/9-F-11 B", "15/9-F-14"]
    rows: list[pd.DataFrame] = []
    for well_index, well_name in enumerate(well_names):
        depth_m = np.arange(2700.0, 3060.0, 0.5)
        reservoir = (depth_m > 2870.0 + 8.0 * well_index) & (
            depth_m < 2970.0 + 5.0 * well_index
        )
        gamma_ray_api = 92.0 - 55.0 * reservoir
        gamma_ray_api += 8.0 * np.sin(depth_m / 7.0)
        gamma_ray_api += random.normal(0.0, 3.0, len(depth_m))
        porosity_fraction = 0.10 + 0.15 * reservoir
        porosity_fraction += random.normal(0.0, 0.012, len(depth_m))
        porosity_fraction = np.clip(porosity_fraction, 0.04, 0.34)
        water_saturation = 0.78 - 0.53 * reservoir
        water_saturation += 0.07 * np.sin(depth_m / 11.0)
        water_saturation = np.clip(water_saturation, 0.12, 1.0)
        density_kg_m3 = 2650.0 - 1050.0 * porosity_fraction
        vp_m_s = 5200.0 - 5600.0 * porosity_fraction
        vp_m_s += 350.0 * water_saturation
        vs_m_s = 0.57 * vp_m_s - 250.0
        permeability_md = 0.03 * (porosity_fraction / 0.08) ** 6
        rows.append(
            pd.DataFrame(
                {
                    "well": well_name,
                    "md_m": depth_m,
                    "gamma_ray_api": gamma_ray_api,
                    "porosity_fraction": porosity_fraction,
                    "water_saturation_fraction": water_saturation,
                    "density_kg_m3": density_kg_m3,
                    "vp_m_s": vp_m_s,
                    "vs_m_s": vs_m_s,
                    "permeability_md": permeability_md,
                    "data_status": "DEMONSTRATION_FALLBACK",
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def demo_production_history() -> pd.DataFrame:
    """Create deterministic monthly rates with Volve-style well identifiers."""

    dates = pd.date_range("2008-02-01", "2016-09-01", freq="MS")
    well_names = [
        "15/9-F-1 C",
        "15/9-F-11 B",
        "15/9-F-12",
        "15/9-F-14",
        "15/9-F-15 D",
    ]
    rows: list[dict[str, object]] = []
    for well_index, well_name in enumerate(well_names):
        start_index = 2 + well_index * 4
        for month_index, date in enumerate(dates):
            active_month = month_index - start_index
            if active_month < 0:
                oil_rate = gas_rate = water_rate = 0.0
            else:
                ramp = min(active_month / 5.0, 1.0)
                decline = math.exp(-0.020 * max(active_month - 5, 0))
                uptime = 0.90 + 0.07 * math.sin((month_index + well_index) / 4.0)
                oil_rate = (1050.0 - 80.0 * well_index) * ramp * decline * uptime
                water_cut = 0.08 + 0.78 / (
                    1.0 + math.exp(-(active_month - 48.0) / 10.0)
                )
                water_rate = oil_rate * water_cut / max(1.0 - water_cut, 0.05)
                gor = 120.0 + 110.0 / (
                    1.0 + math.exp(-(active_month - 60.0) / 8.0)
                )
                gas_rate = oil_rate * gor
            rows.append(
                {
                    "date": date,
                    "well": well_name,
                    "oil_rate_Sm3_day": oil_rate,
                    "gas_rate_Sm3_day": gas_rate,
                    "water_rate_Sm3_day": water_rate,
                    "on_stream_fraction": min(max(oil_rate / 1000.0, 0.0), 1.0),
                    "data_status": "DEMONSTRATION_FALLBACK",
                }
            )
    return pd.DataFrame(rows)


def demo_well_trajectories() -> pd.DataFrame:
    """Create simple platform-well trajectories for SURF and well examples."""

    rows: list[dict[str, object]] = []
    well_names = [
        "15/9-F-1 C",
        "15/9-F-11 B",
        "15/9-F-12",
        "15/9-F-14",
        "15/9-F-15 D",
    ]
    for well_index, well_name in enumerate(well_names):
        measured_depth = np.linspace(0.0, 3800.0 + 120.0 * well_index, 80)
        build = np.clip((measured_depth - 1200.0) / 1800.0, 0.0, 1.0)
        inclination_deg = (55.0 + 4.0 * well_index) * build
        tvd_m = np.cumsum(
            np.cos(np.deg2rad(inclination_deg))
            * np.gradient(measured_depth)
        )
        horizontal_m = np.cumsum(
            np.sin(np.deg2rad(inclination_deg))
            * np.gradient(measured_depth)
        )
        azimuth_rad = np.deg2rad(35.0 + 26.0 * well_index)
        rows.extend(
            {
                "well": well_name,
                "md_m": md,
                "tvd_m": tvd,
                "east_m": horizontal * math.sin(azimuth_rad),
                "north_m": horizontal * math.cos(azimuth_rad),
                "inclination_deg": inclination,
                "data_status": "DEMONSTRATION_FALLBACK",
            }
            for md, tvd, horizontal, inclination in zip(
                measured_depth,
                tvd_m,
                horizontal_m,
                inclination_deg,
            )
        )
    return pd.DataFrame(rows)


def field_monthly_history(production: pd.DataFrame) -> pd.DataFrame:
    """Aggregate well history and calculate field water cut and GOR."""

    field = (
        production.groupby("date", as_index=False)[
            ["oil_rate_Sm3_day", "gas_rate_Sm3_day", "water_rate_Sm3_day"]
        ]
        .sum()
        .sort_values("date")
    )
    field["liquid_rate_Sm3_day"] = (
        field["oil_rate_Sm3_day"] + field["water_rate_Sm3_day"]
    )
    field["water_cut_fraction"] = field["water_rate_Sm3_day"] / field[
        "liquid_rate_Sm3_day"
    ].replace(0.0, np.nan)
    field["gor_Sm3_Sm3"] = field["gas_rate_Sm3_day"] / field[
        "oil_rate_Sm3_day"
    ].replace(0.0, np.nan)
    return field.fillna(0.0)


def reservoir_screen(production: pd.DataFrame) -> pd.DataFrame:
    """Create a material-balance-style pressure and saturation handoff."""

    field = field_monthly_history(production)
    elapsed_days = (field["date"] - field["date"].min()).dt.days.to_numpy()
    oil_volume = np.cumsum(field["oil_rate_Sm3_day"].to_numpy() * 30.4375)
    water_volume = np.cumsum(field["water_rate_Sm3_day"].to_numpy() * 30.4375)
    initial_oil_in_place = 14.5e6
    depletion = oil_volume / initial_oil_in_place
    pressure_bara = 265.0 - 150.0 * depletion + 22.0 * water_volume / 16.0e6
    pressure_bara = np.maximum.accumulate(pressure_bara[::-1])[::-1]
    pressure_bara = np.clip(pressure_bara, 105.0, 265.0)
    field["elapsed_days"] = elapsed_days
    field["cumulative_oil_MSm3"] = oil_volume / 1.0e6
    field["cumulative_water_MSm3"] = water_volume / 1.0e6
    field["average_pressure_bara"] = pressure_bara
    field["recovery_fraction"] = depletion
    return field


def calculate_stoiip_distribution(sample_count: int = 5000) -> pd.DataFrame:
    """Propagate structural and petrophysical uncertainty to STOIIP."""

    random = np.random.default_rng(RANDOM_SEED + 2)
    gross_rock_volume_m3 = random.lognormal(
        mean=math.log(110.0e6),
        sigma=0.18,
        size=sample_count,
    )
    net_to_gross = np.clip(random.normal(0.72, 0.08, sample_count), 0.35, 0.95)
    porosity = np.clip(random.normal(0.23, 0.025, sample_count), 0.12, 0.34)
    water_saturation = np.clip(random.normal(0.27, 0.05, sample_count), 0.10, 0.55)
    oil_fvf = np.clip(random.normal(1.28, 0.05, sample_count), 1.12, 1.45)
    stoiip_sm3 = (
        gross_rock_volume_m3
        * net_to_gross
        * porosity
        * (1.0 - water_saturation)
        / oil_fvf
    )
    return pd.DataFrame(
        {
            "gross_rock_volume_m3": gross_rock_volume_m3,
            "net_to_gross_fraction": net_to_gross,
            "porosity_fraction": porosity,
            "water_saturation_fraction": water_saturation,
            "oil_fvf_rm3_Sm3": oil_fvf,
            "stoiip_MSm3": stoiip_sm3 / 1.0e6,
        }
    )


def write_contract(
    path: Path,
    payload: dict[str, object],
    source: VolveSource,
) -> Path:
    """Write a JSON handoff with explicit source and timestamp."""

    path.parent.mkdir(parents=True, exist_ok=True)
    contract = {
        "schema_version": SERIES_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": asdict(source),
        **payload,
    }
    path.write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def read_contract(path: Path) -> dict[str, object]:
    """Read and verify a handoff contract."""

    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("schema_version") != SERIES_SCHEMA_VERSION:
        raise RuntimeError(f"Unsupported handoff schema in {path}.")
    return contract


def normalize_well_name(name: str) -> str:
    """Normalize Volve-style well identifiers for joins."""

    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", str(name).upper()).strip("-")
    return cleaned.replace("NO-", "")


def relative_mass_residual(inlet_kg_s: float, outlets_kg_s: Iterable[float]) -> float:
    """Return a scale-safe process mass-balance residual."""

    outlet_sum = float(sum(outlets_kg_s))
    return (float(inlet_kg_s) - outlet_sum) / max(abs(float(inlet_kg_s)), 1.0e-12)
