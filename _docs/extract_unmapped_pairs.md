# Name: 
    extract_unmapped_pairs 

# Description
    This make target extract all the pairs from the unmapped bam file.

# Input
        unmapped_reads/%.bam  
        - this is the output from extracReads.mk
            : from extract_unmapped, extract all unmapped reads in the samples' bam files

# Output
    1. extract_reads/unmapped_pairs/%.bam:
        -  all the pairs in the unmapped reads from the samples' bam files.

    2. extract_reads/unmapped_pairs/%.txt:
        - all the unmapped reads' unique IDs.

    3. extract_reads/unmapped_pairs/%_1.fastq etc.
        - all the fastq files from 1.
        
# Error

# Examples
