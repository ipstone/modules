# JRFLab Working Modules Merge Notes (2025-03)

## Overview
- synced ipstone master with `/home/peix/Workbench/toolsets/modules/modules_jrflab_working` to capture jrflab workflow updates.
- retained ipstone-specific targets (e.g. `mosdepth_wgs`, `indexcovTN`, CNVkit helpers) while integrating jrflab resource tweaks.
- confirmed lilac cluster compatibility paths (DMP reference, hotspot v3, Picard jar) and reinstated optional envs (e.g. `MIMSI_ENV`).

## Key Makefile Changes
- `Makefile`:39-725 – merged jrflab workflows, re-added ipstone workflows/tests (`copynumber_summary`, `run_cnvkit`, `svabaTN`, CNVkit test targets, `config`, `samples`).
- `fastq_tools/extractunmappedpairs.mk`:1-28 – new jrflab fastq extraction target, superseding legacy recipe.
- `wgs_metrics.mk`:1-121 plus `scripts/wgs_metrics.R` – added Picard/GATK-based WGS QC workflow (uses `/data/riazlab/lib/java/picard.jar`).

## Pipeline Modules Updated
- Align/BAM: `aligners/align.mk` (reduce merge mem), `aligners/bwamemAligner.mk`, `aligners/starAligner.mk`, `bam_tools/merge_bam.mk`, `bam_tools/processBam.mk`.
- Variant calling: `variant_callers/gatk.mk`, `somatic/mutect.mk`, `somatic/platypus.mk`, `somatic/somaticIndels.mk`, `somatic/strelka.mk`, `somatic/varscanTN.mk` (raised walltimes/memory to jrflab defaults).
- Copy number: `copy_number/ascat.R` (jrflab plotting overhaul, requires `BSgenome.Hsapiens.UCSC.hg19` in `ASCAT_ENV`), `copy_number/facets.mk` (higher resources & new summaries).
- Structural variants: `sv_callers/gridss_tumor_normal.mk` (points to `/data/riazlab/lib/reference/b37_dmp/b37.fasta`), `sv_callers/svaba_tumor_normal.mk` (16 cores, 144h wall), `sv_callers/manta.mk` (doc tweak).
- SV annotations: `vcf_tools/merge_sv.mk`, `vcf_tools/annotate_sv.mk` drop svaba from merge/annotate defaults; `scripts/filter_sv.R` expects GRIDSS & MANTA sample columns.
- VCF annotation: `vcf_tools/annotateSomaticVcf.mk` lowered RAM to 6–7G for bcftools/merge, `vcf_tools/cravat_annotation.mk` fixes `--sample_name $1`.
- Summaries: `summary/mutation_summary_excel.py` uses pandas defaults without `low_memory` to prevent dtype warnings; `summary/delmh_summary.mk`+`.R` now consume `summary/tsv/mutation_summary.tsv` and compute microhomology metrics via BSgenome.

## Configuration & References
- `config.inc`:17-45 locked python env defaults (use exported env vars to override); reinstated optional `MIMSI_ENV`.
- `genome_inc/b37.inc`:43-105 defaults to DMP FASTA/hotspot v3; PDX comment clarifies combined reference usage.
- Added `external/SNVBox/snv_box.conf`; adjust host/credentials if SNV-Box service differs.

## Compatibility Considerations
- Confirm `ASCAT_ENV` contains BSgenome.Hsapiens.UCSC.hg19.
- Picard jar path `/data/riazlab/lib/java/picard.jar` must exist on cluster nodes (verified).
- Reduce risk of resource contention by matching jrflab memory/timeouts (lowered BWA/STAR merge RAM, expanded GATK/Strelka walltimes).
- `config.inc` now uses `=` (not `?=`) for legacy envs; override by exporting before running make.

## Suggested Validation
1. Activate runtime environment (`enable.conda` or system python) before running `./modules/scripts/configure.py`.
2. Rebuild summaries: `make mutation_summary && make delmh_summary` to populate new `summary/tsv` outputs.
3. Test structural variant merge/annotation without svaba; re-enable by adding it back to `SV_CALLERS` if needed.
4. Execute `make wgs_metrics` on sample data to confirm Picard-based QC outputs.
5. Update SNVBox config if you rely on a different database endpoint.

