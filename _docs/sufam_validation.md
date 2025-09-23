# Title:
   Sufam Validation Workflow

# Goal
   Validate somatic variants against matched BAMs on targeted regions shared by IMPACT and exome capture panels.

# Preparation
1. Create an intersected BED of common regions:
   - Use the IMPACT panel (`/share/reference/target_panels/*.bed`) and the exome BED (`/share/data/...`).
   - Run `bedtools intersect` to produce a BED covering shared targets.
2. Use the R helper `01_intersect_common_bbed_updated.R` to merge `summary/tsv/all.tsv` with the intersected BED and export candidate variants.
3. Apply the standard filtering workflow (see `_docs/filtering_dataset.md`) to produce tumor and normal `muts.csv` tables suitable for validation.

# Directory Structure
1. `mkdir sufam` and `cd` into the directory.
2. Create per-sample VCF files with header `#CHROM\tPOS\tREF\tALT` and populate with filtered variants.
3. Convert chromosome `23` entries to `X` where necessary.
4. Create a subdirectory per sample to hold outputs.

# Running Sufam
1. Activate the environment: `source ~/share/usr/anaconda-envs/sufam-dev/bin/activate ~/share/usr/anaconda-envs/sufam-dev`.
2. Execute Sufam for each tumor sample:
   ```bash
   sufam ~/share/reference/GATK_bundle/2.3/human_g1k_v37.fa SAMPLE.vcf /path/to/SAMPLE.bam \
         2> SAMPLE/sufam.log > SAMPLE/sufam.tsv
   ```
3. Repeat for each matched normal.

# Aggregation and Interpretation
1. Concatenate `*/sufam.tsv` outputs for tumors and normals separately (remove duplicate headers).
2. Create a mutation identifier (e.g. `paste(chrom, pos, tumor_id, sep="_")`) to merge with the curated mutation table.
3. Merge Sufam metrics (`cov`, `val_alt_count`, `val_maf`) into the mutation table using R `merge()`.
4. Append `.tumor` / `.normal` suffixes to distinguish columns after merging.
5. Define a `validation` column:
   - `not_tested` if `cov.tumor < 50`.
   - `not_validated` if both `val_alt_count < 3` and `val_maf < 0.05`.
   - Otherwise `validated`.
6. Save the combined table as `sufam_table.csv` for reporting.

# Notes
- Maintain separate TSVs for tumor vs normal Sufam outputs before merging.
- For low MAF variants, consider additional filters (e.g. alt count or depth thresholds) tailored to your assay.
- The validated Sufam table can feed multi-component analyses or be used as an alternate `muts.csv` for ABSOLUTE.
