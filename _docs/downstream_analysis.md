# Title:
   Downstream Analytics and Signatures

# Copy-number Summary
1. `make copynumber_summary`
   - Produces genome-level summaries and HRD metrics under `summary/genome_stats/`.
2. Inspect `summary/genome_stats/genome_summary.tsv` to verify expected copy-number signatures (e.g. LST, NTAI, Myriad HRD).

# Mutational Signatures (deconstructSigs)
1. Create a local `deconstructsig/` directory.
2. Copy the curated `muts.csv` into that directory.
3. Run `deconstructsig.R` line by line to generate `signatures.csv`.
   - Ensure the mutation catalogue matches the reference build (chr prefixes, context availability).

# Troubleshooting Tips
- Check the for-loop boundaries in `deconstructsig.R` to ensure all samples are processed.
- Validate that MAF/VCF files contain the required columns (`Tumor_Sample_Barcode`, `Chromosome`, `Start_position`, etc.).
- Confirm reference FASTA paths inside the script when mutational contexts fail to load.

# Related Documentation
- `_docs/filtering_dataset.md` – preparing `muts.csv` prior to signatures.
- `_docs/mutation_frequency_summary.md` – comparing mutation frequencies across cohorts.
- `_docs/sufam_validation.md` – validation workflow feeding into multi-component analyses.
