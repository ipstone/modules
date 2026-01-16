include modules/Makefile.inc

LOGDIR = log/mixcr_tumor_only.$(NOW)

mixcr : $(foreach sample,$(SAMPLES),mixcr/$(sample)/$(sample).1.fastq.gz)

define mixcr-tumor-only
mixcr/$1/$1.1.fastq : bam/$1.bam
	$$(call RUN,-n 4 -s 4G -m 9G,"set -o pipefail && \
				      mkdir -p mixcr/$1 && \
				      $$(SAMTOOLS) sort -T mixcr/$1/$1 -O bam -n -@ 4 -m 6G $$(<) | \
				      bedtools bamtofastq -i - -fq mixcr/$1/$1.1.fastq -fq2 kallisto/$1/$1.2.fastq")

mixcr/$1/$1.1.fastq.gz : mixcr/$1/$1.1.fastq
	$$(call RUN,-n 4 -s 4G -m 9G,"set -o pipefail && \
				      gzip mixcr/$1/$1.1.fastq && \
				      gzip mixcr/$1/$1.2.fastq")



endef
$(foreach sample,$(SAMPLES),\
		$(eval $(call mixcr-tumor-only,$(sample))))


..DUMMY := $(shell mkdir -p version; \
	     echo 'mixcr' > version/mixcr_tumor_only.txt)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: mixcr
