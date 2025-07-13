# Name: 
    extract_any_unmapped_pairs 

# Description
    This target extract all the pairs( either one of the pair is unmapped) from the original bam file, which is useful to determine virus integration site etc.

# Input
        unmapped_reads/%.bam :
            - this is the output from extracReads.mk
                : from extract_unmapped, extract all unmapped reads in the samples' bam files

        bam/%.bam:
            - The orginal bam file is used to extract all the pairs.

# Output
    1. extract_reads/unmapped_pairs/%.txt:
        - all the unmapped reads' unique IDs.

    2. extract_reads/any_unmapped_pairs/%.bam:
        -  all the pairs (either one unmapped) from orginal bam file.

    3. extract_reads/any_unmapped_pairs/fastq/%_1.fastq.gz etc.
        - all the fastq1.gz, fastq2.gz from step 2.
        
# Error
    TODO: 
        - Need to implement a log, or timestamp for things finished etc.
        
    Note/DONE:
        - Also need to clean up intermediate files if error happens/unfinished.
            .DELETE_ON_ERROR - this target already specified this, no need.

# Examples
