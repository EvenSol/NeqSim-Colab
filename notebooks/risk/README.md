# NeqSim risk and reliability notebooks

This folder contains Colab-ready examples for the NeqSim operational risk framework documented at https://equinor.github.io/neqsim/risk/index.html.

## Notebooks

1. [Operational risk, availability, and production impact](operational_risk_and_availability.ipynb) — builds a NeqSim gas-process model and connects it to production-impact analysis, degraded-operation optimization, reliability data, and Monte Carlo production availability.
2. [LOPA and safety-instrumented risk analysis](lopa_sis_risk_framework.ipynb) — demonstrates the current `SISIntegratedRiskModel` and `SafetyInstrumentedFunction` APIs, validates the LOPA arithmetic independently, and adds a PFD sensitivity study.

## Recommended learning path

Start with the operational-risk notebook to see how process simulation becomes the physics basis for risk consequences. Continue with the LOPA/SIS notebook to see how initiating events and independent protection layers are represented. Follow-on notebooks can cover dynamic risk, bow-tie/barrier analysis, condition-based reliability, real-time risk monitoring, multi-asset portfolio risk, and topology/dependency propagation.

## Engineering-use boundary

The examples demonstrate software behavior and workflow patterns. Reliability rates, initiating-event frequencies, PFD values, consequence categories, SIL targets, proof-test assumptions, and barrier independence must come from an approved and traceable engineering basis before results are used for real decisions.
