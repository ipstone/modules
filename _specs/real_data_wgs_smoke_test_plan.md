# Real-data WGS Smoke Test Plan for `ipstone_modules`

## Purpose
This document describes how to perform a **real-data smoke test** of the merged
WGS-focused `ipstone_modules` pipeline on the lilac cluster.

The goal is **not** to complete a full production analysis. The goal is to
confirm that the current merged modules:

- configure correctly in a real project
- submit and run correctly on the cluster
- produce expected outputs on real BAM / FASTQ inputs
- honor the intended WGS defaults and resource settings
- do not fail because of broken Makefile wiring, stale target names,
  environment mismatches, or missing intermediate assumptions

This plan is intended for future reuse after major pipeline merges or changes.

---

## When to use this plan
Run this smoke test when:

- a major merge was performed across working WGS module repos
- cluster resource defaults were changed
- BAM-processing rules were changed
- SV caller behavior was changed
- WGS QC / duplicate-metrics behavior was changed
- the repo will be used as the new default cloneable working copy on lilac

---

## Scope
### Primary validation targets
These targets exercise the most important merged WGS changes:

1. `wgs_metrics`
2. `svaba_tumor_normal`
3. `gridss_tumor_normal`
4. `copynumber_summary`
5. `hotspot_summary` (optional but useful)

### Secondary / optional validation targets
Use these if you also want to test alignment and BAM processing:

6. `bwamem`
7. `bam_interval_metrics`
8. `mutation_summary`

### Out of scope for the initial smoke test
Do **not** start with the following unless specifically needed:

- full cohort runs
- all samples in a project
- long retrospective reruns of older projects
- all optional/test/beta targets

---

## Recommended smoke-test strategy
Use a **two-stage** approach.

### Stage A: BAM-first smoke test
Preferred first pass.

Use a project that already has:

- `bam/<sample>.bam`
- `bam/<sample>.bam.bai` or `bam/<sample>.bai`
- valid `samples.yaml` / pairing information

This is the fastest and safest way to validate:

- WGS QC
- duplicate-metrics reuse
- SV calling
- summary wiring
- cluster submission behavior

### Stage B: alignment-inclusive smoke test
Run only after Stage A passes.

Use one small / representative sample or tumor-normal pair with FASTQs to test:

- `bwamem`
- `aligners/align.mk`
- `aligners/bwamemAligner.mk`
- `bam_tools/processBam.mk`
- `scripts/job.py` / `scripts/run.py`

This validates the new BAM robustness logic:

- temp-file writes
- `samtools quickcheck`
- sort behavior
- failed-output cleanup

---

## Choosing a test project
Pick a project with these characteristics:

### Preferred project properties
- WGS tumor-normal project already used successfully on lilac
- 1 matched pair with known good BAMs
- representative genome size / depth
- minimal special-case biology
- not currently being modified by another active analysis

### Ideal test pair properties
- one tumor sample and one matched normal
- BAMs already indexed
- sample naming is clean and already works with current config flow
- enough depth to exercise WGS logic, but not the largest/most pathological sample first

### Avoid for first pass
- highly fragmented projects
- partially configured projects
- mixed exome/WGS projects
- projects with uncertain sample pairing
- projects missing BAM indexes
- projects under active production deadlines unless agreed in advance

---

## Pre-flight checklist
Before running anything:

1. **Create / use a dedicated test project copy**
   - Prefer a copy or clearly designated smoke-test area.
   - Avoid modifying the only active production project directory.

2. **Record the repo version**
   ```bash
   cd /path/to/ipstone_modules
   git log --oneline -5
   git status
   ```
   Confirm the repo is clean and note the commit hash used for testing.

3. **Confirm cluster resources / env paths exist**
   Check at minimum:
   - `GRIDSS_ENV`
   - `SVABA_ENV`
   - Picard jar used by `wgs_metrics.mk`
   - reference FASTA used by the project
   - blacklist / dbSNP inputs for SV callers

4. **Confirm project configuration files exist**
   - `samples.yaml`
   - `sample_attr.yaml` (if used)
   - `project_config.yaml`
   - `project_config.inc` or ability to regenerate it with `make config`

5. **Run config regeneration**
   ```bash
   make config
   ```
   Verify `project_config.inc` regenerates successfully.

6. **Confirm sample pairing**
   Check that the intended tumor-normal pair appears correctly in:
   - `SAMPLE_PAIRS`
   - `tumor.<pair>`
   - `normal.<pair>`

