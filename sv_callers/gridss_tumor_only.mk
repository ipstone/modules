include modules/Makefile.inc

LOGDIR = log/gridss_tumor_normal.$(NOW)

GRIDSS_CORES ?= 8
GRIDSS_MEM_CORE ?= 6G
GRIDSS_REF ?= $(HOME)/share/lib/ref_files/b37/human_g1k_v37.fasta
GRIDSS_BLACKLIST ?= $(HOME)/share/lib/resource_files/gridss/example/ENCFF001TDO.bed
GRIDSS ?= gridss
GRIDSS_FILTER ?= gridss_somatic_filter
GRIDSS_PON_DIR ?= $(HOME)/share/lib/resource_files/gridss/pon/

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
												    -b $$(GRIDSS_BLACKLIST) \
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
