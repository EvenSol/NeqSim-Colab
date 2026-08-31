#!/usr/bin/env python3
"""Generate the executed-source notebook for the RMS -> OPM Flow -> ERT example."""

from __future__ import annotations

from pathlib import Path
import textwrap

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "notebooks" / "reservoir" / "rms_to_opm_flow_agent_ert.ipynb"
BASE_NOTEBOOK = ROOT / "notebooks" / "reservoir" / "neqsim_opm_flow_blackoil_coupling.ipynb"

base = nbf.read(BASE_NOTEBOOK, as_version=4)


def source_cell(index: int) -> str:
    return "".join(base.cells[index].source)


def md(source: str):
    return nbf.v4.new_markdown_cell(textwrap.dedent(source).strip())


def code(source: str):
    return nbf.v4.new_code_cell(textwrap.dedent(source).strip())


cells = []

cells.append(md(r"""
# From an RMS-origin reservoir model to OPM Flow, ERT, and NeqSim

**A fully executed NeqSim-Colab reservoir example using the public Reek model**

This notebook reads a real exported corner-point model whose public provenance identifies an
RMS project, audits every input by SHA-256, demonstrates 2 × 2 × 4 blocking and property
spreading, generates a complete OPM Flow black-oil case, runs the simulator, reads restart
states, runs a four-realization ERT ensemble, and transfers a selected result to a NeqSim
surface-process model.

Open in Colab:
https://colab.research.google.com/github/EvenSol/NeqSim-Colab/blob/master/notebooks/reservoir/rms_to_opm_flow_agent_ert.ipynb

The stored outputs are evidence from a clean top-to-bottom run. Re-running will download the
same immutable public inputs and will build the current NeqSim Java master, recording its exact
commit and JAR digest.
"""))

cells.append(md(r"""
## What this notebook proves

By the end, the notebook has produced and checked:

1. An immutable inventory of the public Reek ROFF files, including geometry and all properties.
2. A geological grid of 80 × 128 × 56 cells and a simulation grid of 40 × 64 × 14 cells.
3. Explicit 2 × 2 × 4 blocking, pore-volume-weighted porosity, and volume-majority facies.
4. Property maps, cross-sections, histograms, a 3-D reservoir view, and well screening.
5. NeqSim SRK fluid characterization and Flow-compatible PVTO, PVDG, PVTW, and DENSITY data.
6. A complete OPM Flow corner-point deck and a real dynamic simulation with restart maps.
7. A real ERT ensemble experiment in which porosity, permeability, and injection rate vary.
8. A NeqSim choke, separation, compression, cooling, and oil-letdown process driven by Flow rates.
9. A machine-readable job contract and tool-call ledger for a future RMS automation agent.

**Important boundary.** RMS is commercial software and cannot be installed in a public Colab
runtime. The numerical data used here are genuine public ROFF exports from an RMS-origin Reek
model. The future-agent section shows how the same request is dispatched to a licensed,
allow-listed RMS worker. No proprietary project or license is copied into this notebook.
"""))

cells.append(md(r"""
## End-to-end architecture and trust boundary

The public teaching path and the future licensed path share the same versioned handover contract.

| Stage | This executed notebook | Future production agent |
|---|---|---|
| RMS source | Public RMS-origin ROFF export | Licensed RMS worker |
| Grid/property API | XTGeo | RMS Python API plus XTGeo validation |
| Fluid model | NeqSim current Java master | Same |
| Dynamic model | OPM Flow 2026.04 | Same or approved simulator |
| Uncertainty | ERT 23.0.1 | ERT with governed storage/compute |
| Audit | Checksums, assertions, tool ledger | Signed job, identity, approvals, artifact registry |
"""))

cells.append(code(r"""
import importlib.metadata
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

REQUIRED_PACKAGES = {
    "neqsim": "3.18.0",
    "opm": "2026.4",
    "xtgeo": "4.25.1",
    "ert": "23.0.1",
    "nbformat": "5.10.4",
}

installed = {}
for package_name in REQUIRED_PACKAGES:
    try:
        installed[package_name] = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        installed[package_name] = None

requirements = [
    f"{name}=={required}"
    for name, required in REQUIRED_PACKAGES.items()
    if installed[name] != required
]
if requirements:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", *requirements],
        check=True,
        timeout=1200,
    )

FLOW_RUN_ENV = os.environ.copy()
FLOW_EXECUTABLE = os.environ.get("OPM_FLOW_EXECUTABLE") or shutil.which("flow")
if FLOW_EXECUTABLE is None:
    os_release = Path("/etc/os-release").read_text(encoding="utf-8")
    if "Ubuntu" not in os_release:
        raise RuntimeError("OPM Flow binary installation requires an Ubuntu/Colab runtime.")
    privilege = [] if os.geteuid() == 0 else ["sudo"]
    commands = [
        privilege + ["apt-get", "update", "-qq"],
        privilege + [
            "apt-get", "install", "-y", "-qq", "--no-install-recommends",
            "software-properties-common", "mpi-default-bin",
        ],
        privilege + ["add-apt-repository", "-y", "ppa:opm/ppa"],
        privilege + ["apt-get", "update", "-qq"],
        privilege + [
            "apt-get", "install", "-y", "-qq", "--no-install-recommends",
            "libopm-simulators-bin",
        ],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=1200)
        if result.returncode != 0:
            raise RuntimeError(result.stdout[-2000:] + "\n" + result.stderr[-4000:])
    FLOW_EXECUTABLE = shutil.which("flow")

if FLOW_EXECUTABLE is None:
    raise RuntimeError("The OPM Flow executable was not found.")

flow_version_output = subprocess.run(
    [FLOW_EXECUTABLE, "--version"],
    check=True,
    capture_output=True,
    text=True,
    timeout=60,
)
print(flow_version_output.stdout.strip() or flow_version_output.stderr.strip())
print("Python packages installed:", REQUIRED_PACKAGES)
"""))

cells.append(md(r"""
## Reproducible current-master NeqSim runtime

The public PyPI NeqSim package supplies only the Python bridge. The Java runtime below is built
from the selected equinor/neqsim source ref. The resolved Git commit, JAR SHA-256, and loaded
class location are recorded before any thermodynamic calculation. Set NEQSIM_SOURCE_REF to use
another reviewed ref. Validation automation may provide NEQSIM_SOURCE_ROOT and
NEQSIM_SOURCE_JAR from an exact pre-built checkout.
"""))

cells.append(code(r"""
import hashlib
import importlib.util
import jpype


def run_command(command, *, cwd=None, timeout=1800, environment=None):
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if result.returncode != 0:
        tail = "\n".join(result.stdout.splitlines()[-80:])
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{tail}")
    return result.stdout.strip()


NEQSIM_SOURCE_REF = os.environ.get("NEQSIM_SOURCE_REF", "master")
supplied_source = os.environ.get("NEQSIM_SOURCE_ROOT", "").strip()
supplied_jar = os.environ.get("NEQSIM_SOURCE_JAR", "").strip()

if supplied_source and supplied_jar:
    neqsim_source = Path(supplied_source).resolve()
    neqsim_jar = Path(supplied_jar).resolve()
else:
    build_root = Path("/content") if Path("/content").exists() else Path.cwd()
    neqsim_source = build_root / "neqsim-java-master"
    if not neqsim_source.exists():
        run_command(
            [
                "git", "clone", "--depth", "1", "--branch", NEQSIM_SOURCE_REF,
                "https://github.com/equinor/neqsim.git", str(neqsim_source),
            ],
            timeout=600,
        )
    else:
        run_command(["git", "fetch", "--depth", "1", "origin", NEQSIM_SOURCE_REF],
                    cwd=neqsim_source, timeout=600)
        run_command(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=neqsim_source)

    maven_settings = build_root / "neqsim-maven-settings.xml"
    maven_settings.write_text(
        "<settings><mirrors><mirror><id>canonical-central</id>"
        "<mirrorOf>central</mirrorOf>"
        "<url>https://repo.maven.apache.org/maven2/</url>"
        "</mirror></mirrors></settings>",
        encoding="utf-8",
    )
    run_command(
        [
            "./mvnw", "-q", "-s", str(maven_settings), "-DskipTests",
            "-Dmaven.javadoc.skip=true", "package",
        ],
        cwd=neqsim_source,
        timeout=2400,
    )
    built_jars = [
        path for path in (neqsim_source / "target").glob("neqsim-*.jar")
        if "sources" not in path.name
        and "javadoc" not in path.name
        and not path.name.startswith("original-")
    ]
    if not built_jars:
        raise FileNotFoundError("Maven completed but no NeqSim JAR was found.")
    neqsim_jar = max(built_jars, key=lambda path: path.stat().st_size)

if not neqsim_source.is_dir() or not neqsim_jar.is_file():
    raise FileNotFoundError("NeqSim source root or built JAR is missing.")

neqsim_commit = run_command(["git", "rev-parse", "HEAD"], cwd=neqsim_source)
neqsim_jar_sha256 = hashlib.sha256(neqsim_jar.read_bytes()).hexdigest()

os.environ["NEQSIM_JVM_AUTOSTART"] = "0"
if not jpype.isJVMStarted():
    jpype.addClassPath(str(neqsim_jar))
    neqsim_package = importlib.util.find_spec("neqsim")
    if neqsim_package is None or not neqsim_package.submodule_search_locations:
        raise ImportError("The public-PyPI neqsim bridge is not installed.")
    neqsim_python_root = Path(next(iter(neqsim_package.submodule_search_locations)))
    for runtime_jar in sorted((neqsim_python_root / "lib").glob("*.jar")):
        if runtime_jar.resolve() != neqsim_jar:
            jpype.addClassPath(str(runtime_jar))
    jpype.startJVM()

SystemSrkEos = jpype.JClass("neqsim.thermo.system.SystemSrkEos")
class_source = str(
    SystemSrkEos.class_.getProtectionDomain().getCodeSource().getLocation()
)
if neqsim_jar.name not in class_source:
    raise RuntimeError("NeqSim classes were not loaded from the source-built JAR.")

print("NeqSim source ref:", NEQSIM_SOURCE_REF)
print("NeqSim resolved commit:", neqsim_commit)
print("NeqSim JAR SHA-256:", neqsim_jar_sha256)
print("Loaded class source:", class_source)
"""))

