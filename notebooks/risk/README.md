# NeqSim risk and reliability notebook

This folder contains a single Colab-ready end-to-end example for the NeqSim operational risk framework documented at https://equinor.github.io/neqsim/risk/index.html.

## Notebook

[NeqSim risk framework: process risk, availability, LOPA and SIS](neqsim_risk_framework_complete.ipynb) — builds a NeqSim gas-process model and connects it to production-impact analysis, equipment criticality, degraded-operation optimization, reliability data, Monte Carlo production availability, initiating-event analysis, independent protection layers, a safety instrumented function, LOPA validation, and PFD sensitivity.

The notebook follows one coherent chain:

**process model → equipment failure consequence → degraded operation → reliability and Monte Carlo availability → LOPA/SIS protection layers → residual risk**

The final section shows how the same structure can be used in an agentic NeqSim workflow and identifies natural extensions such as dynamic risk, bow-tie/barrier analysis, condition-based reliability, real-time risk monitoring, portfolio risk, and economic consequence integration.

## Engineering-use boundary

The example demonstrates software behavior and workflow patterns. Reliability rates, initiating-event frequencies, PFD values, consequence categories, SIL targets, proof-test assumptions, and barrier independence must come from an approved and traceable engineering basis before results are used for real decisions.
