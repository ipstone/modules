## Makefile to run https://github.com/walaj/svaba

include modules/Makefile.inc
LOGDIR ?= log/svabaTN.$(NOW)

.DELETE_ON_ERROR:
.SECONDARY:
.PHONY: svabaTN

VPATH = bam
CORES=16 ## set any number of cores
#SVABAREF=$(HOME)/share/reference/GATK_bundle/2.3/human_g1k_v37.fasta
SVABAREF=$(REF_FASTA)
#DBSNP=/data/riazlab/lib/reference/svaba/dbsnp_indel.vcf
#DBSNP=$(HOME)/share/reference/Sanger_mouse_genome_project_v3_dbSNP137_GRCm38/mgp.v3.indels.rsIDdbSNPv137.vcf
DBSNP=/data/riazlab/lib/reference/dbsnp/mouse/mgp.v5.merged.indels.dbSNP142.normed.vcf
# -- note: the -k option is the target bed file - the one in the pipeline is
#  the one removed telomere etc - so called wgs_blacklist_neres.bed (it's
#  substracted the blacklisted region)

svabaTN : $(foreach pair,$(SAMPLE_PAIRS),svaba/$(pair).svaba.somatic.indel.vcf)

define svaba-tumor-normal
svaba/$1_$2.svaba.somatic.indel.vcf : bam/$1.bam bam/$2.bam
	$$(call RUN,-c -n 16 -s 4G -m 6G -w 7200,"svaba run -t bam/$1.bam -n bam/$2.bam -p $$(CORES) -D $$(DBSNP) -L 100000 -x 25000 -k /data/riazlab/lib/reference/svaba/mouse_mm10_removed_blacklist-regon_no-chr.bed -a $1_$2 -G $$(SVABAREF) && mkdir -p svaba && mv *svaba*.vcf svaba/")
endef
$(foreach pair,$(SAMPLE_PAIRS),\
		$(eval $(call svaba-tumor-normal,$(tumor.$(pair)),$(normal.$(pair)))))