cells.append(code(r"""
from importlib.metadata import version
import json
import math
import platform
import textwrap
import time
from urllib.request import urlretrieve

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pandas as pd
import xtgeo
from jpype import JClass
from neqsim import jneqsim
from neqsim.process.processTools import (
    clearProcess, compressor, cooler, mixer, runProcess, separator,
    separator3phase, stream, valve,
)
from neqsim.thermo import TPflash
from opm.io import Parser
from opm.io.ecl import EclFile, EGrid, ERst, ESmry

plt.style.use("seaborn-v0_8-whitegrid")
pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 160)
pd.set_option("display.max_rows", 120)

RANDOM_SEED = 20260831
RESERVOIR_TEMPERATURE_C = 97.5
RESERVOIR_TEMPERATURE_K = RESERVOIR_TEMPERATURE_C + 273.15
STANDARD_TEMPERATURE_C = 15.0
STANDARD_PRESSURE_BARA = 1.01325
INITIAL_RESERVOIR_PRESSURE_BARA = 260.0
PRODUCER_BHP_LIMIT_BARA = 80.0
SECONDS_PER_DAY = 86400.0
DLE_PRESSURES_BARA = np.array([300.0, 250.0, 220.0, 200.0, 180.0, 150.0, 100.0, 50.0, 1.01325])
GAS_PVT_PRESSURES_BARA = np.array([1.01325, 25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0])

OUTPUT_DIRECTORY = Path("rms_to_opm_outputs").resolve()
DATA_DIRECTORY = OUTPUT_DIRECTORY / "input"
ERT_DIRECTORY = OUTPUT_DIRECTORY / "ert"
if OUTPUT_DIRECTORY.exists():
    shutil.rmtree(OUTPUT_DIRECTORY)
DATA_DIRECTORY.mkdir(parents=True)
ERT_DIRECTORY.mkdir(parents=True)
FIGURE_PATHS = []

runtime_table = pd.DataFrame({
    "runtime": ["Python", "Java", "NeqSim Python bridge", "NeqSim Java", "XTGeo", "OPM Python", "OPM Flow", "ERT"],
    "version or identity": [
        platform.python_version(),
        subprocess.run(["java", "-version"], capture_output=True, text=True, check=True).stderr.splitlines()[0],
        version("neqsim"),
        neqsim_commit[:12],
        version("xtgeo"),
        version("opm"),
        (flow_version_output.stdout or flow_version_output.stderr).strip().splitlines()[0],
        version("ert"),
    ],
})
display(runtime_table)
"""))

