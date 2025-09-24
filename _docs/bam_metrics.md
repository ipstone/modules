# Name:
    bam_metrics

# Description
    Runs the Picard-based QC suite defined in `qc/bam_metrics.mk`.  The target
    aggregates alignment, insert-size, oxoG, hybrid-selection, and GC bias
    metrics for every entry in `$(SAMPLES)` and summarises them with
    `scripts/qc/bam_metrics.R`.

# Input
    - `bam/<sample>.bam` (and matching BAM indices).
    - Optional: override `TARGETS_LIST` in `project_config.inc` to point Picard
      HybridSelection metrics at the correct bait/target interval list.

# Output
```
metrics/<sample>.idx_stats.txt
metrics/<sample>.aln_metrics.txt
metrics/<sample>.insert_metrics.txt and .pdf
metrics/<sample>.oxog_metrics.txt
metrics/<sample>.hs_metrics.txt
metrics/<sample>.gc_metrics.txt and gc_bias.txt
summary/idx_metrics.txt
summary/aln_metrics.txt
summary/insert_metrics.txt
summary/oxog_metrics.txt
summary/hs_metrics.txt
summary/gc_metrics.txt
summary/gc_summary.txt
version/bam_metrics.txt   # recorded Picard + R versions
```

# Usage
```
make bam_metrics USE_CLUSTER=false
```
    Set `USE_CLUSTER=true` (default) to fan jobs out through qmake.

# Notes
- Picard binaries are resolved via `$(PICARD)` from `config.inc`; ensure the jar
  exists on the execution host.
- Each summary file is produced by `scripts/qc/bam_metrics.R --option <n>` and
  concatenates sample-level metrics into a single TSV for review.
- The GC bias recipe emits both `*.gc_metrics.txt` (per-sample values) and a
  project-wide `summary/gc_summary.txt` table.
