include modules/Makefile.inc

LOGDIR = log/mixcr_tumor_normal.$(NOW)

mixcr : $(foreach sample,$(SAMPLES),mixcr/$(sample)/$(sample).1.fastq.gz) \
	$(foreach sample,$(SAMPLES),mixcr/$(sample)/alignments.vdjca) \
	$(foreach sample,$(SAMPLES),mixcr/$(sample)/alignments_rescued_1.vdjca) \
	$(foreach sample,$(SAMPLES),mixcr/$(sample)/alignments_rescued_2.vdjca)

define extract-fastq
mixcr/$1/$1.1.fastq : bam/$1.bam
	$$(call RUN,-n 4 -s 4G -m 9G,"set -o pipefail && \
				      mkdir -p mixcr/$1 && \
				      $$(SAMTOOLS) sort -T mixcr/$1/$1 -O bam -n -@ 4 -m 6G $$(<) | \
				      bedtools bamtofastq -i - -fq mixcr/$1/$1.1.fastq -fq2 mixcr/$1/$1.2.fastq")

mixcr/$1/$1.1.fastq.gz : mixcr/$1/$1.1.fastq
	$$(call RUN,-n 4 -s 4G -m 9G,"set -o pipefail && \
				      gzip mixcr/$1/$1.1.fastq && \
				      gzip mixcr/$1/$1.2.fastq")
				      
endef
$(foreach sample,$(SAMPLES),\
		$(eval $(call extract-fastq,$(sample))))


define mixcr-tumor-normal
mixcr/$1/alignments.vdjca : mixcr/$1/$1.1.fastq.gz
	$$(call RUN,-n 8 -s 4G -m 6G -v $(MIXCR_ENV) -w 24:00:00,"set -o pipefail && \
								  mixcr align \
								  --species hsa \
								  --preset rna-seq \
								  --dna \
								  --threads 8 \
								  --verbose \
								  mixcr/$1/$1.1.fastq.gz mixcr/$1/$1.2.fastq.gz \
								  $$(@)")

mixcr/$1/alignments_rescued_1.vdjca : mixcr/$1/alignments.vdjca
	$$(call RUN,-n 8 -s 4G -m 6G -v $(MIXCR_ENV) -w 24:00:00,"set -o pipefail && \
								  mixcr assemblePartial \
								  $$(<) \
								  $$(@)")
								  
mixcr/$1/alignments_rescued_2.vdjca : mixcr/$1/alignments_rescued_1.vdjca
	$$(call RUN,-n 8 -s 4G -m 6G -v $(MIXCR_ENV) -w 24:00:00,"set -o pipefail && \
								  mixcr assemblePartial \
								  $$(<) \
								  $$(@)")
								  
endef
$(foreach sample,$(SAMPLES),\
		$(eval $(call mixcr-tumor-normal,$(sample))))


..DUMMY := $(shell mkdir -p version; \
	     echo 'mixcr' > version/mixcr_tumor_normal.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: mixcr
