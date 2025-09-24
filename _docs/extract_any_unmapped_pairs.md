# Name:
    extract_any_unmapped_pairs 

# Description
    Extracts read pairs where either mate is unmapped.  The rule in
    `fastq_tools/extract_any_unmapped_pairs.mk` filters reads listed in
    `extracted_reads/unmapped_pairs/<sample>.txt`, builds a BAM containing all
    pairs, and writes name-sorted FASTQs for downstream viral or insertion-site
    analyses.

# Input
    - `unmapped_reads/<sample>.bam` produced by `make extract_unmapped`.
    - `bam/<sample>.bam` (used by Picard `FilterSamReads`).

# Output
```
extracted_reads/unmapped_pairs/<sample>.txt          # unique read IDs
extracted_reads/any_unmapped_pairs/<sample>.bam      # BAM with any-unmapped pairs
extracted_reads/any_unmapped_pairs/fastq/<sample>.1.fastq.gz
extracted_reads/any_unmapped_pairs/fastq/<sample>.2.fastq.gz
```

# Usage
```
make extract_unmapped USE_CLUSTER=false      # populate unmapped_reads/
make extract_any_unmapped_pairs USE_CLUSTER=false
```
    Omit `USE_CLUSTER=false` to submit through qmake.  The recipe depends on
    `SAMTOOLS2` and the Picard jar configured in `config.inc`.

# Notes
- The FASTQ step sorts by read name before piping to `samtools fastq`; this
  preserves pair ordering and writes gzipped FASTQs.
- Intermediate BAMs are kept so you can inspect them or rerun the FASTQ export
  without recomputing the read ID lists.
- `FilterSamReads` will fail if the expected BAM symlinks are missing.  Verify
  `bam/<sample>.bam` points to the original alignment files before launching the
  target.
