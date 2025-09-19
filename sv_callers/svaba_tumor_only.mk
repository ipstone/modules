include modules/Makefile.inc

LOGDIR = log/svaba_tumor_normal.$(NOW)

SVABA_CORES ?= 8
SVABA_MEM_CORE ?= 6G
SVABA_REF ?= $(REF_FASTA)
SVABA_DBSNP ?= $(HOME)/share/lib/resource_files/svaba/dbsnp_indel.vcf
SVABA_BLACKLIST ?= $(HOME)/share/lib/resource_files/svaba/wgs_blacklist_meres.bed
SVABA ?= svaba

svaba : $(foreach sample,$(SAMPLES),vcf/$(sample).svaba_sv.vcf)

define svaba-tumor-only
svaba/$1.svaba.somatic.sv.vcf : bam/$1.bam
	$$(call RUN,-c -n $(SVABA_CORES) -s 4G -m $(SVABA_MEM_CORE) -v $(SVABA_ENV) -w 72:00:00,"set -o pipefail && \
												 mkdir -p svaba && \
										 		 cd svaba && \
												 $$(SVABA) run \
												 -t ../bam/$1.bam \
												 -p $$(SVABA_CORES) \
												 -D $$(SVABA_DBSNP) \
												 -L 6 \
												 -k $$(SVABA_BLACKLIST) \
												 -a $1 \
												 -G $$(SVABA_REF)")
												 
vcf/$1.svaba_sv.vcf : svaba/$1.svaba.somatic.sv.vcf
	$$(INIT) cat $$< > $$@

endef
$(foreach pair,$(SAMPLES),\
		$(eval $(call svaba-tumor-only,$(sample))))


..DUMMY := $(shell mkdir -p version; \
	     $(SVABA) --help &> version/svaba_tumor_normal.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: svaba
