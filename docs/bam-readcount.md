# Name: 
    bam-readcount
     https://github.com/genome/bam-readcount


# Description
    This pipeline target bam-readcount will use the mutect output, to run
        bam-readcount on the all the mutation position to general
            bam-readcount results on the 
                tumor and 
                normal tissue.

# Input
    mutect call results : 
        at: tsv/all.mutect.tsv
    bam files 
        at bam/ folder. (bam/%.bam)

# Output
    Final output:
        bam-readcount/
            bam-readcount_tumor.tsv
            bam-readcount_normal.tsv

    Intermediate files and running pipelines:
        # The followings are generated by R script

        bamreadcount_setup.R :
            setup the following folders and file for running
            bamreadcount

            bam-readcount/
                region_tumor/   # Contains the regions to be run
                region_normal/  # normal tissue region
                run_bamreadcount_tumor.sh # bash script to do the calling
                run_bamreadcount_normal.sh

        # The following will parse out the bamreadcount details

        bamreadcount_combine.py :
            Extract information from bamreadcount outupt,and results in:
                 bam-readcount_tumor.tsv
                 bam-readcount_normal.tsv


# Error

# Key code:

