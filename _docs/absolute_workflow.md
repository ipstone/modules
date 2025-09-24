# Title:
   ABSOLUTE Workflow

# Overview
   ABSOLUTE is orchestrated by `modules/clonality/absoluteSeq.mk`.  Run the
   bundled make target after somatic calls and copy-number profiling complete to
   generate ABSOLUTE results, review objects, and integrated mutation tables.

# Prerequisites
   - `make config` has been run so `SAMPLE_PAIRS`, `tumor.<pair>`, and
     `normal.<pair>` are defined.
   - Somatic tables exist (`tables/<pair>.mutect.tab.txt` and
     `tables/<pair>.strelka_varscan_indels.tab.txt`) from `make somatic_variants`.
   - Copy-number segments are available.  The default configuration uses
     `facets/cncf/<pair>.cncf.txt`.  Override `USE_TITAN_COPYNUM` or
     `USE_ONCOSCAN_COPYNUM` in `project_config.yaml` if your study relies on
     alternate callers and re-run `make config`.
   - An R environment with the `ABSOLUTE`, `dplyr`, `stringr`, and `readr`
     packages is reachable by the cluster worker (activate or source it before
     launching the target).

# Running
   ```bash
   # prerequisites: make somatic_variants, make facets (or your CN caller)
   make absolute_seq USE_CLUSTER=false       # or omit flag for scheduler run
   ```
   The driver target fans out to these subtasks:
   - `absolute/tables/<pair>.somatic.txt` - merged SNV/indel inputs prepared
     from the Mutect and Strelka tables.
   - `absolute/segment/<pair>.seg.txt` - segmentation generated from FACETS
     (or Titan/Oncoscan outputs when enabled).
   - `absolute/maf/<pair>.maf.txt` - ABSOLUTE-formatted MAF files.
   - `absolute/results/<pair>.ABSOLUTE.RData` - per-sample ABSOLUTE solutions.
   - `absolute/review/all.PP-calls_tab.txt` and
     `absolute/review/all.PP-modes.data.RData` - review bundles for manual
     curation.

# Manual Review
   1. Inspect the plots under `absolute/review/`.  Choose a diploid solution for
      each sample using the standard ABSOLUTE review interface or by editing
      `absolute/review/all.PP-calls_tab.txt`.
   2. Once decisions are recorded, save the file as
      `absolute/review/all.PP-calls_tab.reviewed.txt` (same directory).
   3. Re-run `make absolute_seq` to materialise
      `absolute/reviewed/all.seq.ABSOLUTE.table.txt` and
      `absolute/tables/<pair>.absolute.txt`.  These contain the curated purity,
      ploidy, and CCF annotations.

# Outputs
```
absolute/results/<pair>.ABSOLUTE.RData
absolute/review/all.PP-calls_tab.txt
absolute/review/all.PP-calls_tab.reviewed.txt  # user-supplied
absolute/reviewed/all.seq.ABSOLUTE.table.txt
absolute/tables/<pair>.absolute.txt
absolute/reviewed/SEG_MAF/<pair>_ABS_MAF.txt
```

# Common Issues
   - **Missing facets CN files** - ensure `make facets` completed and that the
     `<pair>.cncf.txt` files follow the `<tumor>_<normal>` naming convention.
   - **ABSOLUTE library unavailable** - source the R environment that contains
     the ABSOLUTE package before launching the target or adjust `RSCRIPT`/`R_LIBS`
     so the library is discoverable.
   - **No reviewed table** - ABSOLUTE will not produce
     `absolute/reviewed/all.seq.ABSOLUTE.table.txt` until
     `all.PP-calls_tab.reviewed.txt` exists.  Copy the unreviewed file, record
     the chosen solutions, and rerun the target.
