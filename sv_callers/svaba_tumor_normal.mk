include modules/Makefile.inc

LOGDIR = log/svaba_tumor_normal.$(NOW)

SVABA_QUEUE ?= cpuqueue
SVABA_CORES ?= 16
SVABA_SOFT_MEM ?= 4G
SVABA_MEM_CORE ?= 6G
SVABA_WALLTIME ?= 120:00:00
SVABA_MATE_LOOKUP_MIN ?= 100000
SVABA_MAX_READS ?= 25000
SVABA_REF ?= $(REF_FASTA)
SVABA_DBSNP ?= $(HOME)/share/lib/resource_files/svaba/dbsnp_indel.vcf
SVABA_BLACKLIST ?= $(HOME)/share/lib/resource_files/svaba/wgs_blacklist_meres.bed
SVABA ?= svaba

svaba : $(foreach pair,$(SAMPLE_PAIRS),vcf/$(pair).svaba_sv.vcf)

define svaba-tumor-normal
svaba/$1_$2.svaba.somatic.sv.vcf : bam/$1.bam bam/$2.bam
	$$(call RUN,-c -n $(SVABA_CORES) -s $(SVABA_SOFT_MEM) -m $(SVABA_MEM_CORE) $(if $(SVABA_QUEUE),-q $(SVABA_QUEUE)) -v $(SVABA_ENV) -w $(SVABA_WALLTIME),"set -o pipefail && \
							 mkdir -p svaba && \
							 cd svaba && \
							 $$(SVABA) run \
							 -t ../bam/$1.bam \
							 -n ../bam/$2.bam \
							 -p $$(SVABA_CORES) \
							 -D $$(SVABA_DBSNP) \
							 -L $$(SVABA_MATE_LOOKUP_MIN) \
							 -x $$(SVABA_MAX_READS) \
							 -k $$(SVABA_BLACKLIST) \
							 -a $1_$2 \
							 -G $$(SVABA_REF)")

vcf/$1_$2.svaba_sv.vcf : svaba/$1_$2.svaba.somatic.sv.vcf
	$$(INIT) cat $$< > $$@

endef
$(foreach pair,$(SAMPLE_PAIRS),\
		$(eval $(call svaba-tumor-normal,$(tumor.$(pair)),$(normal.$(pair)))))


..DUMMY := $(shell mkdir -p version; \
	     $(SVABA) --help &> version/svaba_tumor_normal.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: svaba
