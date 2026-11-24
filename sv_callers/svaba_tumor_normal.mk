include modules/Makefile.inc

LOGDIR = log/svaba_tumor_normal.$(NOW)

# SVABA_VERSION selects the recipe: 1 = svaba 1.1.0 (default, $(SVABA_ENV)),
# 2 = svaba 2.0.0 (run + postprocess + tovcf). For 2.0.0 on lilac set, e.g.,
# SVABA = /data/riazlab/lib/bin/svaba and SVABA_ENV = (empty) in project_config.
# Read sv_callers/SVABA_SETUP_NOTES.md before using svaba 2.0.0.
SVABA_VERSION ?= 1
SVABA_QUEUE ?= cpuqueue
SVABA_CORES ?= 16
SVABA_REF ?= $(REF_FASTA)
SVABA_DBSNP ?= $(HOME)/share/lib/resource_files/svaba/dbsnp_indel.vcf
# Region-INCLUSION file passed to -k (whole genome minus centromere/telomere
# gaps). The historic variable name says "blacklist", but it is not an
# exclusion list. Passing it to svaba 2.0.0 --blacklist masks ~97% of the
# genome and gives empty output.
SVABA_BLACKLIST ?= $(HOME)/share/lib/resource_files/svaba/wgs_blacklist_meres.bed
SVABA_REGION ?= $(SVABA_BLACKLIST)
# True exclusion list for svaba 2.0.0 --blacklist; empty by default because the
# bundled svaba blacklists are hg38/chr-prefixed.
SVABA_EXCLUDE_BED ?=
SVABA ?= svaba

ifeq ($(SVABA_VERSION),2)
SVABA_SOFT_MEM ?= 8G
SVABA_MEM_CORE ?= 14G
SVABA_POSTPROCESS_MEM ?= 6G
SVABA_WALLTIME ?= 168:00:00
SVABA_MATE_MIN ?= 3
SVABA_MATE_LIM ?= 400
else
SVABA_SOFT_MEM ?= 4G
SVABA_MEM_CORE ?= 6G
SVABA_WALLTIME ?= 120:00:00
SVABA_MATE_LOOKUP_MIN ?= 100000
SVABA_MAX_READS ?= 25000
endif

svaba : $(foreach pair,$(SAMPLE_PAIRS),vcf/$(pair).svaba_sv.vcf)

ifeq ($(SVABA_VERSION),2)
# svaba 2.0.0 postprocess writes three breakpoint tables:
#   <id>.bps.sorted.dedup.txt.gz              all breakpoints, somatic + germline
#   <id>.bps.sorted.dedup.pass.txt.gz         passing
#   <id>.bps.sorted.dedup.pass.somatic.txt.gz passing AND somatic
# tovcf converts whatever table it is given without filtering. Converting the
# combined table put ~91% germline records into the somatic VCF (WGS_CDH1SV
# audit, 2026-08-27), so the tumour/normal recipe converts pass.somatic only.
define svaba-tumor-normal
svaba/$1_$2.sv.vcf.gz : bam/$1.bam bam/$2.bam
	$$(call RUN,-c -n $(SVABA_CORES) -s $(SVABA_SOFT_MEM) -m $(SVABA_MEM_CORE) $(if $(SVABA_QUEUE),-q $(SVABA_QUEUE)) $(if $(SVABA_ENV),-v $(SVABA_ENV)) -w $(SVABA_WALLTIME),"set -o pipefail && \
							 mkdir -p svaba && \
							 cd svaba && \
							 $$(SVABA) run \
							 -t ../bam/$1.bam \
							 -n ../bam/$2.bam \
							 -p $$(SVABA_CORES) \
							 --dbsnp $$(SVABA_DBSNP) \
							 --mate-min $$(SVABA_MATE_MIN) \
							 --mate-lim $$(SVABA_MATE_LIM) \
							 $(if $(SVABA_REGION),-k $(SVABA_REGION)) \
							 $(if $(SVABA_EXCLUDE_BED),--blacklist $(SVABA_EXCLUDE_BED)) \
							 -a $1_$2 \
							 -G $$(SVABA_REF) && \
							 $$(SVABA) postprocess \
							 -i $1_$2 \
							 -t $$(SVABA_CORES) \
							 -m $$(SVABA_POSTPROCESS_MEM) && \
							 $$(SVABA) tovcf \
							 -i $1_$2.bps.sorted.dedup.pass.somatic.txt.gz \
							 -b ../bam/$1.bam \
							 -a $1_$2")

vcf/$1_$2.svaba_sv.vcf : svaba/$1_$2.sv.vcf.gz
	$$(INIT) zcat $$< > $$@

endef
else
define svaba-tumor-normal
svaba/$1_$2.svaba.somatic.sv.vcf : bam/$1.bam bam/$2.bam
	$$(call RUN,-c -n $(SVABA_CORES) -s $(SVABA_SOFT_MEM) -m $(SVABA_MEM_CORE) $(if $(SVABA_QUEUE),-q $(SVABA_QUEUE)) $(if $(SVABA_ENV),-v $(SVABA_ENV)) -w $(SVABA_WALLTIME),"set -o pipefail && \
							 mkdir -p svaba && \
							 cd svaba && \
							 $$(SVABA) run \
							 -t ../bam/$1.bam \
							 -n ../bam/$2.bam \
							 -p $$(SVABA_CORES) \
							 -D $$(SVABA_DBSNP) \
							 -L $$(SVABA_MATE_LOOKUP_MIN) \
							 -x $$(SVABA_MAX_READS) \
							 -k $$(SVABA_REGION) \
							 -a $1_$2 \
							 -G $$(SVABA_REF)")

vcf/$1_$2.svaba_sv.vcf : svaba/$1_$2.svaba.somatic.sv.vcf
	$$(INIT) cat $$< > $$@

endef
endif
$(foreach pair,$(SAMPLE_PAIRS),\
		$(eval $(call svaba-tumor-normal,$(tumor.$(pair)),$(normal.$(pair)))))


..DUMMY := $(shell mkdir -p version; \
	     $(SVABA) --help &> version/svaba_tumor_normal.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: svaba
