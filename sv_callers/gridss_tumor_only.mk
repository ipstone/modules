include modules/Makefile.inc

LOGDIR = log/gridss_tumor_only.$(NOW)

GRIDSS_CORES ?= 8
GRIDSS_MEM_CORE ?= 6G
# human: the b37 g1k FASTA prepared for GRIDSS; other species: REF_FASTA
GRIDSS_REF ?= $(if $(filter human,$(SPECIES)),$(HOME)/share/lib/ref_files/b37/human_g1k_v37.fasta,$(REF_FASTA))
# GRIDSS_BLACKLIST (hg19 ENCODE blacklist) and GRIDSS_PON_DIR (human PON)
# default to the human files only when SPECIES=human; for other species they
# are empty and the -b / --pondir options are left out.
GRIDSS_BLACKLIST ?= $(if $(filter human,$(SPECIES)),$(HOME)/share/lib/resource_files/gridss/example/ENCFF001TDO.bed)
GRIDSS ?= gridss
GRIDSS_FILTER ?= gridss_somatic_filter
GRIDSS_PON_DIR ?= $(if $(filter human,$(SPECIES)),$(HOME)/share/lib/resource_files/gridss/pon/)

gridss : $(foreach sample,$(SAMPLES),gridss/$(sample)/$(sample).gridss_sv.vcf) \
	 $(foreach sample,$(SAMPLES),vcf/$(sample).gridss_sv.vcf)

define gridss-tumor-only
gridss/$1/$1.gridss_sv.vcf : bam/$1.bam
	$$(call RUN,-c -n $(GRIDSS_CORES) -s 4G -m $(GRIDSS_MEM_CORE) -v $(GRIDSS_ENV) -w 72:00:00,"set -o pipefail && \
												    mkdir -p gridss/$1 && \
												    cd gridss/$1 && \
												    $$(GRIDSS) \
												    -t $$(GRIDSS_CORES) \
												    -r $$(GRIDSS_REF) \
												    -o $1.gridss_sv.vcf \
												    $$(if $$(GRIDSS_BLACKLIST),-b $$(GRIDSS_BLACKLIST)) \
												    ../../bam/$1.bam")
												    
vcf/$1.gridss_sv.vcf : gridss/$1/$1.gridss_sv.vcf
	$$(INIT) cat $$(<) > $$(@)
	
endef
$(foreach sample,$(SAMPLES),\
		$(eval $(call gridss-tumor-only,$(sample))))


..DUMMY := $(shell mkdir -p version; \
	     echo 'gridss' > version/gridss_tumor_only.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: gridss
