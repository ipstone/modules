# Run strelka on tumour-normal matched pairs

include modules/Makefile.inc
include modules/variant_callers/gatk.inc
##### DEFAULTS ######


LOGDIR ?= log/strelka.$(NOW)
PHONY += strelka strelka_vcfs strelka_mafs

STRELKA_ENV ?= /lila/data/riazlab/data/peix/miniconda3/envs/strelka-2.9.7
CONFIGURE_STRELKA = $(STRELKA_ENV)/bin/configureStrelkaSomaticWorkflow.py
STRELKA_PYTHON = $(STRELKA_ENV)/bin/python
STRELKA_CONFIG = $(HOME)/share/usr/etc/strelka_config.ini
STRELKA_SOURCE_ANN_VCF = $(STRELKA_PYTHON) modules/vcf_tools/annotate_source_vcf.py --source strelka

strelka : strelka_vcfs #strelka_mafs
	
STRELKA_VARIANT_TYPES := strelka_snps strelka_indels
strelka_vcfs : $(foreach type,$(STRELKA_VARIANT_TYPES),$(foreach pair,$(SAMPLE_PAIRS),vcf/$(pair).$(type).vcf))
strelka_mafs : $(foreach type,$(STRELKA_VARIANT_TYPES),$(foreach pair,$(SAMPLE_PAIRS),maf/$(pair).$(type).maf))

define strelka-tumor-normal
strelka/$1_$2/runWorkflow.py : bam/$1.bam bam/$2.bam
	$$(call RUN,-N strelka_$1_$2,"rm -rf $$(@D) && $$(STRELKA_PYTHON) $$(CONFIGURE_STRELKA) --tumorBam=$$< --normalBam=$$(<<) --referenceFasta=$$(REF_FASTA) --config=$$(STRELKA_CONFIG) --runDir=$$(@D)")

strelka/$1_$2/task.complete : strelka/$1_$2/runWorkflow.py
	$$(call RUN,-N $1_$2.strelka -n 10 -s 40G -m 48G -w 7200,"cd $$(<D) && $$(STRELKA_PYTHON) runWorkflow.py -m local -j 10 && touch task.complete")

strelka/vcf/$1_$2.%.vcf.tmp : strelka/vcf/$1_$2.%.vcf
	$$(call RUN,-s 4G -m 8G -w 7200,"$$(RSCRIPT) modules/scripts/swapvcf.R --file $$< --tumor $1 --normal $2")

vcf/$1_$2.%.vcf : strelka/vcf/$1_$2.%.vcf.tmp
	$$(INIT) perl -ne 'if (/^#CHROM/) { s/NORMAL/$2/; s/TUMOR/$1/; } print;' $$< > $$@ && $$(RM) $$<
	
strelka/vcf/$1_$2.strelka_snps.vcf : strelka/$1_$2/task.complete
	$$(INIT) zcat strelka/$1_$2/results/variants/somatic.snvs.vcf.gz | $$(STRELKA_SOURCE_ANN_VCF) > $$@

strelka/vcf/$1_$2.strelka_indels.vcf : strelka/$1_$2/task.complete
	$$(INIT) zcat strelka/$1_$2/results/variants/somatic.indels.vcf.gz | $$(STRELKA_SOURCE_ANN_VCF) > $$@

endef
$(foreach pair,$(SAMPLE_PAIRS),$(eval $(call strelka-tumor-normal,$(tumor.$(pair)),$(normal.$(pair)))))

include modules/vcf_tools/vcftools.mk

.DELETE_ON_ERROR:
.SECONDARY:
.PHONY: $(PHONY)

