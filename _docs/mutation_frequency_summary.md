# Title:
   Mutation Frequency Comparison

# Purpose
   Compare gene-level mutation rates between cohorts (e.g. IMPACT vs TCGA) using
   the TSVs produced by `make mutation_summary`.

# Inputs
   - `summary/tsv/mutation_summary.tsv` (project cohort).
   - A second cohort exported in the same format (or at minimum the columns
     `TUMOR_SAMPLE`, `ANN[*].GENE`, `Variant_Classification`).
   - Optional: gene panel list to restrict the comparison (e.g. IMPACT468).

# Workflow (R example)
```r
library(dplyr)
library(readr)
library(tidyr)

impact_panel <- read_tsv("impact468_genes.txt", col_names = FALSE)$X1
project <- read_tsv("summary/tsv/mutation_summary.tsv")
external <- read_tsv("other_cohort.tsv")

clean <- function(df, panel) {
  df %>%
    filter(ANN[*].GENE %in% panel) %>%
    filter(!Variant_Classification %in% c("Silent", "Intron", "RNA", "3'UTR", "5'UTR", "IGR")) %>%
    distinct(TUMOR_SAMPLE, ANN[*].GENE)
}

project_freq <- clean(project, impact_panel) %>%
  count(ANN[*].GENE, name = "project_hits") %>%
  mutate(project_freq = project_hits / n_distinct(project$TUMOR_SAMPLE))

external_freq <- clean(external, impact_panel) %>%
  count(ANN[*].GENE, name = "external_hits") %>%
  mutate(external_freq = external_hits / n_distinct(external$TUMOR_SAMPLE))

freq_table <- full_join(project_freq, external_freq, by = "ANN[*].GENE") %>%
  replace_na(list(project_hits = 0, external_hits = 0, project_freq = 0, external_freq = 0))

# Fisher's exact test per gene
fisher_tests <- freq_table %>%
  rowwise() %>%
  mutate(p_value = fisher.test(matrix(c(project_hits,
                                        n_distinct(project$TUMOR_SAMPLE) - project_hits,
                                        external_hits,
                                        n_distinct(external$TUMOR_SAMPLE) - external_hits),
                                      nrow = 2))$p.value) %>%
  ungroup()

write_tsv(fisher_tests, "mutation_frequency_comparison.tsv")
```

# Notes
- Keep cohorts on the same reference build and gene symbol set before joining.
- Adjust the filtering step to match your validation criteria (e.g. require two
  callers, drop known artifacts, etc.).
- Apply multiple-testing correction (e.g. `p.adjust(p_value, method = "BH")`) if
  the comparison will be used for reporting.
