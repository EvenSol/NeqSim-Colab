# Introduction to Gas Processing using NeqSim in Colab
This GitHub repository is the code and notebook base for the web module [Introduction to Gas Processing using NeqSim in Colab](/notebooks/examples_of_NeqSim_in_Colab.ipynb).

NeqSim Python/Colab is part of the [NeqSim project](https://equinor.github.io/neqsimhome/). NeqSim (Non-Equilibrium Simulator) is a Java library for estimation of fluid behavior and process design. The basis for NeqSim is a library of fundamental mathematical models related to phase behavior and physical properties of fluids.

Advanced notebooks use the released Python distribution only as the JPype bridge. They clone current [`equinor/neqsim`](https://github.com/equinor/neqsim) `master`, build the Java runtime JAR, record the resolved commit and SHA-256 digest, and verify that Java classes were loaded from that JAR before running calculations.

[NeqSim (Non-Equilibrium Simulator)](https://equinor.github.io/neqsimhome/) is a library for estimation of fluid behaviour for oil and gas production. Colaboratory (Colab) is a free Jupyter notebook environment that requires no setup and runs entirely in the cloud. In the notebooks listed in this page you will find examples of typical gas processing calculations using NeqSim in Colab, and will serve both as introduction to natural gas processing and to interactive use of NeqSim in a Python based notebook. The notebooks serves as a theoretical introduction and as a simulation tool for many processes found in the gas industry.

## Featured notebooks

* [The AI Asset Team: tie-back and debottlenecking](notebooks/AI/agentic_asset_team_tieback_and_debottlenecking.ipynb) – One executed industrial study combining fixed compressor maps, protected host production, constrained optimization, derating recovery, uncertainty, five-year economics, retained graphics, an audited investigation replay and an optional live language-model agent. Uses pinned NeqSim source; local source reuse is available through `NEQSIM_SOURCE_ROOT`/`NEQSIM_SOURCE_JAR`. Live mode uses `OPENAI_API_KEY` and optional `OPENAI_MODEL`; credentials are never stored in outputs.

* [Mechanical design to interactive 3D equipment](notebooks/process/mechanical_design_to_3d_models.ipynb) – Generate separator and compressor models from calculated NeqSim dimensions, inspect cutaways, compare flow cases, and exchange qualified STL/GLB/JSON artifacts.

* [Hot-oil commissioning and ML risk screening](notebooks/flowassurance/hot_oil_commissioning_neqsim_ml.ipynb) – Combine NeqSim properties, wax, thermal resistance and a native heater/pipeline process with a conservative transient displacement model, numerical checks, RF/MLP surrogates and explicit gel-restart assumptions.
* [open-DARTS waterflood simulation and a NeqSim process handoff](notebooks/reservoir/open_darts_waterflood_to_neqsim.ipynb) – Build and validate an open-DARTS reservoir model, exercise well controls, check analytical and numerical sensitivity, and transfer component rates into NeqSim; connect the tutorial to the existing OPM Flow, RMS, and ERT examples.
* [Elemental sulfur in oil stabilization and gas recompression](notebooks/process/elemental_sulfur_stabilization_recompression.ipynb) – Calculate H2S/O2 equilibrium and kinetics, sulfur deposition, rust/FeS effects, separator oil/condensate carryover, compressor fouling, and potential mitigation and cleaning measures.
* [LNG process simulation and benchmark comparison](notebooks/process/LNG_Process_Benchmark_Comparison.ipynb) – Run closed-loop SMR, C3MR, DMR, and nitrogen-expander models with common KPIs, literature checks, and an exchanger grid-convergence study.
* [IoT and Industry 4.0 with NeqSim](notebooks/AI/IoT_and_Industry4.0_with_NeqSim.ipynb) – Build an instrumented digital twin, stream dynamic simulation data, and explore Industry 4.0 workflows backed by NeqSim measurements.
* [Plant-data reconciliation and a Bayesian digital twin](notebooks/process/data_reconciliation_bayesian_digital_twin.ipynb) – Qualify historian windows, reconcile redundant meters, isolate gross errors, calibrate compressor efficiency, validate a Bayesian posterior, and propagate uncertainty to an operating decision.
* [Seismic acquisition to RMS-ready subsurface inputs](notebooks/reservoir/seismic_to_rms_input_workflow.ipynb) – Calculate CMP moveout and stacking, interpret public Reek seismic and wells, validate horizons and faults, screen seismic attributes, and export a checked RMS import package.
* [RMS-origin reservoir to OPM Flow, ERT, and NeqSim](notebooks/reservoir/rms_to_opm_flow_agent_ert.ipynb) – Audit public Reek ROFF exports, demonstrate blocking and property spreading, run OPM Flow and ERT, and define a governed RMS-agent contract.

## Getting Started
See the [NeqSim Colab page](https://colab.research.google.com/github/EvenSol/NeqSim-Colab/blob/master/notebooks/examples_of_NeqSim_in_Colab.ipynb) for how to start using NeqSim in Colab/Python.

## Contributing
See the [NeqSim Colab page](https://colab.research.google.com/github/EvenSol/NeqSim-Colab/blob/master/notebooks/examples_of_NeqSim_in_Colab.ipynb). Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.

Repository-wide notebook integrity is checked with `python scripts/check_notebook.py --all`. New main-source notebooks must additionally pass `python scripts/check_notebook.py PATH --require-main-source` after clean execution.


