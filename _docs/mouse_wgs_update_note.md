# Title:
   Mouse WGS Variant Calling Updates (February 2025)

# Summary
   The `mouse_wgs` branch includes three coordinated changes that stabilise the
   somatic indel workflow and modernise our Strelka integration:

   1. `variant_callers/somatic/strelka.mk` now drives Strelka2 via the
      `configureStrelkaSomaticWorkflow.py` entry point in a dedicated
      `STRELKA_ENV`.  The rule invokes the bundled Python interpreter, runs the
      generated `runWorkflow.py`, increases memory limits, and consumes the
      gzipped results under `results/variants/*.vcf.gz` before annotating them.
   2. `variant_callers/somatic/somaticIndels.mk` strips out semicolon-prefixed
      lines from generated `.uvcf` files so downstream merges no longer propagate
      malformed comment rows.
   3. `vcf_tools/merge_uvcf_vcf.py` hardens the UPS coordinate join logic by
      reading the UPS table with explicit column names, ignoring blank/comment
      rows, recording skipped entries, and ensuring Python 2/3 compatible output.

# Impact
   Together these updates eliminate stray `;...` lines that previously broke UPS
   annotations, let Strelka runs operate entirely from a managed Conda environment,
   and make the merge utility resilient to missing UPS coordinate values.
