# Run strelka on tumour-normal matched pairs

include modules/Makefile.inc
include modules/variant_callers/gatk.inc
##### DEFAULTS ######


LOGDIR ?= log/strelka.$(NOW)
PHONY += strelka strelka_vcfs strelka_mafs

# STRELKA_VERSION selects the recipe: 1 = Strelka 1 (default, unchanged);
# 2 = Strelka2 (configureStrelkaSomaticWorkflow.py) from STRELKA_ENV, as used
# by the mouse WGS projects. Strelka2 adds --exome for SEQ_TYPE WES/PANEL.
STRELKA_VERSION ?= 1
STRELKA_CONFIG = $(HOME)/share/usr/etc/strelka_config.ini
ifeq ($(STRELKA_VERSION),2)
STRELKA_ENV ?= /lila/data/riazlab/data/peix/miniconda3/envs/strelka-2.9.7
STRELKA_PYTHON ?= $(STRELKA_ENV)/bin/python
CONFIGURE_STRELKA = $(STRELKA_ENV)/bin/configureStrelkaSomaticWorkflow.py
# the mouse_wgs branch passed the Strelka 1 ini here; set empty to omit --config
STRELKA2_CONFIG ?= $(STRELKA_CONFIG)
STRELKA2_RUN_RESOURCES ?= -s 40G -m 48G -w 7200
STRELKA_SOURCE_ANN_VCF = $(STRELKA_PYTHON) modules/vcf_tools/annotate_source_vcf.py --source strelka
else
CONFIGURE_STRELKA = $(PERL) $(HOME)/share/usr/bin/configureStrelkaWorkflow.pl
STRELKA_SOURCE_ANN_VCF = python modules/vcf_tools/annotate_source_vcf.py --source strelka
endif

strelka : strelka_vcfs #strelka_mafs
	
STRELKA_VARIANT_TYPES := strelka_snps strelka_indels
strelka_vcfs : $(foreach type,$(STRELKA_VARIANT_TYPES),$(foreach pair,$(SAMPLE_PAIRS),vcf/$(pair).$(type).vcf))
strelka_mafs : $(foreach type,$(STRELKA_VARIANT_TYPES),$(foreach pair,$(SAMPLE_PAIRS),maf/$(pair).$(type).maf))

ifeq ($(STRELKA_VERSION),2)
define strelka-tumor-normal
strelka/$1_$2/runWorkflow.py : bam/$1.bam bam/$2.bam
	$$(call RUN,-N strelka_$1_$2,"rm -rf $$(@D) && $$(STRELKA_PYTHON) $$(CONFIGURE_STRELKA) --tumorBam=$$< --normalBam=$$(<<) --referenceFasta=$$(REF_FASTA) $$(if $$(STRELKA2_CONFIG),--config=$$(STRELKA2_CONFIG)) $$(if $$(filter WES PANEL,$$(SEQ_TYPE)),--exome) --runDir=$$(@D)")

strelka/$1_$2/task.complete : strelka/$1_$2/runWorkflow.py
	$$(call RUN,-N $1_$2.strelka -n 10 $$(STRELKA2_RUN_RESOURCES),"cd $$(<D) && $$(STRELKA_PYTHON) runWorkflow.py -m local -j 10 && touch task.complete")

strelka/vcf/$1_$2.%.vcf.tmp : strelka/vcf/$1_$2.%.vcf
	$$(call RUN,$$(STRELKA_SWAP_RESOURCES),"$$(RSCRIPT) modules/scripts/swapvcf.R --file $$< --tumor $1 --normal $2")

vcf/$1_$2.%.vcf : strelka/vcf/$1_$2.%.vcf.tmp
	$$(INIT) perl -ne 'if (/^#CHROM/) { s/NORMAL/$2/; s/TUMOR/$1/; } print;' $$< > $$@ && $$(RM) $$<

strelka/vcf/$1_$2.strelka_snps.vcf : strelka/$1_$2/task.complete
	$$(INIT) zcat strelka/$1_$2/results/variants/somatic.snvs.vcf.gz | $$(STRELKA_SOURCE_ANN_VCF) > $$@

strelka/vcf/$1_$2.strelka_indels.vcf : strelka/$1_$2/task.complete
	$$(INIT) zcat strelka/$1_$2/results/variants/somatic.indels.vcf.gz | $$(STRELKA_SOURCE_ANN_VCF) > $$@

endef
else
define strelka-tumor-normal
strelka/$1_$2/Makefile : bam/$1.bam bam/$2.bam
	$$(call RUN,-N strelka_$1_$2,"rm -rf $$(@D) && $$(CONFIGURE_STRELKA) --tumor=$$< --normal=$$(<<) --ref=$$(REF_FASTA) --config=$$(STRELKA_CONFIG) --output-dir=$$(@D)")

strelka/$1_$2/task.complete : strelka/$1_$2/Makefile
	$$(call RUN,-N $1_$2.strelka -n 10 $$(STRELKA_RUN_RESOURCES),"make -j 10 -C $$(<D)")

strelka/vcf/$1_$2.%.vcf.tmp : strelka/vcf/$1_$2.%.vcf
	$$(call RUN,$$(STRELKA_SWAP_RESOURCES),"$$(RSCRIPT) modules/scripts/swapvcf.R --file $$< --tumor $1 --normal $2")

vcf/$1_$2.%.vcf : strelka/vcf/$1_$2.%.vcf.tmp
	$$(INIT) perl -ne 'if (/^#CHROM/) { s/NORMAL/$2/; s/TUMOR/$1/; } print;' $$< > $$@ && $$(RM) $$<
	
strelka/vcf/$1_$2.strelka_snps.vcf : strelka/$1_$2/task.complete
	$$(INIT) $$(STRELKA_SOURCE_ANN_VCF) < strelka/$1_$2/results/all.somatic.snvs.vcf > $$@

strelka/vcf/$1_$2.strelka_indels.vcf : strelka/$1_$2/task.complete
	$$(INIT) $$(STRELKA_SOURCE_ANN_VCF) < strelka/$1_$2/results/all.somatic.indels.vcf > $$@

endef
endif
$(foreach pair,$(SAMPLE_PAIRS),$(eval $(call strelka-tumor-normal,$(tumor.$(pair)),$(normal.$(pair)))))

include modules/vcf_tools/vcftools.mk

.DELETE_ON_ERROR:
.SECONDARY:
.PHONY: $(PHONY)

