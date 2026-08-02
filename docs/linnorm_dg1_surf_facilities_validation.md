# Linnorm DG1 SURF and facilities notebook validation

Validation date: 2026-08-02

Artifact:
`notebooks/fielddevelopment/linnorm_dg1_surf_facilities_design.ipynb`

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
| Catalog notebook `nbformat` validation | passed (catalog unchanged from PR #76) |
| Credential-pattern scan | no matches |

Notebook SHA-256:
`f6faea766946ccd3b5ec5d2dd48eed1cb4572c2f043aa5792a800a5cdd3e004e`

The final notebook acceptance table contains 17 passing calculation and package
gates. The generated 32-file educational handoff ZIP has SHA-256
`a28ebab0fce808a79b21ea11554c9385abbf0adf19fdd14aa484c90b9c00d04e`.

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

- Exported with `nbconvert` to HTML.
- Server-side MathJax converted all 30 notebook equations to self-contained SVG;
  no MathJax conversion errors were present.
- Rendered to a 66-page A3 landscape PDF.
- Inspected all 66 rendered pages through 17 contact sheets.
- Verified headings, equations, code, tabular results, and all 11 figures for
  visibility and clipping after the final render correction.
- Inspected the numbered system-architecture drawing at full resolution and in
  the complete notebook render. Wells, jumpers, four-slot manifold and spare,
  wet-gas flowline, MEG/service line, umbilical, local ESD/chemical system,
  flexible riser, and floating-host interface are readable and mapped to the
  scope table.
- Extracted PDF text contained no raw `$$`, `\\frac`, MathJax error, or conversion
  failure marker.

## Engineering boundary

The notebook deliberately identifies pressure-wall, collapse, and on-bottom
stability calculations as preliminary screens. It omits code checks such as
propagation buckling, combined loading, fatigue, fracture, free spans, upheaval or
lateral buckling, installation, trawl interaction, and material qualification.
The process, amine, utility, emissions, brownfield, cost, and schedule models are
educational screening models. The 50-deliverable matrix is an educational synthesis
from public guidance, not an official Equinor internal checklist. RED and AMBER
items remain explicit hold points; passing notebook assertions does not close them.

No missing NeqSim API capability was encountered during implementation, so no
NeqSim issue was opened.