7. **Check BAM existence and indexes**
   For BAM-first validation:
   ```bash
   ls bam/<tumor>.bam bam/<normal>.bam
   ls bam/<tumor>.bam.bai bam/<normal>.bam.bai 2>/dev/null || ls bam/<tumor>.bai bam/<normal>.bai
   ```

8. **Check available disk / tmp space**
   Especially for:
   - `TMPDIR`
   - project output volume
   - `svaba/`
   - `gridss/`
   - `metrics/`

9. **Choose queue policy before starting**
   Decide whether to:
   - run locally with `USE_CLUSTER=false` for very small tests, or
   - run on cluster queues for realistic WGS validation

For actual WGS smoke tests on real data, **cluster-backed execution is preferred**.

---

## Pre-run dry-run checks
Before submitting real jobs, run dry-runs in the project directory.

### Required dry-run commands
```bash
make -n wgs_metrics
make -n svaba_tumor_normal
make -n gridss_tumor_normal
make -n copynumber_summary
```

### Optional dry-runs
```bash
make -n hotspot_summary
make -n bwamem
```

### What to look for
- no missing module Makefile paths
- no unexpected legacy target names
- correct sample names in output paths
- expected queue/resource flags in job submission commands
- expected BAM inputs / dependency chains

If dry-run fails with only missing project outputs (for example, because BAMs are
not yet present), that is acceptable only if you understand why.

If dry-run fails due to missing module files, bad paths, or broken Makefile
wiring, fix that before live testing.

---

## Stage A: BAM-first live smoke test

## A1. Minimal recommended live test set
Run on **one matched pair** and **one or two samples only**.

### Test 1: WGS QC
```bash
make wgs_metrics
```

### Test 2: SvABA SV calling
```bash
make svaba_tumor_normal
```

### Test 3: GRIDSS SV calling
```bash
make gridss_tumor_normal
```

### Test 4: Copy-number summary
```bash
make copynumber_summary
```

### Test 5: Hotspot summary (optional)
```bash
make hotspot_summary
```

---

## A2. What each test is validating

### `make wgs_metrics`
Validates:
- root-level `wgs_metrics.mk`
- Picard invocation
- summary generation via `scripts/wgs_metrics.R`
- duplicate metrics default behavior
- reuse of `metrics/<sample>.dup_metrics.txt` when present

#### Success criteria
- per-sample files appear under `metrics/`
- summary files appear under `summary/`
- `summary/duplicate_metrics.txt` is generated by default
- if `metrics/<sample>.dup_metrics.txt` already exists, it is reused rather than recomputed

#### Check explicitly
```bash
ls metrics/*.duplicate_metrics.txt
ls summary/duplicate_metrics.txt summary/wgs_metrics.txt
```

### `make svaba_tumor_normal`
Validates:
- active top-level target wiring
- queue support / resource variables
- SvABA environment and references
- production of `vcf/<pair>.svaba_sv.vcf`

#### Success criteria
```bash
ls svaba/<tumor>_<normal>.svaba.somatic.sv.vcf
ls vcf/<tumor>_<normal>.svaba_sv.vcf
```

### `make gridss_tumor_normal`
Validates:
- queue-aware GRIDSS submission
- filter-stage env throttling
- cleanup path correctness
- production of `vcf/<pair>.gridss_sv.vcf`

#### Success criteria
```bash
ls gridss/<tumor>_<normal>/<tumor>_<normal>.gridss_sv.vcf
ls vcf/<tumor>_<normal>.gridss_sv.vcf
```

### `make copynumber_summary`
Validates:
- top-level target wiring after stale path cleanup
- dependency path through existing copy-number modules
- `summary/genomesummary.mk`

#### Success criteria
Expected copy-number / genome-summary outputs are generated without missing-module errors.

### `make hotspot_summary`
Validates:
- repaired top-level wiring to `variant_callers/hotspot.mk`
- summary generation path

---

## Stage B: alignment-inclusive live smoke test
Run this only after Stage A passes.

### B1. Test one representative sample
If FASTQs are available and you want to validate the alignment merge:

```bash
make bwamem
```

If you want an even smaller test, use a small sample or a subsampled/split input
that still reflects normal project structure.

