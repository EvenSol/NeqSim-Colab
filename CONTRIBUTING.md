# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change. 

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a 
   build.
2. Update the README.md with details of changes to the interface, this includes new environment 
   variables, exposed ports, useful file locations and container parameters.
3. Increase the version numbers in any examples files and the README.md to the new version that this
   Pull Request would represent. The versioning scheme we use is [SemVer](http://semver.org/).
4. You may merge the Pull Request in once you have the sign-off of two other developers, or if you 
   do not have permission to do that, you may request the second reviewer to merge it for you.

## Notebook validation environments

Use the [resilient NeqSim validation environment](docs/validation_environment.md) for clean notebook execution. The bootstrap resolves an immutable public-PyPI wheel snapshot when the index is healthy, verifies every artifact by SHA-256, and creates a fresh no-index environment for every run. This keeps transient package-index or proxy failures out of the notebook-publication critical path without weakening clean-environment validation.

## NeqSim source and notebook integrity

New advanced notebooks must run Java calculations from current `equinor/neqsim` `master`. The released `neqsim` Python distribution may be installed as the JPype bridge, but its bundled Java dependency is not accepted as the demonstrated runtime when main-only functionality is required.

Before importing `neqsim`, a notebook must:

1. clone or fetch `equinor/neqsim` `master` and build its runtime JAR;
2. record the resolved `git rev-parse HEAD` commit and JAR SHA-256;
3. set `NEQSIM_JVM_AUTOSTART=0` and add the source-built JAR to JPype;
4. assert that a main-only Java class was loaded from that JAR; and
5. retain the provenance output in the executed notebook.

For local clean validation, `NEQSIM_SOURCE_ROOT` and `NEQSIM_SOURCE_JAR` may point to the same checked-out commit and built artifact. They must not bypass the commit, hash, or class-location assertions.

Run the integrity checks before opening a pull request:

```bash
python -m unittest discover -s scripts -p 'test_check_notebook.py'
python scripts/check_notebook.py --all
python scripts/check_notebook.py path/to/new_notebook.ipynb \
  --require-main-source
```

When local Jupyter kernel sockets are unavailable, execute from a newly created validation environment with:

```bash
python scripts/execute_notebook_inprocess.py path/to/notebook.ipynb
```

The in-process runner writes the notebook only after every code cell succeeds. Publication still requires retained outputs, zero stored exceptions or stderr, rendered-HTML and MathJax review, inspection of every figure, and a truthful maintenance-ledger update.

The root `notebooks/notebook_maintenance_ledger.json` is an index. Active evidence is loaded from the JSON files matched by its `shards_glob`. Add a dedicated, descriptively named shard for a new notebook or focused pull request; do not rebuild unrelated shards. This keeps evidence changes reviewable and avoids concurrent pull-request conflicts.
