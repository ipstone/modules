# Title:
   ABSOLUTE Workflow

# Prerequisites
- Curated mutation table (`muts.csv`) produced from `_docs/filtering_dataset.md` steps with ≥1 mutation per sample.
- Facets copy-number output (`facets/cncf/*.txt`).
- Access to an R host with ABSOLUTE dependencies (e.g. `swan`).

# Directory Setup
1. `mkdir absolute`
2. Copy `muts.csv` into `absolute/`.
3. Copy all `facets/cncf/*.cncf.txt` files into `absolute/`.

# Input Generation
1. SSH to an R-friendly node: `ssh swan`.
2. Run `Rscript Make_ABS_muts_Input.R` inside `absolute/`.
   - If errors occur, run line-by-line; a common issue is the tumor column labelled `SAMPLE.TUMOR` instead of `TUMOR_SAMPLE`.
3. Execute `Rscript Make_SegFromFacets.R` to generate segmentation input.

# Parameter Tuning (Highly Segmented Facets)
1. Increase the FACETS critical values in `project_config.yaml` by 50–100.
2. Re-run `make config`.
3. Clean previous FACETS artefacts: remove sample-specific files in `facets/` (plots, `geneCN.txt`, and entries under `facets/cncf/`).
4. Re-run `make facets` and inspect plots.
5. Repeat adjustments until copy-number profiles look reasonable.
6. Restart ABSOLUTE prep from `Make_ABS_muts_Input.R` after each FACETS iteration.

# Running ABSOLUTE
1. Confirm paths referenced inside `runabc.qsh` and `RunAbsolute1.R` are correct.
2. Submit `runabc.qsh` (e.g. `sh runabc.qsh`).
3. After completion, download the `plot.pdf` files and `*.tab.txt` results for review.
4. Choose a solution for each sample, add a leading `solution` column to the relevant `tab.txt`, and upload back to the cluster (same filename/location).
5. Run `Rscript RunAbsolute2.R`.
6. Merge mutations with ABSOLUTE output using `Rscript Combine_muts_cncf.R` (set `MAF.directory`, `results.directory`, and output filename).  The merged product can be named `<project>_absolute.csv`.

# Quality Checks
- Validate deletions/amplifications in geneCN results by manual inspection.
- Ensure every sample retains ≥1 mutation; if not, add a dummy mutation before running ABSOLUTE.
- Version-control your edited ABSOLUTE scripts (`runabc.qsh`, `RunAbsolute*.R`) alongside project metadata.
