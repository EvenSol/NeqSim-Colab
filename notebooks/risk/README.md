# NeqSim risk and reliability notebook

This folder contains a single Colab-ready end-to-end example for the NeqSim operational risk framework documented at https://equinor.github.io/neqsim/risk/index.html.

## Notebook

[NeqSim risk framework: process risk, availability, LOPA and SIS](neqsim_risk_framework_complete.ipynb) — builds a NeqSim gas-process model and connects it to production-impact analysis, equipment criticality, degraded-operation optimization, reliability data, Monte Carlo production availability, initiating-event analysis, independent protection layers, a safety instrumented function, LOPA validation, and PFD sensitivity.

The notebook follows one coherent chain:

**process model → equipment failure consequence → degraded operation → reliability and Monte Carlo availability → LOPA/SIS protection layers → residual risk**

The final section shows how the same structure can be used in an agentic NeqSim workflow and identifies natural extensions such as dynamic risk, bow-tie/barrier analysis, condition-based reliability, real-time risk monitoring, portfolio risk, and economic consequence integration.

## Execution status

The notebook was executed top-to-bottom on GitHub Actions with the public `neqsim` 3.20.0 Python package on Python 3.12. Execution outputs and plots are retained in the notebook. The executable LOPA check closes exactly for the demonstrated assumptions: initiating-event frequency 0.1/year × BPCS PFD 0.1 × SIF PFD 0.005 = 5.0e-5/year, with total RRF 2000.

The production-impact example also demonstrates an important safeguard in the current API: a complete compressor trip that leaves nominal mass flow unchanged is returned as `MANUAL_REVIEW` rather than being accepted as confirmed zero production loss. A real study should define the saleable-product specification or topology/isolation consequence explicitly before crediting that flow.

## Engineering-use boundary

The example demonstrates software behavior and workflow patterns. Reliability rates, initiating-event frequencies, PFD values, consequence categories, SIL targets, proof-test assumptions, and barrier independence must come from an approved and traceable engineering basis before results are used for real decisions.
