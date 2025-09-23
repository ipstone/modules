# Title:
   Mutation Frequency Comparison

# Purpose
   Compare gene-level mutation rates between cohorts (e.g. IMPACT vs TCGA) using filtered mutation tables.

# Workflow
1. Subset to the desired gene panel (e.g. IMPACT468):
   ```r
   library(dplyr)
   muts <- read.csv("muts.csv", stringsAsFactors = FALSE)
   panel <- read.delim("impact468_genes.txt", header = FALSE)$V1
   muts_panel <- filter(muts, Hugo_Symbol %in% panel)
   ```
2. Remove silent and splice-region events.
3. Create a unique `Sample_Gene` identifier to de-duplicate entries.
4. Export the gene list for `freq.R`/`fisher.R` input.
5. Update the sample count inside `freq.R` (e.g. `F = N / <#samples>`).
6. Run `freq.R` for each cohort to obtain frequency tables.
7. Supply both frequency outputs to `fisher.R` (or the combined `muts_freq.R`) to compute Fisher's exact tests.
   - Adjust input filenames, sample counts, and output names inside the scripts.
   - Keep default variable names unless refactoring the entire pipeline.

# Outputs
- Cohort-specific frequency tables.
- Fisher's exact test results (`result_fisher.out`).

# Notes
- Ensure both cohorts share the same gene list for fair comparison.
- Record intermediate files (panel list, frequency outputs) for reproducibility.
- The helper script `muts_freq.R` consolidates these steps if you prefer a single entry point.
