# Volve field evaluation notebook series

This series connects the Equinor Volve Data Village from seismic and well logs
through reservoir, wells, SURF, facilities, field constraints, uncertainty, and
decisions. The Databricks Marketplace listing is the authoritative input
boundary. The notebooks never redistribute the full Volve package.

## Volve field calculations

Run the notebooks in order; each notebook reads the preceding versioned
handoff contract and refuses to present teaching fixtures as measured data:

1. [01 - seismic, wells, and static model](01_volve_seismic_wells_static_model.ipynb)
2. [02 - PVT, black oil, and reservoir](02_volve_pvt_blackoil_reservoir.ipynb)
3. [03 - wells, SURF, and flow assurance](03_volve_wells_surf_flow_assurance.ipynb)
4. [04 - facilities and processing](04_volve_facilities_processing.ipynb)
5. [05 - integrated field twin and decisions](05_volve_integrated_field_twin.ipynb)

Marketplace mode is the normal default. Provide either a mounted or exported
VOLVE_VOLUME_ROOT, or a VOLVE_REMOTE_VOLUME_ROOT together with Databricks host
and token secrets. Individual asset paths can be selected with the environment
variables documented in each notebook. In Colab, keep DATABRICKS_HOST and
DATABRICKS_TOKEN in Colab Secrets; do not paste credentials into a notebook.

The stored clean-runtime validation was made with deterministic teaching
fixtures by setting VOLVE_VALIDATION_MODE=1. Every fixture output is marked
DEMONSTRATION_FALLBACK. It is not measured Volve data, a history match, a
reserves statement, or a design certification.

## Acceptance status

- Five notebooks execute cleanly in the explicit validation mode with stored
  outputs, 14 inspected figures, 10 inspected display equations, and no error
  or stderr outputs.
- Normal execution defaults to Marketplace mode and stops if the installed
  Volve Volume is not configured; it does not silently substitute teaching
  data.
- Measured-data acceptance requires the installed path in the form
  `/Volumes/<catalog>/<schema>/<volume>` and an authenticated run. Keep tokens
  in Colab Secrets or the environment, never in version-controlled cells.
- The collection downloads only explicitly selected files and does not
  redistribute the complete Volve package.
