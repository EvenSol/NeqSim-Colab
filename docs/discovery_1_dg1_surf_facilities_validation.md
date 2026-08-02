# Discovery 1 DG1 SURF and facilities notebook validation

Validation date: 2026-08-02

Artifact:
`notebooks/fielddevelopment/discovery_1_dg1_surf_facilities_design.ipynb`

This ledger records reproducibility and presentation checks for the educational
DG1 follow-up notebook. It is not an independent engineering verification or an
official DG1 approval record.

## Runtime

- Python 3.12.13
- NeqSim Python 3.16.0
- OpenJDK 17.0.19
- deterministic random seed 2731
- clean, ordered execution in an in-process IPython shell because the validation
  sandbox blocks the TCP sockets used by a normal Jupyter kernel

The notebook's Colab bootstrap cell installs NeqSim 3.16.0 and records the actual
Python, Java, NeqSim, repository, and predecessor revisions during re-execution.

## Execution and static checks

| Check | Result |
|---|---:|
| Notebook cells | 98 |
| Markdown cells | 43 |
| Code cells executed | 55 / 55 |
| Saved outputs | 66 |
| Saved PNG figures | 11 |
| Error outputs | 0 |
| Standard-error streams | 0 |
| Code lines over 100 characters | 0 |
| `nbformat` validation | passed |
| Catalog notebook `nbformat` validation | passed; neutral paths occur once |
| Credential-pattern scan | no matches |

Notebook SHA-256:
`45bcfd1f24c4da97a86fe08562bdde9581d11795f45dcc79c42b62ac7c2c536d`

The final notebook acceptance table contains 17 passing calculation and package
gates. The generated 32-file educational handoff ZIP has SHA-256
`fc7fde7566379e5d6c2ac73d4f1f062b670f2fa84e250878baef6cb86c474c27`.

## Representative reproduced results

| Item | Saved result |
|---|---:|
| Selected candidate | Concept A, 18-inch nominal HP wet-gas tie-back |
| Selected nominal wall | 25.4 mm |
| Base flow | 6.3 MSm3/d |
| Base arrival pressure | 197.94 bara |
| Base arrival temperature | 18.29 degC |
| Base compression power | 4.106 MW |
| Base preheat duty | 5.039 MW |
| Base cooler duty | 7.105 MW |
| Treated-gas CO2 | below 1.0 mol% |
| Synthetic CAPEX P50 | 2,936 million real-2026 USD |
| Synthetic schedule to first gas | 53 months after DG1 |

These are screening values produced from the notebook's synthetic learning basis.
They are not field-validated design values.

## Render and visual review

- Exported the final neutral-labelled notebook with `nbconvert` to HTML.
- Server-side MathJax converted all 30 notebook equations (26 display and four
  inline equations) to self-contained SVG; no conversion errors were present.
- Inspected all 11 regenerated figures at original resolution. Labels, legends,
  axes, units, colors, and layouts were readable and unclipped.
- Inspected the numbered system-architecture drawing at full resolution and in
  the final HTML render. Wells, jumpers, four-slot manifold and spare,
  wet-gas flowline, MEG/service line, umbilical, local ESD/chemical system,
  flexible riser, and floating-host interface are readable and mapped to the
  scope table.
- Searched Markdown, code, non-image outputs, metadata, paths, and OCR text from
  every stored figure for the former asset names; no matches remained.
- The NeqSim notebook checker passed after clean execution and rendering.

## Engineering boundary

The notebook deliberately identifies pressure-wall, collapse, and on-bottom
stability calculations as preliminary screens. It omits code checks such as
propagation buckling, combined loading, fatigue, fracture, free spans, upheaval or
lateral buckling, installation, trawl interaction, and material qualification.
The process, amine, utility, emissions, brownfield, cost, and schedule models are
educational screening models. The 50-deliverable matrix is an educational synthesis
from public guidance, not an official internal company checklist. RED and AMBER
items remain explicit hold points; passing notebook assertions does not close them.

No missing NeqSim API capability was encountered during implementation, so no
NeqSim issue was opened.

## Neutral-label update

The case now uses `Discovery 1`, `Host 1`, and `Host 2` throughout source, stored
outputs, figures, package names, paths, catalog text, and interpretation. These labels
identify a composite educational example and are not aliases for named NCS fields.

## Merge-conflict resolution

The system-architecture drawing and validation additions merged through PR #78
were retained, regenerated with neutral labels, and included in the checks above.
No newer `master` content was discarded while updating PR #79.

## Reservoir-to-host companion validation

The companion reservoir and tie-in notebook remains at
`notebooks/reservoir/ncs_discovery_1_tie_in_opm_neqsim_master.ipynb`. It was run
top to bottom with NeqSim master commit
`ab314d6a0fceafe2f5f2a60213a70b7db3d7fccf` and OPM Flow 2026.04.

| Check | Result |
|---|---:|
| Notebook cells | 103 |
| Code cells executed | 47 / 47 |
| Saved outputs | 51 |
| Saved PNG figures | 8 |
| Error outputs | 0 |
| Standard-error streams | 0 |
| Final acceptance gates | all passed |
| MathJax equations rendered | 164 / 164 |
| Former asset-name matches in source/output/OCR | 0 |
| NeqSim notebook checker | passed |

Companion notebook SHA-256:
`f78284f83921ca9240e29c42f871c2f7ffe273771bf8f1e08c643630d4651e26`.
