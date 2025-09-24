# Name:
    mosdepth_wgs
    Tool: https://github.com/brentp/mosdepth

# Description
    Calculates fixed-window genome-wide depth profiles for each sample using
    mosdepth.  The make target lives in `copy_number/mosdepth_wgs.mk` and emits
    `.regions.bed.gz` files summarising coverage in 10 kb bins (configurable via
    `MOSDEPTH_WINDOW`).

# Inputs
    - `bam/<sample>.bam` and index files listed in `$(SAMPLES)`.
    - `mosdepth` binary on PATH.

# Outputs
```
mosdepth_wgs/<sample>.regions.bed.gz
mosdepth_wgs/<sample>.regions.bed.gz.csi
version/mosdepth_wgs.txt   # recorded tool version
```

# Usage
```
make mosdepth_wgs USE_CLUSTER=false          # run locally for quick checks
```
    To adjust the window size, override `MOSDEPTH_WINDOW` on the command line or
    in `project_config.inc` (default: 10000 bp).

# Notes
- mosdepth runs quickly on whole-genome BAMs (≈50 minutes for 50× coverage when
  executed with the default 4 threads).
- The makefile pre-creates `mosdepth_wgs/` to keep outputs in a single
  directory; remove stale `.regions.bed.gz` files if you rerun with a different
  window size.
- Combine these depth tracks with `indexcovTN` to triage copy-number anomalies
  before launching heavier CNV callers.
