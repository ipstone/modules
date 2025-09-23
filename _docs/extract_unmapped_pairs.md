# Name:
    extract_unmapped_pairs

# Description
    Extract paired reads from unmapped BAMs, convert to FASTQ, and provide inputs
    for downstream viral detection/krona classification.

# Input
        unmapped_reads/%.bam  
        - this is the output from extracReads.mk
            : from extract_unmapped, extract all unmapped reads in the samples' bam files

# Output
    1. `extracted_reads/unmapped_pairs/%.bam` – paired reads subsetted from
       `unmapped_reads/*.bam`.
    2. `extracted_reads/unmapped_pairs/%.txt` – list of read IDs used to filter.
    3. `extracted_reads/unmapped_pairs/%_1.fastq` / `%_2.fastq` – gz-ready FASTQ
       files for BLAST/viral pipelines.

# Typical Viral Detection Workflow
1. `make extract_unmapped` – populate `unmapped_reads/*.bam` from aligned BAMs.
2. `make extract_unmapped_pairs` – run this target to produce paired FASTQs.
3. `make bam_to_fasta` – transforms BAMs to FASTA format for BLAST.
4. `make blast_reads` – BLASTs unmapped reads against viral references.
5. `make krona_classify` – builds interactive HTML reports inside
   `unmapped_reads/*/krona/`.
6. Download the resulting Krona HTML files for review.

# Notes
- Ensure the jrflab environment is active so Picard/Samtools binaries resolve.
- `unmapped_reads/*.bam` must exist (typically from `extractReads.mk`).
- Large projects benefit from running the steps above in sequence to keep
  dependent outputs fresh.

# Examples
```
make extract_unmapped
make extract_unmapped_pairs
make bam_to_fasta
make blast_reads
make krona_classify
```
