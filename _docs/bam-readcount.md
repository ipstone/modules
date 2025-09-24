# Name:
    bam-readcount

# Description
    Helper scripts for generating per-variant readcount summaries using the
    `bam-readcount` binary.  There is no standalone make target; instead you run
    the provided R and Python utilities after somatic calling to build region
    lists, execute `bam-readcount`, and convert the output to tabular format.

# Inputs
    - `tsv/all.mutect.tsv` (all Mutect calls from the somatic workflow).
    - `bam/<sample>.bam` symlinks for every tumor and normal sample.
    - `bam-readcount` executable in `$PATH` (version from
      https://github.com/genome/bam-readcount).

# Workflow
1. Generate target regions and wrapper scripts:
   ```bash
   Rscript qc/bam-readcount_setup.R
   ```
   This creates `bam-readcount/region_tumor/*.txt`,
   `bam-readcount/region_normal/*.txt`, and the shell launchers
   `run_bamreadcount_tumor.sh`, `run_bamreadcount_normal.sh`.  Update the
   reference FASTA path inside the scripts if your environment differs from the
   hard-coded `/home/peix/share/reference/b37_dmp/b37.fasta`.
2. Execute `bam-readcount` for tumors and normals:
   ```bash
   bash run_bamreadcount_tumor.sh
   bash run_bamreadcount_normal.sh
   ```
   Outputs land in `bam-readcount/readcount_tumor/` and
   `bam-readcount/readcount_normal/` with filenames
   `<sample>_readcount.txt`.
3. Convert `bam-readcount` output to TSV:
   ```bash
   python qc/bam-readcount_combine.py bam-readcount/readcount_tumor/<sample>_readcount.txt \
        > bam-readcount/<sample>.tumor.tsv
   python qc/bam-readcount_combine.py bam-readcount/readcount_normal/<sample>_readcount.txt \
        > bam-readcount/<sample>.normal.tsv
   ```
   The converter prints a header plus per-base statistics (`avg_mapping_quality`,
   `avg_basequality`, strand counts, etc.).

# Outputs
```
bam-readcount/region_tumor/<sample>.txt
bam-readcount/region_normal/<sample>.txt
run_bamreadcount_tumor.sh
run_bamreadcount_normal.sh
bam-readcount/readcount_tumor/<sample>_readcount.txt
bam-readcount/readcount_normal/<sample>_readcount.txt
bam-readcount/<sample>.tumor.tsv
bam-readcount/<sample>.normal.tsv
```

# Notes
- The setup script loads `ipfun` and `data.table`; source the jrflab Conda env
  (`JRFLAB_MODULES_ENV`) before running if those libraries are missing.
- The TSV outputs can be merged back into mutation tables for validation or
  inspection alongside Sufam results.
