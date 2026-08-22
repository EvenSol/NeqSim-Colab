# Volve field evaluation notebook series

This is the principal NeqSim-Colab educational and validation collection for a
complete field lifecycle. It connects the Equinor Volve Data Village from
seismic and well logs through static scenarios, OPM Flow, reservoir history
matching, producer/injector placement, wells, SURF, facilities, constrained
operations, late life, shutdown, and decommissioning. The Databricks
Marketplace listing is the authoritative input boundary. The notebooks never
redistribute the full Volve package.

Use the [NeqSim Field Development and Operations book](https://equinor.github.io/neqsimhome/doc/field_development_and_operations/book_standalone.html)
as the conceptual companion. The book explains the general lifecycle,
production-technology, SURF, process, optimization, economics, and operations
topics; this series applies them to one governed Volve field case.

## Volve field calculations

Run the notebooks in order; each notebook reads the preceding versioned
handoff contract and refuses to present teaching fixtures as measured data:

1. [01 - seismic, wells, and static model](01_volve_seismic_wells_static_model.ipynb)
2. [02 - PVT, black oil, and reservoir](02_volve_pvt_blackoil_reservoir.ipynb)
3. [03 - wells, SURF, and flow assurance](03_volve_wells_surf_flow_assurance.ipynb)
4. [04 - facilities and processing](04_volve_facilities_processing.ipynb)
5. [05 - integrated field twin and decisions](05_volve_integrated_field_twin.ipynb)
6. [06 - reservoir simulation and production history matching](06_volve_reservoir_history_matching.ipynb)
7. [07 - all wells, nodal analysis, gathering, and full SURF](07_volve_all_wells_gathering_surf.ipynb)
8. [08 - closed-loop full-field development and operations](08_volve_closed_loop_field_development_operations.ipynb)

## Principal collection requirements

| Requirement | Calculated evidence | Primary notebooks | Saved acceptance status |
|---|---|---|---|
| SEG-Y interpretation with `segyio` | geometry, amplitude QC, horizons, discontinuity and depth conversion | 01 | executed teaching fixture; measured SEG-Y acceptance pending |
| Static model and development scenarios | petrophysics, STOIIP uncertainty, opportunity grid and 3P-1I to 5P-2I cases | 01, 02, 08 | executed teaching scenarios |
| OPM Flow simulation and history matching | deck contract, schedule records, parameter ensemble, four-vector objective and OPM summary alignment | 02, 06, 08 | reduced bridge executed; complete measured OPM case pending |
| Producer and injector placement | geological score, spacing, injectivity context, `WELSPECS`, `COMPDAT`, production and injection controls | 03, 08 | executed teaching placement |
| IPR/VLP and nodal analysis | bubble-point IPR, NeqSim-calibrated VLP, chokes, branches and operating points | 03, 07 | executed for all teaching-case producers |
| Complete wells and gathering system | five producers, two manifolds, two trunks, common riser and host boundary | 07 | algebraic and direct NeqSim verification executed |
| Separation, compression, water, export and injection | three-phase processing, gas compression, oil export, water treatment, NeqSim water density and injection power | 04, 08 | executed teaching facilities |
| Facility feedback to reservoir optimization | hard oil, liquid, gas, water and injection constraints in monthly choke/injection optimization | 05, 08 | executed teaching closed loop |
| Late life, shutdown and decommissioning | turndown, outage, hydrate window, economic limit, P&A inventory, removal and cost uncertainty | 07, 08 | executed teaching cessation screen |

## Field-development and operations lifecycle

| Lifecycle stage | Volve calculations | Primary notebooks |
|---|---|---|
| Discovery and framing | seismic interpretation, well ties, rock physics, petrophysics, static uncertainty, STOIIP | 01 |
| Fluid and reservoir basis | compositional PVT, DLE, black-oil source tables, initialization, material balance | 02 |
| Development concept | well count and placement context, IPR/VLP, tubing, chokes, flowlines, manifolds, riser | 03 and 07 |
| Facilities design | inlet conditioning, separation, stabilization, compression, water, utilities, emissions, safety | 04 |
| Operate and optimize | measured production QA, history matching, allocation, bottlenecks, interventions, economics | 05 and 06 |
| Late life and shutdown | turndown, well outage, integrity, cooldown, hydrate exposure, restart, economic limit and decommissioning evidence | 03, 05, 07, and 08 |

Notebook 6 executes a reduced communicating two-tank reservoir simulator and
fits pressure, oil, gas, and water simultaneously. Notebook 7 represents every
active producer with IPR, NeqSim-calibrated tubing VLP, choke and branch loss,
two gathering manifolds, two trunks, a common riser, and the facility inlet. It
also evaluates peak, mature, late-life, outage, turndown, shutdown, cooldown,
and restart cases. Notebook 8 closes the loop with explicit development
scenarios, producer/injector placement, OPM schedule generation, an OPM-primary
history-match ensemble path, facility-constrained reservoir controls, water
injection power, economic-limit timing, and decommissioning uncertainty.

Marketplace mode is the normal default. Provide either a mounted or exported
VOLVE_VOLUME_ROOT, or a VOLVE_REMOTE_VOLUME_ROOT together with Databricks host
and token secrets. Individual asset paths can be selected with the environment
variables documented in each notebook. In Colab, keep DATABRICKS_HOST and
DATABRICKS_TOKEN in Colab Secrets; do not paste credentials into a notebook.

The stored clean-runtime validation was made with deterministic teaching
fixtures. Notebook 02 enables them by setting VOLVE_VALIDATION_MODE=1; the
other notebooks use the validation setup documented in their own setup cells.
Every fixture output is marked DEMONSTRATION_FALLBACK. It is not measured Volve
data, a history match, a reserves statement, or a design certification.

## Acceptance status

- All eight notebooks execute cleanly in the explicit validation mode with
  retained outputs. Exact code-cell, figure, equation, and engineering-check
  evidence is recorded in the Volve maintenance-ledger shard.
- Notebook 02 installs the newest released NeqSim distribution from public
  PyPI with the unpinned `!pip install neqsim` command. It no longer clones or
  builds NeqSim source and does not inject a custom JAR classpath.
- Normal execution defaults to Marketplace mode and stops if the installed
  Volve Volume is not configured; it does not silently substitute teaching
  data.
- Measured-data acceptance requires the installed path in the form
  `/Volumes/<catalog>/<schema>/<volume>` and an authenticated run. Keep tokens
  in Colab Secrets or the environment, never in version-controlled cells.
- The collection downloads only explicitly selected files and does not
  redistribute the complete Volve package.
