include modules/Makefile.inc

LOGDIR = log/svabaTN.$(NOW)

SVABA_CORES ?= 8
SVABA_MEM_CORE ?= 6G
SVABA_REF ?= $(REF_FASTA)
# SVABA_DBSNP and SVABA_REGION may come from the genome include (GRCm38.inc
# sets mouse files); the paths below are the human (b37) defaults.
SVABA_DBSNP ?= /data/riazlab/lib/reference/svaba/dbsnp_indel.vcf
# region-inclusion BED for -k: genome minus telomere/centromere (blacklist) regions
SVABA_BLACKLISTED ?= $(if $(SVABA_REGION),$(SVABA_REGION),/data/riazlab/lib/reference/wgs_blacklist_meres.bed)
SVABA ?= /data/riazlab/lib/bin/svaba
SVABA_MATE_LOOKUP_MIN ?= 100000
SVABA_MAX_READS ?= 25000
SVABA_WALLTIME ?= 72:00:00

svabaTN : $(foreach pair,$(SAMPLE_PAIRS),svaba/$(pair).svaba.somatic.indel.vcf)

define svaba-tumor-normal
svaba/$1_$2.svaba.somatic.indel.vcf : bam/$1.bam bam/$2.bam
	$$(call RUN,-c -n $(SVABA_CORES) -s 4G -m $(SVABA_MEM_CORE) -w $(SVABA_WALLTIME),"set -o pipefail && \
										 mkdir -p svaba && \
										 cd svaba && \
										 $$(SVABA) run \
										 -t ../bam/$1.bam \
										 -n ../bam/$2.bam \
										 -p $$(SVABA_CORES) \
										 -D $$(SVABA_DBSNP) \
										 -L $$(SVABA_MATE_LOOKUP_MIN) \
										 -x $$(SVABA_MAX_READS) \
										 -k $$(SVABA_BLACKLISTED) \
										 -a $1_$2 \
										 -G $$(SVABA_REF)")
endef
$(foreach pair,$(SAMPLE_PAIRS),\
		$(eval $(call svaba-tumor-normal,$(tumor.$(pair)),$(normal.$(pair)))))


..DUMMY := $(shell mkdir -p version; \
	     $(SVABA) --help &> version/svabaTN.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: svabaTN
