# Repository Guidelines

## Project Structure & Module Organization
Core workflows live in the top-level `Makefile` and `Makefile.inc`, which dispatch into domain-specific directories such as `aligners/`, `variant_callers/`, `copy_number/`, `clonality/`, and `summary/`. Shared helper code is under `scripts/`, while reference bundles, default YAML templates, and genome metadata sit in `reference/`, `default_yaml/`, and `genome_inc/`. Configuration overrides belong in `config.inc` (global) or `project_config.inc` (project-specific). Example runbooks and schema docs live in `_docs/`, and conda environment specifications are tracked in `conda_env/`.

## Build, Test, and Development Commands
Initialize a new analysis area with `./init_project`, then tailor `config.inc` before launching jobs. The canonical entry points are `make somatic_indels`, `make somatic_variants`, or other targets listed in the `Makefile`; append `USE_CLUSTER=false NUM_JOBS=4` to exercise them locally. Use `make -n <target>` for a dry run that validates dependencies without submitting to the scheduler. Many subflows can be executed directly, for example `make -f modules/copy_number/genomealtered.mk` when debugging copy-number summaries.

## Coding Style & Naming Conventions
Match the existing language idioms: Makefiles require hard tabs for recipes; Python utilities are Python 2 compatible (see `vcf_tools/merge_vcf.py`) and prefer snake_case with four-space indents; Perl and shell scripts mirror their current brace and spacing style. Keep shebangs intact and document non-obvious flags with a terse comment. When adding configuration keys, group related variables and sort alphabetically within their block.

## Testing Guidelines
There is no centralized unit-test harness; validation relies on replaying representative datasets. Reuse the sample YAMLs in `_docs/examples/` or craft synthetic inputs under `summary/test_data/` when available. Before merging, run the affected `make` targets with `USE_CLUSTER=false` to ensure rule graph integrity, then perform one scheduler-backed submission in a staging queue to confirm DRMAA settings. Capture relevant log excerpts from `log/<target>.<date>.log` for review.

## Commit & Pull Request Guidelines
Follow the prevailing imperative subject style (`Verb noun phrase`, e.g., `Document make config workflow`) and keep the first line under 72 characters. Reference ticket IDs when they exist, and note key targets touched in the body. Pull requests should summarize the change scope, enumerate expected pipeline targets, link any configuration diffs, and attach screenshots or sample outputs when altering reports. Always mention whether cluster or local smoke tests were run and include pointers to the resulting logs.

## Environment & Configuration Tips
Cluster interaction is mediated by `modules/scripts/qmake.pl`; prefer editing retry counts or Slack hooks via variables (`NUM_ATTEMPTS`, `SLACK_CHANNEL`) instead of code. Pin tool versions through the paths in `config.inc` or by updating the relevant `conda_env/*.txt` lockfiles, and document any new environment requirement alongside the change.
