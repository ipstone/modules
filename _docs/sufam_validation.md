# Title:
   Sufam Validation Workflow

# Goal
   Recompute read-level support for somatic variants using Sufam and merge the
   results back into project mutation tables for downstream analyses.

# Prerequisites
   - `make mutation_summary` has been run (`summary/tsv/all.tsv` is required).
   - `SUFAM_ENV` (see `config.inc`) points to an environment with the `sufam`
     binary and dependencies installed.
   - `SAMPLE_SETS` defined if you plan to run multi-sample validations (populate
     `sample_sets.txt` and rerun `make config`).

# Running
1. **Per-sample validation:**
   ```bash
   make sufam_gt USE_CLUSTER=false
   ```
   Generates `sufam/<sample>.vcf`, `sufam/<sample>.txt`, per-sample MAFs, and the
   aggregated `sufam/mutation_summary_ft.maf` filtered table.
2. **Sample-set validation:**
   ```bash
   make sufam USE_CLUSTER=false
   ```
   Merges VCFs across each sample set, runs Sufam jointly, annotates the result,
   and writes `tsv/<set>.sufam.tsv` plus `tsv/sufam_variants.tsv`.
3. **Interactive reporting (optional):**
   ```bash
   make recurrent_mutations_sufam USE_CLUSTER=false
   ```
   Builds `recurrent_mutations/sufam/sufam.ipynb` and an HTML summary with plots
   of Sufam metrics across the cohort.

# Key Outputs
```
sufam/<sample>.vcf
sufam/<sample>.txt
sufam/<sample>.maf
sufam/<sample>_ann.maf
sufam/mutation_summary.maf
sufam/mutation_summary_ft.maf
vcf_ann/<set>.sufam.vcf.gz
tsv/<set>.sufam.tsv
tsv/sufam_variants.tsv
recurrent_mutations/sufam/sufam.html
```

# Notes
- The `sufam_gt` recipes call `scripts/sufam_gt.R` to merge counts and annotate
  with panel membership.  Edit that script if you need project-specific filters.
- `SUFAM_OPTS` (in the makefiles) controls mpileup parameters.  Override on the
  command line (e.g. `make sufam SUFAM_OPTS="--format vcf ..."`) for special
  assays.
- Outputs are suitable for feeding into ABSOLUTE, PyClone, or manual mutation
  review.  Keep both the `.txt` (raw counts) and `.maf` (annotated) files until
  QC is complete.
