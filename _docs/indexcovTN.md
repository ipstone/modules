# Name: indexcovTN
    Tool: https://github.com/brentp/goleft/tree/master/indexcov

# Description
    Runs `goleft indexcov` on each tumor/normal pair to estimate coverage trends
    directly from BAM indices.  Implemented in `copy_number/indexcovTN.mk` and
    typically completes in seconds.

# Inputs
    - `bam/<tumor>.bam`, `bam/<normal>.bam` (plus their `.bai` indices).
    - `SAMPLE_PAIRS` populated via `make config`.
    - `goleft` available on the PATH used by the make recipe.

# Outputs
```
indexcovTN/<tumor>/index.html
indexcovTN/<tumor>/indexcov/*.bed.gz     # per-chromosome coverage summaries
indexcovTN/<tumor>/indexcov/*.json       # QC metadata
```
    Files are organised by tumor sample name; normals are only used as controls
    during the run.

# Usage
```
make indexcovTN USE_CLUSTER=false
```
    Omit `USE_CLUSTER=false` to submit through qmake.  The rule internally
    creates the `indexcovTN/<tumor>` directory if it does not yet exist.

# Notes
- The default command processes the tumor BAM first and supplies the matched
  normal as an additional BAM argument to `goleft indexcov`.
- Review the generated `index.html` plots for coverage spikes or dropout before
  proceeding to SV or copy-number workflows.
- `SVABA_BLACKLISTED` is not used here; keep high-coverage blacklist files for
  SV callers separate from indexcov runs.