### B2. What this validates
- `aligners/align.mk`
- `aligners/bwamemAligner.mk`
- `bam_tools/processBam.mk`
- `samtools sort` path
- temp-file creation and move semantics
- BAM indexing with `samtools quickcheck`
- `scripts/job.py` integrity checks
- `scripts/run.py` cleanup behavior

### B3. Success criteria
- final BAM appears under `bam/`
- BAM index exists
- no partial BAM is left behind after failure
- no stale temp files are treated as successful outputs

#### Check explicitly
```bash
ls bam/<sample>.bam
ls bam/<sample>.bam.bai 2>/dev/null || ls bam/<sample>.bai
```

---

## Logging and evidence capture
For every smoke test run, record:

1. repo commit hash
2. project path
3. tested sample(s) / pair(s)
4. commands run
5. queue used
6. relevant log files
7. summary of pass/fail observations

### Suggested capture commands
```bash
git -C /path/to/ipstone_modules log --oneline -3
make -n wgs_metrics > smoke_dryrun_wgs_metrics.txt 2>&1
make -n svaba_tumor_normal > smoke_dryrun_svaba.txt 2>&1
make -n gridss_tumor_normal > smoke_dryrun_gridss.txt 2>&1
```

For live runs, save:
- stdout/stderr capture if launching manually
- qmake / cluster job ids
- `log/<target>.*`

---

## Failure handling / stop conditions
Stop the smoke test and fix issues before continuing if any of the following occur:

- missing module Makefile path
- incorrect top-level target name
- cluster submission arguments malformed
- BAM integrity failures from `samtools quickcheck`
- duplicate metrics not produced when expected
- VCF target generated in an unexpected location
- environment path not found
- references do not match project genome build

Do **not** continue to later stages if Stage A already reveals wiring/config bugs.

---

## Quick triage guide

### Failure: `No rule to make target ... .mk`
Likely cause:
- stale top-level `Makefile` target wiring

Action:
- inspect the target definition in `Makefile`
- compare with current module layout

### Failure: BAM exists but downstream caller says corrupt BAM
Likely cause:
- incomplete BAM write or index issue

Action:
```bash
samtools quickcheck -v bam/<sample>.bam
samtools index bam/<sample>.bam
```
Review alignment / processBam logs.

### Failure: duplicate metrics missing
Likely cause:
- `ENABLE_DUPLICATE_METRICS=false`
- no prior `metrics/<sample>.dup_metrics.txt` and fallback failed

Action:
- check `wgs_metrics.mk`
- verify whether alignment-stage dup metrics exist
- inspect `metrics/<sample>.duplicate_metrics.txt` rule execution

### Failure: GRIDSS or SvABA queue/resource issues
Likely cause:
- queue mismatch or env mismatch

Action:
- override queue explicitly, e.g.
  ```bash
  make svaba_tumor_normal SVABA_QUEUE=cpuqueue
  make gridss_tumor_normal GRIDSS_QUEUE=cpuqueue
  ```

---

## Recommended final sign-off criteria
Consider the merged repo smoke-tested successfully if:

1. `make config` works in a real project
2. `make -n` works for the primary WGS smoke-test targets
3. `make wgs_metrics` succeeds on real BAM(s)
4. duplicate metrics are produced by default and reuse prior dup-metrics files when available
5. `make svaba_tumor_normal` succeeds on one real pair
6. `make gridss_tumor_normal` succeeds on one real pair
7. `make copynumber_summary` succeeds without stale-target errors
8. optional alignment test (`make bwamem`) succeeds on one representative sample, if alignment changes were part of the merge being validated

---

## Recommended command sequence (practical default)
For a future real-data smoke test, this is the recommended order:

```bash
make config
make -n wgs_metrics
make -n svaba_tumor_normal
make -n gridss_tumor_normal
make -n copynumber_summary

make wgs_metrics
make svaba_tumor_normal
make gridss_tumor_normal
make copynumber_summary
```

Optional after that:

```bash
make hotspot_summary
make bwamem
```

---

## Related references
- `_docs/pipeline_run_checklist.md`
- `_docs/wgs_metrics.md`
- `_docs/svaba_tumor_normal.md`
- `_docs/logs/2026-04-23_wgs_modules_merge.md`

---

## Notes for future updates
If this smoke-test plan is reused after another merge, update at least:

- the active primary targets
- any queue defaults
- any duplicate-metrics behavior
- any changed top-level aliases in `Makefile`
- the related references section
