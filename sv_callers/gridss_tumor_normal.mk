include modules/Makefile.inc

LOGDIR = log/gridss_tumor_normal.$(NOW)

GRIDSS_CORES ?= 16
GRIDSS_SOFT_MEM ?= 6G
GRIDSS_HARD_MEM ?= 10G
GRIDSS_QUEUE ?= cpuqueue
GRIDSS_WALLTIME ?= 168:00:00
GRIDSS_CORE_ULIMIT ?= 0
# GRIDSS_REF ?= $(HOME)/share/lib/ref_files/b37/human_g1k_v37.fasta
# GRIDSS_REF ?= $(REF_FASTA)
GRIDSS_REF ?= /data/riazlab/lib/reference/b37_dmp/b37.fasta
GRIDSS_BLACKLIST ?= $(HOME)/share/lib/resource_files/gridss/example/ENCFF001TDO.bed
GRIDSS ?= gridss
GRIDSS_FILTER ?= gridss_somatic_filter
GRIDSS_PON_DIR ?= $(HOME)/share/lib/resource_files/gridss/pon/
GRIDSS_FILTER_SOFT_MEM ?= 32G
GRIDSS_FILTER_HARD_MEM ?= 48G
GRIDSS_FILTER_QUEUE ?= $(GRIDSS_QUEUE)
GRIDSS_FILTER_WALLTIME ?= 72:00:00
GRIDSS_FILTER_THREADS ?= 2
GRIDSS_FILTER_ENV ?= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

gridss : $(foreach pair,$(SAMPLE_PAIRS),gridss/$(pair)/$(pair).gridss_sv.vcf) \
	 $(foreach pair,$(SAMPLE_PAIRS),gridss/$(pair)/$(pair).gridss_sv_ft.vcf.bgz) \
	 $(foreach pair,$(SAMPLE_PAIRS),vcf/$(pair).gridss_sv.vcf) \
	 $(foreach pair,$(SAMPLE_PAIRS),gridss/$(pair)/taskcomplete)

define gridss-tumor-normal
gridss/$1_$2/$1_$2.gridss_sv.vcf : bam/$1.bam bam/$2.bam
	$$(call RUN,-c -n $(GRIDSS_CORES) -s $(GRIDSS_SOFT_MEM) -m $(GRIDSS_HARD_MEM) $(if $(GRIDSS_QUEUE),-q $(GRIDSS_QUEUE)) -v $(GRIDSS_ENV) -w $(GRIDSS_WALLTIME),"set -o pipefail && \
							    ulimit -c $$(GRIDSS_CORE_ULIMIT) && \
							    mkdir -p gridss/$1_$2 && \
							    cd gridss/$1_$2 && \
							    $$(GRIDSS) \
							    -t $$(GRIDSS_CORES) \
							    -r $$(GRIDSS_REF) \
							    -o $1_$2.gridss_sv.vcf \
							    -b $$(GRIDSS_BLACKLIST) \
							    ../../bam/$2.bam \
							    ../../bam/$1.bam")
							    
gridss/$1_$2/$1_$2.gridss_sv_ft.vcf.bgz : gridss/$1_$2/$1_$2.gridss_sv.vcf
	$$(call RUN,-c -n 1 -s $(GRIDSS_FILTER_SOFT_MEM) -m $(GRIDSS_FILTER_HARD_MEM) $(if $(GRIDSS_FILTER_QUEUE),-q $(GRIDSS_FILTER_QUEUE)) -v $(GRIDSS_ENV) -w $(GRIDSS_FILTER_WALLTIME),"set -o pipefail && \
							    ulimit -c $$(GRIDSS_CORE_ULIMIT) && \
							    cd gridss/$1_$2 && \
							    $$(GRIDSS_FILTER_ENV) $$(GRIDSS_FILTER) \
							    --pondir $$(GRIDSS_PON_DIR) \
							    --input $1_$2.gridss_sv.vcf \
							    --output $1_$2.gridss_sv_ft.vcf \
							    -n 1 \
							    -t $$(GRIDSS_FILTER_THREADS)")

vcf/$1_$2.gridss_sv.vcf : gridss/$1_$2/$1_$2.gridss_sv_ft.vcf.bgz
	$$(INIT) zcat $$(<) > $$(@)
	
gridss/$1_$2/taskcomplete : vcf/$1_$2.gridss_sv.vcf
	$$(INIT) rm -f gridss/$1_$2/$1.bam.gridss.working/$1.bam.sv.bam && \
		 rm -f gridss/$1_$2/$1.bam.gridss.working/$1.bam.sv.bam.bai && \
		 rm -f gridss/$1_$2/$2.bam.gridss.working/$2.bam.sv.bam && \
		 rm -f gridss/$1_$2/$2.bam.gridss.working/$2.bam.sv.bam.bai && \
		 rm -f gridss/$1_$2/$1_$2.gridss_sv.vcf.assembly.bam.gridss.working/$1_$2.gridss_sv.vcf.assembly.bam.sv.bam && \
		 rm -f gridss/$1_$2/$1_$2.gridss_sv.vcf.assembly.bam.gridss.working/$1_$2.gridss_sv.vcf.assembly.bam.sv.bam.bai && \
		 echo 'complete!' > $$(@)

endef
$(foreach pair,$(SAMPLE_PAIRS),\
		$(eval $(call gridss-tumor-normal,$(tumor.$(pair)),$(normal.$(pair)))))


..DUMMY := $(shell mkdir -p version; \
	     echo 'gridss' > version/gridss_tumor_normal.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: gridss
