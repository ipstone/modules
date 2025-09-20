include modules/Makefile.inc
include modules/sv_callers/manta.inc

LOGDIR ?= log/manta_tumor_only.$(NOW)

manta: $(foreach sample,$(SAMPLES),vcf/$(sample).manta_sv.vcf)
	

manta/%/runWorkflow.py : bam/%.bam bam/%.bam.bai
	$(INIT) $(CONFIG_MANTA) $(CONFIG_MANTA_OPTS) --tumorBam $< --runDir $(@D) 

manta/%/results/variants/candidateSV.vcf.gz : manta/%/runWorkflow.py
	$(call RUN,-n 8 -s 2G -m 4G -w 72:00:00,"python $< -m local -j 8")

vcf/%.manta_sv.vcf : manta/%/results/variants/candidateSV.vcf.gz
	$(INIT) zcat $< > $@

..DUMMY := $(shell mkdir -p version; \
	     python --version &> version/manta_tumor_only.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: manta
