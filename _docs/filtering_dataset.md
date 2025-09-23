# Title:
   Filtering and Finalising Mutation Tables

# Objective
   Outline the post-`mutation_summary` review steps used to curate the final mutation call set prior to downstream analyses or reporting.

# Download / Collect
1. Create a local results folder for the project.
2. Retrieve key outputs from the cluster:
   - `summary/tsv/all.tsv`
   - `summary/hs_metrics.summary.xlsx`
   - `facets/plots/*cncf.pdf`
   - `facets/cncf/*.txt`

# Variant Filtering Workflow
1. Open `all.tsv` (or work in R for large cohorts).
2. Remove non-coding events:
   - Exclude rows where `Variant_Classification` contains 3' UTR, 5' UTR, intron, IGR, RNA, etc.  In R:
     ```r
     library(dplyr)
     library(stringr)
     all <- read.table("all.tsv", header = TRUE, sep = "\t", stringsAsFactors = FALSE)
     all <- all %>% filter(!str_detect(Variant_Classification, "Intron|3'UTR|5'UTR|IGR|RNA"))
     ```
3. Enforce caller support rules:
   - Keep varscan+strelka calls.
   - Retain platypus calls only when supported by scalpel *or* lancet.
4. Cull in-frame indels:
   - Remove rows flagged as `In_Frame_Del`/`In_Frame_Ins`.
   - Further exclude indels where `|REF| - |ALT| < 3` bp and not supported by the desired callers.
5. AF thresholding – discard variants with `AF > 0.05` in the matched normal.
6. Save the curated table as `muts.csv` (comma-delimited) for downstream scripts.

# Notes
- For interactive checking, Excel works well; save back to CSV once filters are complete.
- Keep a copy of the raw `all.tsv` for audit purposes.
- The filtered `muts.csv` feeds ABSOLUTE, deconstructSigs, and other downstream tools described in related docs.