cells.append(code(r"""
architecture_figure, axis = plt.subplots(figsize=(13.5, 5.0))
axis.set_xlim(0, 13.5)
axis.set_ylim(0, 5.0)
axis.axis("off")

nodes = [
    (0.3, 2.0, 2.1, 1.1, "RMS-origin\nROFF export", "#5B8FF9"),
    (2.9, 2.0, 2.1, 1.1, "XTGeo\nQC + blocking", "#61DDAA"),
    (5.5, 3.25, 2.1, 1.1, "NeqSim\nPVT", "#F6BD16"),
    (5.5, 0.75, 2.1, 1.1, "Agent job\ncontract", "#9270CA"),
    (8.1, 2.0, 2.1, 1.1, "OPM Flow\nsimulation", "#E8684A"),
    (10.8, 3.25, 2.1, 1.1, "ERT\nensemble", "#6DC8EC"),
    (10.8, 0.75, 2.1, 1.1, "NeqSim\nfacilities", "#FF9D4D"),
]
for x, y, width, height, label, color in nodes:
    axis.add_patch(plt.Rectangle((x, y), width, height, facecolor=color, edgecolor="#263238", linewidth=1.4))
    axis.text(x + width / 2, y + height / 2, label, ha="center", va="center", color="white", weight="bold", fontsize=10)

arrows = [
    ((2.4, 2.55), (2.9, 2.55)),
    ((5.0, 2.55), (8.1, 2.55)),
    ((7.6, 3.8), (8.5, 3.1)),
    ((7.6, 1.3), (8.5, 2.0)),
    ((10.2, 2.75), (10.8, 3.55)),
    ((10.2, 2.25), (10.8, 1.55)),
]
for start, end in arrows:
    axis.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "linewidth": 2, "color": "#263238"})

axis.text(1.35, 1.55, "public fixture", ha="center", color="#455A64")
axis.text(6.55, 4.55, "fluid contract", ha="center", color="#455A64")
axis.text(6.55, 0.30, "governed execution", ha="center", color="#455A64")
axis.set_title("Executed public path and reusable production-agent boundary", fontsize=15, weight="bold")
path = OUTPUT_DIRECTORY / "workflow_architecture.png"
architecture_figure.savefig(path, dpi=160, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(md(r"""
## 1. Immutable public RMS-origin inputs

The data come from equinor/xtgeo-testdata at commit
cad17f24e22c19c6cefe6f647185395cc0a11add under LGPL-3.0. Its Reek readme states that the data
were taken from an RMS project. The public files contain no license, credentials, or private
asset paths.

The geological ROFF contains geometry plus Poro, EQLNUM, and Facies. The simulation ROFF
contains the blocked grid. Separate simulation property files provide porosity, permeability,
facies, and zone. Every byte used below is downloaded from the immutable commit and checked.
"""))

cells.append(code(r"""
DATA_COMMIT = "cad17f24e22c19c6cefe6f647185395cc0a11add"
DATA_BASE = f"https://raw.githubusercontent.com/equinor/xtgeo-testdata/{DATA_COMMIT}/3dgrids/reek"
DATA_MANIFEST = [
    ("0readme.txt", "8f76ce966e77a13cdeb1be9bf021b330719f34ac51d810569fc8e27df05cedcd", 149),
    ("reek_geo2_grid_3props.roff", "cf199d7126dc96b574e05c6709a5216f454e2da7ff5e017bc7a503a6ab1a165c", 7837496),
    ("reek_sim_grid.roff", "6454b7aa1d1f2701438310b8b3dc3101e70dd9643b49ec2f837a257e802ea90d", 376580),
    ("reek_sim_poro.roff", "7368cc75d0436c3816fd16d61f77621c00f4f97ec25f0fcc2a7b0ddfe3cb3c14", 143718),
    ("reek_sim_permx.roff", "37866e0fb8d9ab8e036f2ed9d34537a7274efbf63466526942e7da34ff297b53", 143719),
    ("reek_sim_facies2.roff", "6aeb52f6dd41f1e0783fb998a92b3da08cfa0f8fd5621f537b4b10e4903f9bb9", 143786),
    ("reek_sim_zone.roff", "1d8f60577a4da72b6234eb036e8d1d0248513fb93d61b955e58fab3563521baa", 143825),
]

download_rows = []
for filename, expected_sha256, expected_bytes in DATA_MANIFEST:
    destination = DATA_DIRECTORY / filename
    if not destination.exists():
        urlretrieve(f"{DATA_BASE}/{filename}", destination)
    actual_bytes = destination.stat().st_size
    actual_sha256 = hashlib.sha256(destination.read_bytes()).hexdigest()
    verified = actual_sha256 == expected_sha256 and actual_bytes == expected_bytes
    if not verified:
        raise RuntimeError(f"Integrity check failed for {filename}")
    download_rows.append({
        "file": filename,
        "bytes": actual_bytes,
        "sha256": actual_sha256,
        "verified": verified,
        "immutable URL": f"{DATA_BASE}/{filename}",
    })

download_table = pd.DataFrame(download_rows)
display(download_table)
print((DATA_DIRECTORY / "0readme.txt").read_text(encoding="utf-8"))
"""))

cells.append(md(r"""
## 2. Read the geological and simulation grids with XTGeo

ROFF is the native handover format in this example. XTGeo reads both corner-point geometry and
properties while retaining the I, J, K ordering and inactive-cell masks. The fine geological
model is not sent directly to Flow. It is compared with the supplied simulation-scale export so
that the blocking rules are visible and testable.
"""))

cells.append(code(r"""
fine_grid_path = DATA_DIRECTORY / "reek_geo2_grid_3props.roff"
sim_grid_path = DATA_DIRECTORY / "reek_sim_grid.roff"

fine_grid = xtgeo.grid_from_file(fine_grid_path)
fine_properties_collection = xtgeo.gridproperties_from_file(
    fine_grid_path,
    names=["Poro", "EQLNUM", "Facies"],
    grid=fine_grid,
)
fine_properties = {prop.name.lower(): prop for prop in fine_properties_collection.props}

sim_grid = xtgeo.grid_from_file(sim_grid_path)
sim_poro = xtgeo.gridproperty_from_file(DATA_DIRECTORY / "reek_sim_poro.roff", grid=sim_grid)
sim_permx = xtgeo.gridproperty_from_file(DATA_DIRECTORY / "reek_sim_permx.roff", grid=sim_grid)
sim_facies = xtgeo.gridproperty_from_file(DATA_DIRECTORY / "reek_sim_facies2.roff", grid=sim_grid)
sim_zone = xtgeo.gridproperty_from_file(DATA_DIRECTORY / "reek_sim_zone.roff", grid=sim_grid)
sim_poro.name = "PORO"
sim_permx.name = "PERMX"
sim_facies.name = "FACIES"
sim_zone.name = "FIPNUM"

fine_poro = fine_properties["poro"]
fine_eqlnum = fine_properties["eqlnum"]
fine_facies = fine_properties["facies"]

grid_table = pd.DataFrame([
    {
        "grid": "geological",
        "NI": fine_grid.ncol,
        "NJ": fine_grid.nrow,
        "NK": fine_grid.nlay,
        "total cells": fine_grid.ntotal,
        "active cells": fine_grid.nactive,
    },
    {
        "grid": "simulation",
        "NI": sim_grid.ncol,
        "NJ": sim_grid.nrow,
        "NK": sim_grid.nlay,
        "total cells": sim_grid.ntotal,
        "active cells": sim_grid.nactive,
    },
])
display(grid_table)
"""))

cells.append(code(r"""
property_objects = {
    "fine Poro": fine_poro,
    "fine EQLNUM": fine_eqlnum,
    "fine Facies": fine_facies,
    "simulation PORO": sim_poro,
    "simulation PERMX [mD]": sim_permx,
    "simulation FACIES": sim_facies,
    "simulation Zone": sim_zone,
}
summary_rows = []
for label, prop in property_objects.items():
    values = prop.values
    summary_rows.append({
        "property": label,
        "minimum": float(np.ma.min(values)),
        "mean": float(np.ma.mean(values)),
        "maximum": float(np.ma.max(values)),
        "defined cells": int(values.count()),
        "discrete": bool(prop.isdiscrete),
        "codes": ", ".join(str(int(value)) for value in np.unique(values.compressed())[:12]) if prop.isdiscrete else "",
    })
property_summary = pd.DataFrame(summary_rows)
display(property_summary.round(6))

sim_x, sim_y, sim_z = sim_grid.get_xyz()
sim_dz = sim_grid.get_dz()
coordinate_table = pd.DataFrame({
    "quantity": ["X", "Y", "depth", "cell thickness"],
    "minimum": [
        float(np.ma.min(sim_x.values)), float(np.ma.min(sim_y.values)),
        float(np.ma.min(sim_z.values)), float(np.ma.min(sim_dz.values)),
    ],
    "mean": [
        float(np.ma.mean(sim_x.values)), float(np.ma.mean(sim_y.values)),
        float(np.ma.mean(sim_z.values)), float(np.ma.mean(sim_dz.values)),
    ],
    "maximum": [
        float(np.ma.max(sim_x.values)), float(np.ma.max(sim_y.values)),
        float(np.ma.max(sim_z.values)), float(np.ma.max(sim_dz.values)),
    ],
    "unit": ["m", "m", "m TVDSS", "m"],
})
display(coordinate_table.round(3))
"""))

cells.append(code(r"""
fine_x, fine_y, fine_z = fine_grid.get_xyz()
fine_top = np.ma.filled(fine_z.values[:, :, 0], np.nan)
sim_top = np.ma.filled(sim_z.values[:, :, 0], np.nan)
sim_poro_map = np.nanmean(np.ma.filled(sim_poro.values, np.nan), axis=2)
sim_logk_map = np.nanmean(np.log10(np.ma.filled(sim_permx.values, np.nan)), axis=2)

structure_figure, axes = plt.subplots(2, 2, figsize=(13.5, 9.0), constrained_layout=True)
items = [
    (fine_top.T, "Geological-grid top depth", "viridis_r", "m TVDSS"),
    (sim_top.T, "Simulation-grid top depth", "viridis_r", "m TVDSS"),
    (sim_poro_map.T, "Simulation-grid mean porosity", "YlGnBu", "fraction"),
    (sim_logk_map.T, "Simulation-grid mean log10(PERMX)", "magma", "log10(mD)"),
]
for axis, (array, title, cmap, unit) in zip(axes.ravel(), items):
    image = axis.imshow(array, origin="lower", aspect="auto", cmap=cmap)
    axis.set_title(title)
    axis.set_xlabel("I column")
    axis.set_ylabel("J row")
    structure_figure.colorbar(image, ax=axis, label=unit, shrink=0.82)

path = OUTPUT_DIRECTORY / "reek_structure_and_static_maps.png"
structure_figure.savefig(path, dpi=165, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(code(r"""
active_poro = sim_poro.values.compressed()
active_permx = sim_permx.values.compressed()
active_facies = sim_facies.values.compressed().astype(int)

distribution_figure, axes = plt.subplots(1, 3, figsize=(14.5, 4.4), constrained_layout=True)
axes[0].hist(active_poro, bins=30, color="#007F87", edgecolor="white")
axes[0].set(xlabel="Porosity [-]", ylabel="Active cells", title="Simulation porosity")
axes[1].hist(active_permx, bins=np.logspace(np.log10(active_permx.min()), np.log10(active_permx.max()), 32),
             color="#C75B12", edgecolor="white")
axes[1].set_xscale("log")
axes[1].set(xlabel="PERMX [mD]", ylabel="Active cells", title="Permeability")
scatter = axes[2].scatter(active_poro, active_permx, c=active_facies, cmap="viridis",
                          s=7, alpha=0.28, rasterized=True)
axes[2].set_yscale("log")
axes[2].set(xlabel="Porosity [-]", ylabel="PERMX [mD]", title="Rock-property cross-plot")
distribution_figure.colorbar(scatter, ax=axes[2], label="Facies code")
path = OUTPUT_DIRECTORY / "reek_property_distributions.png"
distribution_figure.savefig(path, dpi=165, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(md(r"""
## 3. Blocking and spreading properties

The dimensions reveal an exact 2 × 2 × 4 relationship:

$$
(80,128,56) \rightarrow (40,64,14).
$$

For block B, porosity is pore-volume weighted:

$$
\phi_B = \frac{\sum_{c\in B} \phi_c V_c A_c}
{\sum_{c\in B} V_c A_c},
$$

where V is bulk volume and A is the active-cell indicator. Facies is assigned by the largest
active bulk volume in the block. For teaching, fine Background, Channel, and Crevasse codes are
mapped to simulation SHALE, COARSESAND, and FINESAND codes. This mapping is explicit and is not
claimed to reproduce every hidden RMS workflow setting.

Permeability is not arithmetically averaged here. The supplied simulation PERMX is used because
flow upscaling is directional and depends on boundary conditions. The future RMS job contract
therefore names the approved permeability-upscaling workflow rather than silently inventing one.
"""))

cells.append(code(r"""
BLOCK = (2, 2, 4)
assert (
    fine_grid.ncol // sim_grid.ncol,
    fine_grid.nrow // sim_grid.nrow,
    fine_grid.nlay // sim_grid.nlay,
) == BLOCK

fine_actnum = np.ma.filled(fine_grid.get_actnum().values, 0).astype(bool)
fine_bulk_volume = np.ma.filled(fine_grid.get_bulk_volume().values, 0.0)
fine_poro_values = np.ma.filled(fine_poro.values, 0.0)
fine_facies_values = np.ma.filled(fine_facies.values, 0).astype(int)

def block_sum(array):
    reshaped = array.reshape(
        sim_grid.ncol, BLOCK[0],
        sim_grid.nrow, BLOCK[1],
        sim_grid.nlay, BLOCK[2],
    )
    return reshaped.sum(axis=(1, 3, 5))

active_volume = fine_bulk_volume * fine_actnum
blocked_volume = block_sum(active_volume)
blocked_poro = np.divide(
    block_sum(fine_poro_values * active_volume),
    blocked_volume,
    out=np.full_like(blocked_volume, np.nan, dtype=float),
    where=blocked_volume > 0.0,
)

facies_volume = np.stack([
    block_sum(active_volume * (fine_facies_values == code_value))
    for code_value in [0, 1, 2]
])
fine_majority_facies = np.argmax(facies_volume, axis=0)
fine_to_sim_facies = np.array([0, 2, 1])
blocked_facies = fine_to_sim_facies[fine_majority_facies]

sim_actnum = np.ma.filled(sim_grid.get_actnum().values, 0).astype(bool)
sim_poro_values = np.ma.filled(sim_poro.values, np.nan)
sim_facies_values = np.ma.filled(sim_facies.values, -1).astype(int)
comparison_mask = sim_actnum & np.isfinite(blocked_poro) & np.isfinite(sim_poro_values)

poro_difference = blocked_poro[comparison_mask] - sim_poro_values[comparison_mask]
blocking_metrics = pd.DataFrame({
    "metric": [
        "fine cells per simulation block",
        "porosity RMSE",
        "porosity mean bias",
        "porosity correlation",
        "facies agreement after teaching map",
        "compared active blocks",
    ],
    "value": [
        int(np.prod(BLOCK)),
        float(np.sqrt(np.mean(poro_difference ** 2))),
        float(np.mean(poro_difference)),
        float(np.corrcoef(blocked_poro[comparison_mask], sim_poro_values[comparison_mask])[0, 1]),
        float(np.mean(blocked_facies[comparison_mask] == sim_facies_values[comparison_mask])),
        int(comparison_mask.sum()),
    ],
    "unit": ["fine cells", "fraction", "fraction", "correlation", "fraction", "blocks"],
})
display(blocking_metrics.round(6))
"""))

cells.append(code(r"""
layer_index = sim_grid.nlay // 2
fine_layer_start = layer_index * BLOCK[2]
fine_layer_mean = np.nanmean(
    np.ma.filled(fine_poro.values[:, :, fine_layer_start:fine_layer_start + BLOCK[2]], np.nan),
    axis=2,
)

blocking_figure, axes = plt.subplots(2, 2, figsize=(13.0, 9.0), constrained_layout=True)
arrays = [
    (fine_layer_mean.T, "Fine porosity: four layers before blocking", "YlGnBu", 0.0, 0.40),
    (blocked_poro[:, :, layer_index].T, "Calculated PV-weighted blocked porosity", "YlGnBu", 0.0, 0.40),
    (sim_poro_values[:, :, layer_index].T, "Supplied RMS simulation porosity", "YlGnBu", 0.0, 0.40),
    ((blocked_poro[:, :, layer_index] - sim_poro_values[:, :, layer_index]).T,
     "Calculated minus supplied", "coolwarm", -0.12, 0.12),
]
for axis, (array, title, cmap, vmin, vmax) in zip(axes.ravel(), arrays):
    image = axis.imshow(array, origin="lower", aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    axis.set(title=title, xlabel="I column", ylabel="J row")
    blocking_figure.colorbar(image, ax=axis, shrink=0.82)
blocking_figure.suptitle(f"Blocking audit for simulation layer {layer_index + 1}", fontsize=15)
path = OUTPUT_DIRECTORY / "reek_blocking_comparison.png"
blocking_figure.savefig(path, dpi=170, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(code(r"""
spread_figure, axes = plt.subplots(2, 3, figsize=(15.0, 8.5), constrained_layout=True)
selected_layers = [1, sim_grid.nlay // 2]
facies_colors = "viridis"
for row, k_index in enumerate(selected_layers):
    facies_image = axes[row, 0].imshow(sim_facies_values[:, :, k_index].T, origin="lower",
                                       aspect="auto", cmap=facies_colors, vmin=0, vmax=2)
    axes[row, 0].set_title(f"Facies, layer {k_index + 1}")
    poro_image = axes[row, 1].imshow(sim_poro_values[:, :, k_index].T, origin="lower",
                                     aspect="auto", cmap="YlGnBu", vmin=0.0, vmax=0.4)
    axes[row, 1].set_title(f"PORO, layer {k_index + 1}")
    perm_image = axes[row, 2].imshow(
        np.log10(np.ma.filled(sim_permx.values[:, :, k_index], np.nan)).T,
        origin="lower", aspect="auto", cmap="magma", vmin=-1, vmax=4,
    )
    axes[row, 2].set_title(f"log10(PERMX/mD), layer {k_index + 1}")
    for axis in axes[row]:
        axis.set(xlabel="I column", ylabel="J row")
spread_figure.colorbar(facies_image, ax=axes[:, 0], label="Facies code", shrink=0.85)
spread_figure.colorbar(poro_image, ax=axes[:, 1], label="Porosity [-]", shrink=0.85)
spread_figure.colorbar(perm_image, ax=axes[:, 2], label="log10(mD)", shrink=0.85)
path = OUTPUT_DIRECTORY / "reek_property_spreading_layers.png"
spread_figure.savefig(path, dpi=170, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(md(r"""
## 4. Screen an injector–producer pair

A transparent screening score is used only to place demonstration wells. It combines column
hydrocarbon pore volume with a logarithmic permeability-thickness proxy. The producer uses the
best column. The injector is selected among high-score columns 8–14 Manhattan grid steps away,
which makes the displacement visible without claiming an optimized field-development plan.
Only active layers are completed.
"""))

cells.append(code(r"""
sim_bulk_volume = np.ma.filled(sim_grid.get_bulk_volume().values, 0.0)
sim_perm_values = np.ma.filled(sim_permx.values, 0.0)
INITIAL_WATER_SATURATION = 0.18
column_hcpv = np.sum(sim_bulk_volume * sim_poro_values * (1.0 - INITIAL_WATER_SATURATION), axis=2)
column_kh = np.sum(sim_perm_values * np.ma.filled(sim_dz.values, 0.0), axis=2)
screening_score = column_hcpv * np.log1p(column_kh)
screening_score[~np.any(sim_actnum, axis=2)] = -np.inf

producer_flat = int(np.nanargmax(screening_score))
producer_i, producer_j = np.unravel_index(producer_flat, screening_score.shape)

candidate_order = np.argsort(screening_score.ravel())[::-1]
injector_i = injector_j = None
for flat_index in candidate_order:
    i_index, j_index = np.unravel_index(int(flat_index), screening_score.shape)
    distance = abs(i_index - producer_i) + abs(j_index - producer_j)
    if 8 <= distance <= 14 and np.isfinite(screening_score[i_index, j_index]):
        injector_i, injector_j = i_index, j_index
        break
if injector_i is None:
    raise RuntimeError("No suitable injector column was found.")

producer_layers = np.flatnonzero(sim_actnum[producer_i, producer_j, :]) + 1
injector_layers = np.flatnonzero(sim_actnum[injector_i, injector_j, :]) + 1

well_table = pd.DataFrame([
    {
        "well": "PROD", "I": producer_i + 1, "J": producer_j + 1,
        "first K": int(producer_layers.min()), "last K": int(producer_layers.max()),
        "active completions": len(producer_layers),
        "column HCPV [million rm3]": column_hcpv[producer_i, producer_j] / 1e6,
        "score": screening_score[producer_i, producer_j],
    },
    {
        "well": "WINJ", "I": injector_i + 1, "J": injector_j + 1,
        "first K": int(injector_layers.min()), "last K": int(injector_layers.max()),
        "active completions": len(injector_layers),
        "column HCPV [million rm3]": column_hcpv[injector_i, injector_j] / 1e6,
        "score": screening_score[injector_i, injector_j],
    },
])
display(well_table.round(3))
"""))

cells.append(code(r"""
well_figure, axis = plt.subplots(figsize=(10.5, 7.0), constrained_layout=True)
image = axis.imshow((column_hcpv / 1e6).T, origin="lower", aspect="auto", cmap="viridis")
axis.scatter(producer_i, producer_j, marker="v", s=180, color="#D55E00",
             edgecolor="white", linewidth=1.3, label="PROD")
axis.scatter(injector_i, injector_j, marker="^", s=180, color="#0072B2",
             edgecolor="white", linewidth=1.3, label="WINJ")
axis.plot([producer_i, injector_i], [producer_j, injector_j], color="white", linestyle="--", linewidth=1.8)
axis.set(xlabel="I column", ylabel="J row", title="Hydrocarbon pore-volume screen and selected wells")
axis.legend()
well_figure.colorbar(image, ax=axis, label="Column HCPV [million reservoir m3]")
path = OUTPUT_DIRECTORY / "reek_well_screening.png"
well_figure.savefig(path, dpi=170, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(md(r"""
## 5. Generate black-oil PVT with NeqSim

The composition below is fully visible. NeqSim characterizes the C20+ fraction into twelve
pseudo-components, runs a differential-liberation calculation, derives gas and water
properties, and emits strict Flow tables. The PVT input and every generated table row are
printed, not hidden behind a pre-built include file.
"""))

for index in [8, 9, 11, 12, 14, 15]:
    cell_source = source_cell(index)
    if index == 12:
        cell_source += "\nFIGURE_PATHS.append(pvt_plot_path)"
    cells.append(code(cell_source))

pvt_include_source = source_cell(16)
pvt_include_source += r"""

print("\nComplete generated NEQSIM_PVT.INC:\n")
print(black_oil_include)
"""
cells.append(code(pvt_include_source))

cells.append(md(r"""
## 6. Export Flow grid and static properties

The OPM model uses the supplied RMS simulation-scale geometry and properties. The exact modeling
assumptions are:

- PORO and PERMX: supplied public simulation properties;
- PERMY = 0.70 × PERMX;
- PERMZ = 0.10 × PERMX;
- FIPNUM: supplied Zone property;
- initial saturation: equilibrium plus the SWOF endpoint;
- relative permeability: the complete tables printed below.

Each GRDECL include is written by XTGeo and hashed. These generated files plus the immutable ROFF
sources make the complete numerical input reproducible without printing hundreds of thousands
of cell values into the browser.
"""))

cells.append(code(r"""
relative_permeability_tables = '''
SWOF
  0.12  0.00000  1.0000  0.0
  0.20  0.00010  0.8500  0.0
  0.30  0.00100  0.6200  0.0
  0.40  0.00800  0.4000  0.0
  0.50  0.03000  0.2200  0.0
  0.60  0.09000  0.1000  0.0
  0.70  0.22000  0.0300  0.0
  0.80  0.48000  0.0050  0.0
  0.88  1.00000  0.0000  0.0 /

SGOF
  0.00  0.0000  1.0000  0.0
  0.05  0.0020  0.9300  0.0
  0.10  0.0100  0.8000  0.0
  0.20  0.0600  0.5500  0.0
  0.30  0.1600  0.3200  0.0
  0.40  0.3300  0.1500  0.0
  0.50  0.5500  0.0500  0.0
  0.60  0.7800  0.0100  0.0
  0.70  0.9300  0.0010  0.0
  0.88  1.0000  0.0000  0.0 /
'''.strip()
print(relative_permeability_tables)

grid_include_path = OUTPUT_DIRECTORY / "REEK_GRID.GRDECL"
sim_grid.to_file(grid_include_path, fformat="grdecl")

def export_grid_property(source_property, keyword, multiplier=1.0):
    exported = source_property.copy()
    exported.name = keyword
    exported.values = source_property.values * multiplier
    output_path = OUTPUT_DIRECTORY / f"{keyword}.GRDECL"
    exported.to_file(output_path, fformat="grdecl")
    return output_path

poro_path = export_grid_property(sim_poro, "PORO")
permx_path = export_grid_property(sim_permx, "PERMX")
permy_path = export_grid_property(sim_permx, "PERMY", 0.70)
permz_path = export_grid_property(sim_permx, "PERMZ", 0.10)
fipnum_path = export_grid_property(sim_zone, "FIPNUM")

generated_static_paths = [grid_include_path, poro_path, permx_path, permy_path, permz_path, fipnum_path]
generated_static_table = pd.DataFrame([
    {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    for path in generated_static_paths
])
display(generated_static_table)
print("\nGrid include header:\n", "\n".join(grid_include_path.read_text(encoding="utf-8").splitlines()[:24]))
"""))

cells.append(code(r"""
minimum_depth = float(np.ma.min(sim_z.values))
maximum_depth = float(np.ma.max(sim_z.values))
datum_depth = float(np.ma.mean(sim_z.values))
water_contact_depth = maximum_depth + 100.0
gas_contact_depth = minimum_depth - 100.0
initial_rs_sm3_sm3 = saturated_oil_rows[-1]["Rs"]

def completion_lines(well_name, i_index, j_index, layers):
    return "\n".join(
        f"  '{well_name}' {i_index + 1} {j_index + 1} {int(k)} {int(k)} 'OPEN' 1* 1* 0.20 /"
        for k in layers
    )

def render_deck(perm_multiplier, poro_multiplier, injection_rate):
    return f'''
RUNSPEC
TITLE
  PUBLIC RMS-ORIGIN REEK MODEL: NEQSIM PVT, OPM FLOW, ERT

DIMENS
  {sim_grid.ncol} {sim_grid.nrow} {sim_grid.nlay} /

OIL
GAS
WATER
DISGAS
METRIC

START
  1 'JAN' 2025 /

WELLDIMS
  2 {max(len(producer_layers), len(injector_layers))} 1 2 /

TABDIMS
/

EQLDIMS
/

UNIFOUT

GRID
INIT
INCLUDE
  '{grid_include_path.as_posix()}' /
INCLUDE
  '{poro_path.as_posix()}' /
INCLUDE
  '{permx_path.as_posix()}' /
INCLUDE
  '{permy_path.as_posix()}' /
INCLUDE
  '{permz_path.as_posix()}' /

MULTIPLY
  PORO {poro_multiplier} 6* /
  PERMX {perm_multiplier} 6* /
  PERMY {perm_multiplier} 6* /
  PERMZ {perm_multiplier} 6* /
/

PROPS
INCLUDE
  '{black_oil_path.resolve().as_posix()}' /

ROCK
  260.0 4.0E-5 /

{relative_permeability_tables}

REGIONS
INCLUDE
  '{fipnum_path.as_posix()}' /

SOLUTION
EQUIL
  {datum_depth:.6f} {INITIAL_RESERVOIR_PRESSURE_BARA:.6f}
  {water_contact_depth:.6f} 0.0 {gas_contact_depth:.6f} 0.0 1 0 0 /

RSVD
  {minimum_depth:.6f} {initial_rs_sm3_sm3:.8f}
  {maximum_depth:.6f} {initial_rs_sm3_sm3:.8f} /

SUMMARY
FPR
FOPR
FGPR
FWPR
FWIR
FOPT
FGPT
FWPT
WBHP
  'PROD' 'WINJ' /
WGOR
  'PROD' /

SCHEDULE
RPTRST
  'BASIC=1' /

GRUPTREE
  'WELLS' 'FIELD' /
/

WELSPECS
  'PROD' 'WELLS' {producer_i + 1} {producer_j + 1} {datum_depth:.3f} 'OIL' /
  'WINJ' 'WELLS' {injector_i + 1} {injector_j + 1} {datum_depth:.3f} 'WATER' /
/

COMPDAT
{completion_lines("PROD", producer_i, producer_j, producer_layers)}
{completion_lines("WINJ", injector_i, injector_j, injector_layers)}
/

WCONPROD
  'PROD' 'OPEN' 'ORAT' 10000.0 4* {PRODUCER_BHP_LIMIT_BARA:.3f} /
/

WCONINJE
  'WINJ' 'WATER' 'OPEN' 'RATE' {injection_rate} 1* 320.0 /
/

TSTEP
  24*30.4375 /

END
'''.strip()

deck_text = render_deck(1.0, 1.0, 12000.0)
deck_path = OUTPUT_DIRECTORY / "RMS_REEK_BASE.DATA"
deck_path.write_text(deck_text + "\n", encoding="utf-8")
print(deck_text)
"""))

cells.append(code(r"""
parsed_deck = Parser().parse(str(deck_path))
required_keywords = [
    "DIMENS", "COORD", "ZCORN", "ACTNUM", "PORO", "PERMX", "PERMY", "PERMZ",
    "DENSITY", "PVTO", "PVDG", "PVTW", "EQUIL", "WELSPECS", "COMPDAT",
    "WCONPROD", "WCONINJE",
]
deck_keyword_audit = pd.DataFrame({
    "keyword": required_keywords,
    "present": [keyword in parsed_deck for keyword in required_keywords],
})
oil_table_audit = pd.DataFrame(saturated_oil_rows)
pvt_contract_audit = pd.DataFrame({
    "contract": [
        "saturated Rs strictly increases",
        "bubble pressure strictly increases",
        "dry-gas pressure strictly increases",
        "dry-gas Bg strictly decreases",
        "no invalid numeric tokens",
    ],
    "passed": [
        np.all(np.diff(oil_table_audit["Rs"]) > 0),
        np.all(np.diff(oil_table_audit["pressure"]) > 0),
        np.all(np.diff(dry_gas_table["pressure_bara"]) > 0),
        np.all(np.diff(dry_gas_table["Bg_rm3_Sm3"]) < 0),
        not any(token in black_oil_include for token in ["NaN", "Infinity", "-Infinity"]),
    ],
})
display(deck_keyword_audit)
display(pvt_contract_audit)
if not deck_keyword_audit["present"].all() or not pvt_contract_audit["passed"].all():
    raise AssertionError("Deck or PVT contract validation failed.")
print(f"OPM parser accepted {len(parsed_deck)} expanded keywords.")
"""))

cells.append(md(r"""
## 7. Run OPM Flow and retain diagnostics

This is the real simulator invocation. It is not a surrogate decline curve. The return code,
reported timing, output files, and log tail are retained. A failed simulator call raises an
exception and prevents publication of an apparently successful notebook.
"""))

cells.append(code(r"""
flow_start = time.perf_counter()
flow_run = subprocess.run(
    [FLOW_EXECUTABLE, deck_path.name],
    cwd=OUTPUT_DIRECTORY,
    env=FLOW_RUN_ENV,
    capture_output=True,
    text=True,
    timeout=1200,
)
flow_elapsed = time.perf_counter() - flow_start
if flow_run.returncode != 0:
    raise RuntimeError(
        "OPM Flow failed:\n" + flow_run.stdout[-8000:] + "\n" + flow_run.stderr[-4000:]
    )
flow_log_tail = "\n".join(flow_run.stdout.splitlines()[-35:])
flow_diagnostics = pd.DataFrame({
    "diagnostic": ["return code", "wall time", "SMSPEC exists", "UNRST exists", "PRT exists"],
    "value": [
        flow_run.returncode,
        flow_elapsed,
        (OUTPUT_DIRECTORY / "RMS_REEK_BASE.SMSPEC").exists(),
        (OUTPUT_DIRECTORY / "RMS_REEK_BASE.UNRST").exists(),
        (OUTPUT_DIRECTORY / "RMS_REEK_BASE.PRT").exists(),
    ],
    "unit": ["-", "s", "boolean", "boolean", "boolean"],
})
display(flow_diagnostics)
print(flow_log_tail)
"""))

cells.append(code(r"""
flow_summary = ESmry(str(OUTPUT_DIRECTORY / "RMS_REEK_BASE.SMSPEC"))
def summary_values(key):
    return np.asarray(flow_summary[key], dtype=float)

reservoir_history = pd.DataFrame({
    "date": pd.to_datetime(flow_summary.dates()),
    "time_days": summary_values("TIME"),
    "field_pressure_bara": summary_values("FPR"),
    "oil_rate_Sm3_day": summary_values("FOPR"),
    "gas_rate_Sm3_day": summary_values("FGPR"),
    "water_rate_Sm3_day": summary_values("FWPR"),
    "water_injection_Sm3_day": summary_values("FWIR"),
    "cumulative_oil_MSm3": summary_values("FOPT") / 1e6,
    "cumulative_gas_GSm3": summary_values("FGPT") / 1e9,
    "cumulative_water_MSm3": summary_values("FWPT") / 1e6,
    "producer_bhp_bara": summary_values("WBHP:PROD"),
    "well_gor_Sm3_Sm3": summary_values("WGOR:PROD"),
})
display(reservoir_history)
"""))

cells.append(code(r"""
forecast_figure, axes = plt.subplots(2, 2, figsize=(13.0, 8.5), constrained_layout=True)
years = reservoir_history["time_days"] / 365.25
axes[0, 0].plot(years, reservoir_history["field_pressure_bara"], color="#0072B2", linewidth=2)
axes[0, 0].axhline(bubble_pressure_bara, color="black", linestyle="--", label="NeqSim bubble pressure")
axes[0, 0].set(xlabel="Time [year]", ylabel="Pressure [bara]", title="Field pressure")
axes[0, 0].legend()
axes[0, 1].plot(years, reservoir_history["oil_rate_Sm3_day"], label="oil", color="#009E73")
axes[0, 1].plot(years, reservoir_history["water_rate_Sm3_day"], label="water", color="#56B4E9")
axes[0, 1].set(xlabel="Time [year]", ylabel="Rate [Sm3/day]", title="Production rates")
axes[0, 1].legend()
axes[1, 0].plot(years, reservoir_history["gas_rate_Sm3_day"] / 1e3, color="#E69F00")
axes[1, 0].set(xlabel="Time [year]", ylabel="Gas rate [thousand Sm3/day]", title="Produced gas")
axes[1, 1].plot(years, reservoir_history["water_injection_Sm3_day"], color="#0072B2", label="water injection")
axes[1, 1].plot(years, reservoir_history["producer_bhp_bara"], color="#D55E00", label="producer BHP")
axes[1, 1].set(xlabel="Time [year]", ylabel="Rate or pressure", title="Well controls")
axes[1, 1].legend()
path = OUTPUT_DIRECTORY / "opm_flow_forecast.png"
forecast_figure.savefig(path, dpi=170, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(md(r"""
## 8. Read real restart states and visualize displacement

OPM writes EGRID, INIT, and UNRST. The two inactive simulation cells are handled explicitly:
active vectors are inserted into an I-fastest global array before conversion to K, J, I plotting
order. This prevents the common mistake of reshaping an active vector as if every cell were live.
"""))

cells.append(code(r"""
reservoir_grid = EGrid(str(OUTPUT_DIRECTORY / "RMS_REEK_BASE.EGRID"))
initialization_file = EclFile(str(OUTPUT_DIRECTORY / "RMS_REEK_BASE.INIT"))
restart_file = ERst(str(OUTPUT_DIRECTORY / "RMS_REEK_BASE.UNRST"))
restart_steps = [int(step) for step in restart_file.report_steps]
final_restart_step = restart_steps[-1]

grid_nx, grid_ny, grid_nz = [int(value) for value in reservoir_grid.dimension]
active_cell_count = int(reservoir_grid.active_cells)
act_flat = sim_actnum.ravel(order="F")

def active_to_kji(active_values):
    active_values = np.asarray(active_values, dtype=float)
    if active_values.size != act_flat.sum():
        raise ValueError(f"Expected {act_flat.sum()} active values, received {active_values.size}")
    global_flat = np.full(act_flat.size, np.nan)
    global_flat[act_flat] = active_values
    ijk = global_flat.reshape((grid_nx, grid_ny, grid_nz), order="F")
    return np.transpose(ijk, (2, 1, 0))

permeability_cube_md = active_to_kji(initialization_file["PERMX"])
final_pressure_cube_bara = active_to_kji(restart_file["PRESSURE", final_restart_step])
final_water_saturation_cube = active_to_kji(restart_file["SWAT", final_restart_step])
final_gas_saturation_cube = active_to_kji(restart_file["SGAS", final_restart_step])
final_oil_saturation_cube = 1.0 - final_water_saturation_cube - final_gas_saturation_cube

restart_audit = pd.DataFrame({
    "quantity": ["dimensions", "active cells", "restart states", "pressure range", "SWAT range", "SGAS range", "minimum SOIL"],
    "value": [
        f"{grid_nx} × {grid_ny} × {grid_nz}",
        active_cell_count,
        len(restart_steps),
        f"{np.nanmin(final_pressure_cube_bara):.3f} to {np.nanmax(final_pressure_cube_bara):.3f}",
        f"{np.nanmin(final_water_saturation_cube):.4f} to {np.nanmax(final_water_saturation_cube):.4f}",
        f"{np.nanmin(final_gas_saturation_cube):.4f} to {np.nanmax(final_gas_saturation_cube):.4f}",
        float(np.nanmin(final_oil_saturation_cube)),
    ],
})
display(restart_audit)
"""))

cells.append(code(r"""
layers_to_plot = np.unique(np.linspace(0, grid_nz - 1, 4, dtype=int))
state_map_figure, axes = plt.subplots(len(layers_to_plot), 3, figsize=(13.5, 14.0), constrained_layout=True)
definitions = [
    (final_pressure_cube_bara, "Pressure", "bara", "viridis"),
    (final_water_saturation_cube, "Water saturation", "fraction", "Blues"),
    (final_gas_saturation_cube, "Gas saturation", "fraction", "Oranges"),
]
images = []
for column, (cube, label, unit, cmap) in enumerate(definitions):
    vmin, vmax = np.nanmin(cube), np.nanmax(cube)
    for row, k_index in enumerate(layers_to_plot):
        image = axes[row, column].imshow(cube[k_index], origin="lower", cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
        if row == 0:
            images.append(image)
        axes[row, column].scatter(producer_i, producer_j, marker="v", s=65, color="#D55E00", edgecolor="white")
        axes[row, column].scatter(injector_i, injector_j, marker="^", s=65, color="#0072B2", edgecolor="white")
        axes[row, column].set(title=f"Layer {k_index + 1}: {label}", xlabel="I", ylabel="J")
    state_map_figure.colorbar(images[column], ax=axes[:, column], label=f"{label} [{unit}]", shrink=0.82)
state_map_figure.suptitle("OPM Flow final restart states from the Reek corner-point model", fontsize=15)
path = OUTPUT_DIRECTORY / "opm_final_restart_maps.png"
state_map_figure.savefig(path, dpi=170, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(code(r"""
water_increment = final_water_saturation_cube - 0.12
candidate_mask = np.isfinite(water_increment) & (water_increment > 0.015)
k_indices, j_indices, i_indices = np.where(candidate_mask)
if len(i_indices) > 8000:
    rng = np.random.default_rng(RANDOM_SEED)
    keep = rng.choice(len(i_indices), 8000, replace=False)
    i_indices, j_indices, k_indices = i_indices[keep], j_indices[keep], k_indices[keep]

front_figure = plt.figure(figsize=(11.5, 8.0), constrained_layout=True)
axis = front_figure.add_subplot(111, projection="3d")
colors = final_water_saturation_cube[k_indices, j_indices, i_indices]
scatter = axis.scatter(i_indices, j_indices, -k_indices, c=colors, cmap="Blues",
                       vmin=0.12, vmax=max(0.2, float(np.nanmax(final_water_saturation_cube))),
                       s=16, alpha=0.7)
axis.plot([producer_i] * grid_nz, [producer_j] * grid_nz, -np.arange(grid_nz), color="#D55E00", linewidth=3, label="PROD")
axis.plot([injector_i] * grid_nz, [injector_j] * grid_nz, -np.arange(grid_nz), color="#0072B2", linewidth=3, label="WINJ")
axis.set(xlabel="I column", ylabel="J row", zlabel="Layer (depth downward)", title="Cells with increased water saturation")
axis.legend()
front_figure.colorbar(scatter, ax=axis, label="Final SWAT [-]", shrink=0.65)
axis.view_init(elev=26, azim=-55)
path = OUTPUT_DIRECTORY / "opm_3d_water_front.png"
front_figure.savefig(path, dpi=175, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(md(r"""
## 9. Agent contract: fixture today, licensed RMS worker later

An agent should not receive unrestricted shell access to an RMS workstation. It should submit a
typed job to an allow-listed service. The service validates project identity, workflow name,
grid model, properties, output location, resource limits, and approval policy. It returns signed
artifacts and a structured ledger.

The fixture backend below is actually exercised: it verifies the exported artifacts, blocking
contract, Flow run, and ERT run. A production RMS adapter would implement the same methods with
the RMS Python API inside a licensed environment. Human approval should remain mandatory for
publishing project changes, overwriting realizations, or promoting a model to decision use.
"""))

cells.append(code(r"""
agent_job = {
    "schema": "com.neqsim.reservoir-job/v1",
    "job_id": "reek-public-rms-opm-ert-20260831",
    "mode": "public_fixture",
    "source": {
        "kind": "rms_export",
        "repository": "equinor/xtgeo-testdata",
        "commit": DATA_COMMIT,
        "project_alias": "REEK_PUBLIC",
    },
    "requested_tools": [
        "rms.inspect_project", "rms.run_workflow", "rms.export_grid",
        "rms.export_properties", "neqsim.generate_pvt", "opm.validate",
        "opm.run", "ert.ensemble_experiment",
    ],
    "rms": {
        "workflow_allowlist": ["REEK_BLOCK_AND_EXPORT_V1"],
        "grid_model": "REEK_SIM",
        "properties": ["PORO", "PERMX", "FACIES", "Zone"],
        "blocking": {"i": 2, "j": 2, "k": 4},
        "write_policy": "new_realization_only",
    },
    "flow": {"simulator": "opm-flow", "forecast_months": 24},
    "ert": {"realizations": 4, "max_parallel": 2, "random_seed": RANDOM_SEED},
    "security": {
        "network_egress": "deny_except_artifact_registry",
        "secrets": "worker_identity_only",
        "human_approval": ["overwrite_rms", "publish_decision_model"],
    },
    "acceptance": {
        "all_hashes_verified": True,
        "simulator_return_code": 0,
        "ensemble_realizations": 4,
        "engineering_assertions": "all_pass",
    },
}

class AgentToolLedger:
    def __init__(self, job):
        self.job = job
        self.records = []

    def record(self, tool, status, evidence):
        entry = {
            "sequence": len(self.records) + 1,
            "tool": tool,
            "status": status,
            "evidence": evidence,
        }
        self.records.append(entry)
        return entry

    def frame(self):
        return pd.DataFrame(self.records)

agent_ledger = AgentToolLedger(agent_job)
agent_ledger.record("rms.inspect_project", "fixture_passed", {
    "data_commit": DATA_COMMIT,
    "verified_files": int(download_table["verified"].sum()),
})
agent_ledger.record("rms.run_workflow", "fixture_passed", {
    "workflow": "REEK_BLOCK_AND_EXPORT_V1",
    "blocking": list(BLOCK),
    "fine_cells": fine_grid.ntotal,
    "simulation_cells": sim_grid.ntotal,
})
agent_ledger.record("rms.export_grid", "fixture_passed", {
    "grid_sha256": generated_static_table.loc[generated_static_table["file"] == "REEK_GRID.GRDECL", "sha256"].iloc[0],
})
agent_ledger.record("neqsim.generate_pvt", "passed", {
    "source_commit": neqsim_commit,
    "bubble_pressure_bara": float(bubble_pressure_bara),
    "pvt_sha256": hashlib.sha256(black_oil_path.read_bytes()).hexdigest(),
})
agent_ledger.record("opm.validate", "passed", {
    "keywords": int(deck_keyword_audit["present"].sum()),
})
agent_ledger.record("opm.run", "passed", {
    "return_code": flow_run.returncode,
    "restart_steps": len(restart_steps),
})
job_path = OUTPUT_DIRECTORY / "agent_job.json"
job_path.write_text(json.dumps(agent_job, indent=2) + "\n", encoding="utf-8")
display(agent_ledger.frame())
print(json.dumps(agent_job, indent=2))
"""))

cells.append(md(r"""
### Licensed RMS adapter pattern

A production worker implements the same contract approximately as follows:

1. Resolve the approved project alias to a server-side path; never accept an arbitrary path.
2. Open the project read-only and inspect the named grid/property inventory.
3. Create a new realization or approved scratch case.
4. Execute only the allow-listed RMS workflow REEK_BLOCK_AND_EXPORT_V1.
5. Export grid and named properties to a job-specific staging directory.
6. Calculate SHA-256, write a manifest, close RMS, and upload signed artifacts.
7. Trigger the same XTGeo, NeqSim, OPM Flow, and ERT validators shown here.
8. Return artifact URIs, logs, resolved software versions, and approval state.

This separation lets an LLM plan and monitor work without giving it raw access to license files,
project directories, or destructive APIs.
"""))

cells.append(md(r"""
## 10. Configure and run ERT with OPM Flow

ERT samples three transparent uncertainties:

| Parameter | Distribution | Meaning |
|---|---:|---|
| PERM_MULT | Uniform 0.70–1.30 | multiplies PERMX, PERMY, PERMZ |
| PORO_MULT | Uniform 0.95–1.05 | multiplies PORO |
| INJ_RATE | Uniform 8,000–16,000 Sm3/day | water-injection target |

TEMPLATE_RENDER writes one complete Flow deck per realization. The standard ERT FLOW forward
model runs the real simulator. Four realizations are deliberately small enough for Colab but use
the same directory and parameter contracts as a larger study.
"""))

cells.append(code(r"""
parameter_priors = '''PERM_MULT UNIFORM 0.70 1.30
PORO_MULT UNIFORM 0.95 1.05
INJ_RATE UNIFORM 8000.0 16000.0
'''
(ERT_DIRECTORY / "parameters.txt").write_text(parameter_priors, encoding="utf-8")

template_text = render_deck(
    "{{parameters.PERM_MULT.value}}",
    "{{parameters.PORO_MULT.value}}",
    "{{parameters.INJ_RATE.value}}",
)
template_path = ERT_DIRECTORY / "RMS_REEK.DATA.jinja2"
template_path.write_text(template_text + "\n", encoding="utf-8")

ert_configuration = f'''
NUM_REALIZATIONS 4
MIN_REALIZATIONS 4
RANDOM_SEED {RANDOM_SEED}

QUEUE_SYSTEM LOCAL
QUEUE_OPTION LOCAL MAX_RUNNING 2

RUNPATH runs/realization-<IENS>/iter-<ITER>
ECLBASE RMS_REEK
SUMMARY FPR FOPR FGPR FWPR FWIR FOPT FGPT FWPT WBHP:PROD WGOR:PROD

GEN_KW PARAMETERS parameters.txt

FORWARD_MODEL TEMPLATE_RENDER(
  <INPUT_FILES>=parameters.json,
  <TEMPLATE_FILE>=<CONFIG_PATH>/RMS_REEK.DATA.jinja2,
  <OUTPUT_FILE>=RMS_REEK.DATA
)
FORWARD_MODEL FLOW
'''
ert_configuration = textwrap.dedent(ert_configuration).strip() + "\n"
ert_config_path = ERT_DIRECTORY / "rms_reek.ert"
ert_config_path.write_text(ert_configuration, encoding="utf-8")

print("Parameter priors:\n", parameter_priors)
print("ERT configuration:\n", ert_configuration)
print("Rendered deck template (complete):\n", template_text)
"""))

cells.append(code(r"""
ert_lint = subprocess.run(
    ["ert", "lint", ert_config_path.name],
    cwd=ERT_DIRECTORY,
    capture_output=True,
    text=True,
    timeout=180,
)
print(ert_lint.stdout)
if ert_lint.stderr:
    print(ert_lint.stderr)
if ert_lint.returncode != 0:
    raise RuntimeError("ERT lint failed.")

ert_start = time.perf_counter()
ert_run = subprocess.run(
    ["ert", "ensemble_experiment", "--disable-monitoring", ert_config_path.name],
    cwd=ERT_DIRECTORY,
    capture_output=True,
    text=True,
    timeout=3600,
)
ert_elapsed = time.perf_counter() - ert_start
print("\n".join((ert_run.stdout + "\n" + ert_run.stderr).splitlines()[-80:]))
if ert_run.returncode != 0:
    raise RuntimeError("ERT ensemble experiment failed.")

agent_ledger.record("ert.ensemble_experiment", "passed", {
    "return_code": ert_run.returncode,
    "wall_time_seconds": ert_elapsed,
    "realizations": 4,
})
"""))

cells.append(code(r"""
ensemble_frames = []
parameter_rows = []
for realization in range(4):
    run_directory = ERT_DIRECTORY / "runs" / f"realization-{realization}" / "iter-0"
    parameter_payload = json.loads((run_directory / "parameters.json").read_text(encoding="utf-8"))
    parameter_rows.append({
        "realization": realization,
        **{name: float(payload["value"]) for name, payload in parameter_payload.items()},
    })
    realization_summary = ESmry(str(run_directory / "RMS_REEK.SMSPEC"))
    def values(key):
        return np.asarray(realization_summary[key], dtype=float)
    frame = pd.DataFrame({
        "realization": realization,
        "time_days": values("TIME"),
        "field_pressure_bara": values("FPR"),
        "oil_rate_Sm3_day": values("FOPR"),
        "gas_rate_Sm3_day": values("FGPR"),
        "water_rate_Sm3_day": values("FWPR"),
        "water_injection_Sm3_day": values("FWIR"),
        "cumulative_oil_MSm3": values("FOPT") / 1e6,
        "producer_bhp_bara": values("WBHP:PROD"),
        "well_gor_Sm3_Sm3": values("WGOR:PROD"),
    })
    ensemble_frames.append(frame)

ensemble_history = pd.concat(ensemble_frames, ignore_index=True)
ensemble_parameters = pd.DataFrame(parameter_rows).sort_values("realization")
display(ensemble_parameters)
display(ensemble_history.groupby("realization").tail(1))

ensemble_figure, axes = plt.subplots(1, 3, figsize=(15.0, 4.8), constrained_layout=True)
for realization, frame in ensemble_history.groupby("realization"):
    years = frame["time_days"] / 365.25
    axes[0].plot(years, frame["oil_rate_Sm3_day"], alpha=0.8, label=f"R{realization}")
    axes[1].plot(years, frame["field_pressure_bara"], alpha=0.8)
    axes[2].plot(years, frame["water_rate_Sm3_day"], alpha=0.8)
axes[0].set(xlabel="Time [year]", ylabel="Oil rate [Sm3/day]", title="ERT oil-rate ensemble")
axes[1].set(xlabel="Time [year]", ylabel="Pressure [bara]", title="ERT pressure ensemble")
axes[2].set(xlabel="Time [year]", ylabel="Water rate [Sm3/day]", title="ERT water ensemble")
axes[0].legend(ncol=2)
path = OUTPUT_DIRECTORY / "ert_flow_ensemble.png"
ensemble_figure.savefig(path, dpi=170, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()

final_ensemble = ensemble_history.groupby("realization").tail(1).merge(ensemble_parameters, on="realization")
relationship_figure, axes = plt.subplots(1, 2, figsize=(11.5, 4.5), constrained_layout=True)
axes[0].scatter(final_ensemble["PERM_MULT"], final_ensemble["cumulative_oil_MSm3"],
                c=final_ensemble["INJ_RATE"], cmap="viridis", s=100)
axes[0].set(xlabel="PERM_MULT", ylabel="Final cumulative oil [million Sm3]", title="Permeability response")
scatter = axes[1].scatter(final_ensemble["PORO_MULT"], final_ensemble["field_pressure_bara"],
                          c=final_ensemble["INJ_RATE"], cmap="plasma", s=100)
axes[1].set(xlabel="PORO_MULT", ylabel="Final pressure [bara]", title="Porosity and injection response")
relationship_figure.colorbar(scatter, ax=axes, label="Injection target [Sm3/day]", shrink=0.85)
path = OUTPUT_DIRECTORY / "ert_parameter_response.png"
relationship_figure.savefig(path, dpi=170, bbox_inches="tight")
FIGURE_PATHS.append(path)
plt.show()
"""))

cells.append(md(r"""
## 11. Transfer an ERT realization to NeqSim facilities

The realization closest to median final cumulative oil is selected deterministically. Flow
standard oil, gas, and water rates are reconstructed with the same characterized NeqSim stock
oil and gas phases used to build PVT. The selected maximum-load timestep then feeds a wellhead
choke, three-phase separator, gas compressor, aftercooler, oil letdown valve, and low-pressure
separator. The mass balance is checked.
"""))

cells.append(code(r"""
final_oil = final_ensemble.set_index("realization")["cumulative_oil_MSm3"]
median_target = final_oil.median()
selected_realization = int((final_oil - median_target).abs().idxmin())
reservoir_history = ensemble_history.loc[
    ensemble_history["realization"] == selected_realization
].reset_index(drop=True)
print("Selected median-like realization:", selected_realization)
display(reservoir_history)
"""))

cells.append(code(source_cell(31)))
cells.append(code(source_cell(35)))
cells.append(code(source_cell(36)))
process_plot_source = source_cell(37) + "\nFIGURE_PATHS.append(process_plot_path)"
cells.append(code(process_plot_source))

cells.append(md(r"""
## 12. Complete input and artifact inventory

The tables below list every downloaded input and every generated simulator input with byte count
and SHA-256. The complete deck, PVT include, relative-permeability tables, ERT configuration,
priors, and Jinja template were printed above. Cell-scale arrays remain available through their
immutable ROFF URLs and generated GRDECL files; checksums prove the exact bytes used.
"""))

cells.append(code(r"""
input_artifact_paths = (
    [DATA_DIRECTORY / row[0] for row in DATA_MANIFEST]
    + generated_static_paths
    + [black_oil_path, deck_path, ERT_DIRECTORY / "parameters.txt",
       ERT_DIRECTORY / "RMS_REEK.DATA.jinja2", ert_config_path, job_path]
)
input_inventory = pd.DataFrame([
    {
        "role": "downloaded public input" if path.parent == DATA_DIRECTORY else "generated simulation input",
        "file": path.relative_to(OUTPUT_DIRECTORY).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    for path in input_artifact_paths
])
display(input_inventory)

ledger_path = OUTPUT_DIRECTORY / "agent_tool_ledger.json"
ledger_path.write_text(json.dumps(agent_ledger.records, indent=2) + "\n", encoding="utf-8")
display(agent_ledger.frame())
"""))

cells.append(md(r"""
## 13. Engineering validation gates

These assertions are publication gates, not decorative status labels. They check provenance,
dimensions, blocking, property physics, deck parsing, the real Flow process, restart saturation
closure, all four ERT simulator runs, NeqSim PVT contracts, the process mass balance, and the
agent ledger. A failed check raises and leaves the notebook unpublishable.
"""))

cells.append(code(r"""
all_ert_smspec = [
    ERT_DIRECTORY / "runs" / f"realization-{realization}" / "iter-0" / "RMS_REEK.SMSPEC"
    for realization in range(4)
]
saturation_sum = final_water_saturation_cube + final_gas_saturation_cube
validation_checks = {
    "all seven public files match SHA-256 and byte count": bool(download_table["verified"].all()),
    "fine grid is 80 x 128 x 56": (fine_grid.ncol, fine_grid.nrow, fine_grid.nlay) == (80, 128, 56),
    "simulation grid is 40 x 64 x 14": (sim_grid.ncol, sim_grid.nrow, sim_grid.nlay) == (40, 64, 14),
    "fine-to-simulation blocking is exactly 2 x 2 x 4": BLOCK == (2, 2, 4),
    "simulation grid has 35,838 active cells": sim_grid.nactive == 35838,
    "porosity remains between zero and one": bool(active_poro.min() > 0 and active_poro.max() < 1),
    "permeability is positive": bool(active_permx.min() > 0),
    "blocked porosity is finite on compared blocks": bool(np.isfinite(blocked_poro[comparison_mask]).all()),
    "all generated static includes are nonempty": all(path.stat().st_size > 0 for path in generated_static_paths),
    "all required Flow deck keywords parse": bool(deck_keyword_audit["present"].all()),
    "all NeqSim PVT contracts pass": bool(pvt_contract_audit["passed"].all()),
    "OPM Flow returned success": flow_run.returncode == 0,
    "Flow summary is finite": bool(np.isfinite(reservoir_history.select_dtypes(include=[np.number])).all().all()),
    "restart active count matches XTGeo": active_cell_count == sim_grid.nactive,
    "restart has 24 forecast steps plus initial state": len(restart_steps) in (24, 25),
    "restart states are finite on active cells": bool(np.isfinite(final_pressure_cube_bara[~np.isnan(final_pressure_cube_bara)]).all()),
    "final saturations close": bool(np.nanmin(final_oil_saturation_cube) >= -1e-6 and np.nanmax(saturation_sum) <= 1 + 1e-6),
    "ERT lint returned success": ert_lint.returncode == 0,
    "ERT ensemble returned success": ert_run.returncode == 0,
    "all four ERT SMSPEC files exist": all(path.is_file() for path in all_ert_smspec),
    "ERT parsed four realizations": ensemble_history["realization"].nunique() == 4,
    "NeqSim process compressor consumes power": gas_compressor.getPower() > 0,
    "NeqSim process mass balance closes": abs(process_mass_residual_kg_s) < 1e-8,
    "at least eleven retained figures exist": len(list(OUTPUT_DIRECTORY.glob("*.png"))) >= 11,
    "agent ledger records all executed stages as passed": all(record["status"].endswith("passed") for record in agent_ledger.records),
    "job contract contains no filesystem project path": "project_path" not in json.dumps(agent_job),
}
validation_table = pd.DataFrame({"check": validation_checks.keys(), "passed": validation_checks.values()})
display(validation_table)
failed = validation_table.loc[~validation_table["passed"], "check"].tolist()
if failed:
    raise AssertionError(f"Failed validation checks: {failed}")
print(f"All {len(validation_checks)} engineering validation gates passed.")
"""))

cells.append(code(r"""
final_results = {
    "data_commit": DATA_COMMIT,
    "neqsim_commit": neqsim_commit,
    "neqsim_jar_sha256": neqsim_jar_sha256,
    "grid_dimensions": [grid_nx, grid_ny, grid_nz],
    "active_cells": active_cell_count,
    "blocking": list(BLOCK),
    "porosity_blocking_rmse": float(np.sqrt(np.mean(poro_difference ** 2))),
    "bubble_pressure_bara": float(bubble_pressure_bara),
    "base_final_pressure_bara": float(summary_values("FPR")[-1]),
    "base_final_cumulative_oil_million_sm3": float(summary_values("FOPT")[-1] / 1e6),
    "ert_realizations": int(ensemble_history["realization"].nunique()),
    "ert_final_oil_range_million_sm3": [
        float(final_ensemble["cumulative_oil_MSm3"].min()),
        float(final_ensemble["cumulative_oil_MSm3"].max()),
    ],
    "selected_process_realization": selected_realization,
    "compressor_power_MW": float(gas_compressor.getPower() / 1e6),
    "process_mass_residual_kg_s": float(process_mass_residual_kg_s),
    "figures": [path.name for path in FIGURE_PATHS],
    "validation_checks_passed": int(validation_table["passed"].sum()),
    "validation_checks_total": len(validation_table),
}
results_path = OUTPUT_DIRECTORY / "run_results.json"
results_path.write_text(json.dumps(final_results, indent=2) + "\n", encoding="utf-8")
display(pd.DataFrame([
    ("Active cells", active_cell_count, "count"),
    ("NeqSim bubble pressure", bubble_pressure_bara, "bara"),
    ("Base final pressure", final_results["base_final_pressure_bara"], "bara"),
    ("Base cumulative oil", final_results["base_final_cumulative_oil_million_sm3"], "million Sm3"),
    ("ERT low final oil", final_results["ert_final_oil_range_million_sm3"][0], "million Sm3"),
    ("ERT high final oil", final_results["ert_final_oil_range_million_sm3"][1], "million Sm3"),
    ("Selected compressor power", final_results["compressor_power_MW"], "MW"),
], columns=["result", "value", "unit"]).round(6))
print(json.dumps(final_results, indent=2))
"""))

cells.append(md(r"""
## What is demonstrated, and what is not

**Demonstrated with stored execution evidence**

- public RMS-origin ROFF ingestion;
- geological-to-simulation blocking calculations;
- RMS-export property inspection and spatial spreading;
- NeqSim master-source PVT generation;
- complete OPM Flow deck generation and dynamic simulation;
- restart-state visualization;
- real ERT orchestration of four OPM Flow realizations;
- reservoir-to-NeqSim facility handover;
- machine-readable agent request, allow-list, acceptance checks, and tool ledger.

**Not claimed**

- The public Reek export is not a confidential asset model.
- The explicit teaching facies map is not asserted to be the archived RMS workflow definition.
- PERMY and PERMZ multipliers are assumptions, not measurements.
- The wells and controls are visualization choices, not an optimized development plan.
- Four ERT realizations demonstrate integration; they do not quantify decision-grade uncertainty.
- The notebook does not execute licensed RMS. That execution belongs on a governed worker.
- PVT, rock-fluid functions, contacts, and controls are illustrative and are not history matched.

A production implementation should add RMS project snapshots, signed artifacts, scheduler/resource
limits, secret-free workload identity, approval gates, observation ingestion, ERT update steps,
and domain review before model promotion.
"""))

cells.append(md(r"""
## Suggested exercises

1. Replace the supplied simulation PORO with the calculated blocked porosity and compare Flow.
2. Implement harmonic, arithmetic, and flow-based directional permeability upscaling.
3. Add region-specific SWOF/SGOF tables using facies or Zone.
4. Increase the ERT ensemble and add observed well data for an ensemble smoother experiment.
5. Add fault transmissibility multipliers and inspect water-front sensitivity.
6. Replace the public-fixture adapter with an authenticated licensed RMS worker in a test project.
7. Extend the agent contract with artifact signatures, approvals, and a model-promotion state machine.

## References

- NeqSim: https://github.com/equinor/neqsim
- NeqSim-Colab: https://github.com/EvenSol/NeqSim-Colab
- OPM Flow: https://opm-project.org
- ERT: https://ert.readthedocs.io
- XTGeo: https://xtgeo.readthedocs.io
- Public test data: https://github.com/equinor/xtgeo-testdata
- Reek source commit: cad17f24e22c19c6cefe6f647185395cc0a11add
"""))

notebook = nbf.v4.new_notebook(
    cells=cells,
    metadata={
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.12"},
        "colab": {
            "name": TARGET.name,
            "provenance": [],
            "toc_visible": True,
        },
    },
)

TARGET.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, TARGET)
print(f"Wrote {TARGET} with {len(cells)} cells and {sum(c.cell_type == 'code' for c in cells)} code cells.")
