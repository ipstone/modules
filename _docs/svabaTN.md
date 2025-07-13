# Name: 
    svabaTN

# Description
    Run the svaba strucrual variant caller on tumor-normal pairs

# Input
    tumor/normal pairs bam files.

# Output
    svaba/ folder contains 
        vcf files

# Error

# Post processing:
    samples=`basename input/svaba_vcf/*.vcf`
    for i in $samples; do
        Rscript lib/svaba/R/svaba-annotate.R -i input/svaba_vcf/$i -g
        hg19 > output/svaba_annotation/$i.ann.txt
    done

    Annotation R files are located in:
        https://github.com/walaj/svaba/tree/master/R

# Examples
