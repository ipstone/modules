include modules/Makefile.inc

LOGDIR ?= log/bam_to_fasta.$(NOW)

.DELETE_ON_ERROR:
.SECONDARY:
.PHONY: bam_to_fasta

VPATH = unmapped_reads

bam_to_fasta : $(foreach sample,$(SAMPLES),unmapped_reads/$(sample).fasta)

unmapped_reads/%.fasta : unmapped_reads/%.bam
	$(call RUN,-n 4 -s 4G -m 9G,"$(SAMTOOLS2) fasta $< > unmapped_reads/$*.fasta")
