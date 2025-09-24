# Title:
   Downstream Analytics and Signatures

## Copy-number Summary
1. After `make facets` completes, run `make copynumber_summary`.
2. The target invokes genome altered fraction, LST, NTAI, and Myriad HRD
   recipes (`modules/copy_number/*.mk`) and collates them with
   `summary/genomesummary.mk`.
3. Review results in `genome_summary/`:
   - `genome_summary/genome_altered/<pair>.txt`
   - `genome_summary/lst/<pair>.txt`
   - `genome_summary/ntai/<pair>.txt`
   - `genome_summary/myriad_score/<pair>.txt`
   - `genome_summary/summary.txt` (per-sample aggregate table)

## Mutational Signatures (deconstructSigs)
1. Ensure `make mutation_summary` has generated `summary/tsv/mutation_summary.tsv`.
2. Run `make deconstruct_sigs` (requires `DECONSTRUCTSIGS_ENV` with the
   `deconstructSigs` R package).
3. Outputs are written to `deconstructsigs/`:
   - `deconstructsigs/signatures/<tumor>.RData`
   - `deconstructsigs/plots/context/<tumor>.pdf`

## Troubleshooting Tips
- Signature extraction depends on Mutect calls; confirm the sample appears in
  `summary/tsv/mutation_summary.tsv` with `variantCaller == "mutect"`.
- Copy-number summaries expect FACETS outputs named `<tumor>_<normal>`.
- If an R package is missing, activate the environment referenced by
  `DECONSTRUCTSIGS_ENV` or `FACETS_SUITE_ENV` before re-running the target.

## Related Documentation
- `_docs/filtering_dataset.md` - preparing `muts.csv` prior to manual review.
- `_docs/sufam_validation.md` - validation workflow that augments mutation
  tables with Sufam evidence.
