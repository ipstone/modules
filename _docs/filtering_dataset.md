# Title:
   Filtering and Finalising Mutation Tables

# Objective
   Outline the post-`mutation_summary` review steps used to curate the final
   mutation call set prior to downstream analyses or reporting.

# Prepare the Inputs
1. Run `make mutation_summary` so that `summary/mutation_summary.xlsx` and the
   companion TSVs under `summary/tsv/` exist.
2. Create a local results folder for the project and pull down the following
   artefacts:
   - `summary/tsv/all.tsv`
   - `summary/mutation_summary.xlsx`
   - `facets/plots/*cncf.pdf`
   - `facets/cncf/*.txt`

# Variant Filtering Workflow
1. Open `summary/tsv/all.tsv` in your analysis tool of choice (R is preferred for
   large cohorts).
2. Remove non-coding events:
   ```r
   library(dplyr)
   library(stringr)
   all <- read.table("all.tsv", header = TRUE, sep = "\t", stringsAsFactors = FALSE)
   all <- all %>% filter(!str_detect(Variant_Classification, "Intron|3'UTR|5'UTR|IGR|RNA"))
   ```
3. Enforce caller support rules:
   - Keep calls supported by both VarScan and Strelka.
   - Retain Platypus calls only when supported by Scalpel or Lancet.
4. Cull in-frame indels:
   - Remove rows flagged as `In_Frame_Del`/`In_Frame_Ins`.
   - Further exclude indels where `|REF| - |ALT| < 3` bp unless supported by the
     desired callers.
5. Apply germline/normal filters - discard variants with `AF > 0.05` in the
   matched normal (`NORMAL_MAF` column).
6. Save the curated table as `muts.csv` (comma-delimited) for downstream tools
   such as ABSOLUTE, deconstructSigs, and Sufam.

# Notes
- Keep a pristine copy of `all.tsv` for auditability.
- `summary/tsv/mutation_summary.tsv` mirrors the Excel “Mutation Summary” sheet
  and is often more convenient for scripting than the full `all.tsv` export.
- Record any manual inclusion/exclusion decisions so they can be folded back
  into project notebooks or QC reports.
