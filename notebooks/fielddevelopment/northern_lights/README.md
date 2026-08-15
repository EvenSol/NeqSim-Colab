# Northern Lights open data and NeqSim notebook series

This section turns the Northern Lights open-data boundary into traceable CCS
engineering models. It follows the chain from capture-stream evidence through
conditioning, ship and terminal receipt, dense-phase transport, injection,
storage, surveillance, operations, expansion, and late-life decisions.

The [Equinor Northern Lights Databricks Marketplace listing][marketplace] is the
authoritative route to the full shared package. The repository bundles only
four small licensed Eos snapshots so that the data-foundation notebook can run
without credentials. See [DATA_ATTRIBUTION.md](DATA_ATTRIBUTION.md) before
redistributing or adapting them.

Use the [NeqSim Field Development and Operations book][book] as the conceptual
companion. NeqSim owns thermodynamics, fluid properties, wells, pipelines,
facilities, process dynamics, and operations screening in this series. OPM Flow
owns dynamic storage-reservoir simulation; the notebooks define an explicit
handoff instead of replacing it with a Python tank model.

## Planned learning sequence

Publish and validate the notebooks one at a time so every case remains a clean,
standalone tutorial with retained outputs:

1. [Open-data foundation and NeqSim model basis](01_northern_lights_open_data_foundation.ipynb) — licensed Eos snapshots, Marketplace governance, trajectory and interval QA, public well-test evidence, EOS-CG CO2 properties, hydrostatic injection screening, capacity translation, and OPM Flow/NeqSim handoffs.
2. **CO2 stream thermodynamic basis** — acceptance compositions, impurities,
   water, EOS selection, phase envelope, Joule-Thomson behavior, and
   conditioning envelopes without duplicating the general CO2 tutorials.
3. **Terminal, pipeline, and injection system** — Øygarden receipt and storage,
   pumps/heaters, the offshore pipeline, the injection well, Phase 1 and Phase
   2 operating cases, and steady-state capacity limits.
4. **Eos well test and injectivity** — formation pressure, fluid samples, DST
   reconstruction, pressure-transient evidence, wellbore hydraulics, and an
   injectivity contract.
5. **Thermal and geomechanical screening** — open core and thermo-mechanical
   data coupled to NeqSim pressure-temperature-enthalpy paths and explicit
   stress-model boundaries.
6. **Storage model with OPM Flow** — data-conditioned grid/PVT/saturation and
   schedule inputs, real Flow execution, plume/pressure diagnostics, and a
   versioned reservoir-to-well handoff.
7. **Integrated operations and expansion twin** — normal operation, turndown,
   shutdown, restart, depressurisation, 1.5-to-5 Mt/year expansion, monitoring,
   availability, emissions, economics, uncertainty, and decision gates.

## Data modes

The first notebook defaults to `open-snapshot`. This uses the four bundled,
hash-checked files and labels raw/licensed, interpreted, curated, derived, and
scenario data separately.

To inventory an installed or exported Marketplace volume, set:

```text
NORTHERN_LIGHTS_DATA_MODE=marketplace
NORTHERN_LIGHTS_VOLUME_ROOT=/Volumes/<catalog>/<schema>/<volume>
```

The volume path must exist. The notebook never silently falls back from
Marketplace mode and never prints credentials. In Colab, keep Databricks host
and token values in Secrets if a later notebook downloads selected volume
objects; do not paste tokens into cells.

## Scope and acceptance boundary

- The bundled formation and UCS files are third-party interpretations, not raw
  Equinor records. They are useful for teaching data contracts, not for making
  authoritative stratigraphic or geomechanical claims.
- Public SODIR and Northern Lights facts are cited, dated snapshots. Recheck the
  live sources before a project decision.
- Synthetic cases are labelled `SCENARIO_ASSUMPTION`; derived values retain
  their input lineage. No teaching value is presented as a measurement.
- The series is for learning and screening. It is not an injection permit,
  storage-capacity certification, operating procedure, well design, pipeline
  design, or assurance of containment.

[marketplace]: https://marketplace.databricks.com/details/ea296770-0ee0-4b74-a202-a2c0873add7c/Equinor-ASA_Northern-Lights
[book]: https://equinor.github.io/neqsimhome/doc/field_development_and_operations/book_standalone.html

