include modules/Makefile.inc
include modules/genome_inc/b37.inc

LOGDIR ?= log/fix_bam.$(NOW)
PHONY += fixed_bam

VPATH = fixed_bam unprocessed_bam
PICARD_JAR = ~/share/usr/picard/bin/picard.jar

fix_bam : $(foreach sample,$(SAMPLES),fixed_bam/$(sample).bam)

define fix-bam
unprocessed_bam/%.ubam : unprocessed_bam/%.bam
	$$(call RUN,-c -n 1 -s 8G -m 16G,"java -Xmx8G -jar $$(PICARD_JAR) RevertSam I=$$(<) O=unprocessed_bam/$$(*).ubam SANITIZE=true MAX_DISCARD_FRACTION=0.005 ATTRIBUTE_TO_CLEAR=XT ATTRIBUTE_TO_CLEAR=XN ATTRIBUTE_TO_CLEAR=AS ATTRIBUTE_TO_CLEAR=OC ATTRIBUTE_TO_CLEAR=OP SORT_ORDER=queryname RESTORE_ORIGINAL_QUALITIES=true REMOVE_DUPLICATE_INFORMATION=true REMOVE_ALIGNMENT_INFORMATION=true")
unprocessed_bam/%.fixed.bam : unprocessed_bam/%.ubam
	$$(call RUN, -c -n 1 -s 8G -m 16G,"java -Xmx8G -jar $$(PICARD_JAR) MergeBamAlignment R=$$(REF_FASTA) UNMAPPED_BAM=$$(<) ALIGNED_BAM=unprocessed_bam/$$(*).bam O=unprocessed_bam/$$(*).fixed.bam CREATE_INDEX=true ADD_MATE_CIGAR=true CLIP_ADAPTERS=true CLIP_OVERLAPPING_READS=true INCLUDE_SECONDARY_ALIGNMENTS=false MAX_INSERTIONS_OR_DELETIONS=-1")
unprocessed_bam/%.dedup.bam : unprocessed_bam/%.fixed.bam
	$$(call RUN, -c -n 1 -s 8G -m 16G,"java -Xmx8G -jar $$(PICARD_JAR) MarkDuplicates I=$$(<) O=unprocessed_bam/$$(*).dedup.bam M=unprocessed_bam/$$(*).txt")
fixed_bam/%.bam : unprocessed_bam/%.dedup.bam
	$$(call RUN, -c -n 1 -s 8G -m 16G,"java -Xmx8G -jar $$(PICARD_JAR) AddOrReplaceReadGroups I=$$(<) O=fixed_bam/$$(*).bam RGID=$$(*) RGLB=$$(*) RGPL=illumina RGPU=NA RGSM=$$(*) && samtools index fixed_bam/$$(*).bam && cp fixed_bam/$$(*).bam.bai fixed_bam/$$(*).bai")
endef
 $(foreach sample,$(SAMPLES),\
		$(eval $(call fix-bam,$(sample))))

.DELETE_ON_ERROR:
.SECONDARY:
.PHONY: $(PHONY)
