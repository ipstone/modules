# Run unified genotyper on snp positions and cluster samples using results
##### DEFAULTS ######
LOGDIR = log/cluster_samples.$(NOW)

##### MAKE INCLUDES #####
include modules/Makefile.inc
include modules/variant_callers/gatk.inc
VPATH ?= bam

.DELETE_ON_ERROR:
.SECONDARY: 
.PHONY : all

ifeq ($(EXOME),true)
#DBSNP_SUBSET ?= $(HOME)/share/reference/dbsnp_137_exome.bed
DBSNP_SUBSET ?= $(HOME)/share/reference/mus_musculus_known_genes_exons_GRCm38_noheader.bed
# -- modified subset to the mouse exome region
else
#DBSNP_SUBSET = $(HOME)/share/reference/dbsnp_tseq_intersect.bed
DBSNP_SUBSET ?= $(HOME)/share/reference/mus_musculus_known_genes_exons_GRCm38_noheader.bed
# -- modified subset to the mouse exome region
endif

CLUSTER_VCF = $(RSCRIPT) modules/contamination/clusterSampleVcf.R

all : snp_vcf/snps_filtered.clust.png

#snp_vcf/snps.vcf : $(foreach sample,$(SAMPLES),bam/$(sample).bam)
#$(call RUN,-s 4G -m 8G,"$(SAMTOOLS) mpileup -f $(REF_FASTA) -g -l <(sed '/^#/d' $(DBSNP) | cut -f 1,2) $^ | $(BCFTOOLS) view -g - > $@")

snp_vcf/snps.vcf : $(foreach sample,$(SAMPLES),snp_vcf/$(sample).snps.vcf)
	$(call RUN,-s 16G -m 20G,"$(call GATK_MEM,14G) -T CombineVariants $(foreach vcf,$^,--variant $(vcf) ) -o $@ --genotypemergeoption UNSORTED -R $(REF_FASTA)")

snp_vcf/snps_filtered.vcf : snp_vcf/snps.vcf
	$(INIT) grep '^#' $< > $@ && grep -e '0/1' -e '1/1' $< >> $@

snp_vcf/%.snps.vcf : bam/%.bam 
	$(call RUN,-n 4 -s 2.5G -m 3G,"$(call GATK_MEM,8G) -T UnifiedGenotyper -nt 4 -R $(REF_FASTA) --dbsnp $(DBSNP) $(foreach bam,$(filter %.bam,$^),-I $(bam) ) -L $(DBSNP_SUBSET) -o $@ --output_mode EMIT_ALL_SITES")

snp_vcf/%.clust.png : snp_vcf/%.vcf
	$(INIT) $(CLUSTER_VCF) --outPrefix snp_vcf/$* $<

include modules/vcf_tools/vcftools.mk
