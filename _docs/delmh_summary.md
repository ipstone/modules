# Name:
   delmh_summary

# Description
   Computes deletion microhomology statistics from the curated mutation summary
   so you can flag samples with elevated deletion-with-microhomology burdens.
   The make target is implemented in `summary/delmh_summary.mk` and delegates the
   heavy lifting to `summary/delmh_summary.R`.

# Inputs
   - `summary/tsv/mutation_summary.tsv` - produced by `make mutation_summary`.
   - Reference FASTA and BSgenome assets available to R (the script loads
     `BSgenome.Hsapiens.UCSC.hg19`).  Ensure the genome package is installed in
     the environment used by the rule.

# Outputs
```
summary/tsv/delmh_summary.tsv
version/delmh_summary.txt   # R version captured by the job wrapper
```
   The TSV reports per-sample counts, mean/median deletion lengths, and the
   fraction of deletions with ≥3 bp microhomology for events ≥4 bp long.

# Usage
```
make mutation_summary
make delmh_summary USE_CLUSTER=false
```
   The first command materialises the TSV inputs; the second runs the summary
   locally (omit `USE_CLUSTER=false` to submit via qmake).

# Common Issues
   - **Missing BSgenome library** - install
     `Bioconductor::BSgenome.Hsapiens.UCSC.hg19` in the runtime environment if
     the script aborts at `library("BSgenome.Hsapiens.UCSC.hg19")`.
   - **No deletions present** - samples without qualifying deletions still
     appear in the output with `NA` summary metrics; this is expected.
