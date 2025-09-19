include modules/Makefile.inc

LOGDIR ?= log/qdnaseq.$(NOW)

qdnaseq : $(foreach sample,$(SAMPLES),qdnaseq/$(sample).txt)

define qdnaseq-extract
qdnaseq/$1.txt : bam/$1.bam
	$$(call RUN,-c -v $(QDNASEQ_ENV) -s 12G -m 24G,"set -o pipefail && \
						        $(RSCRIPT) modules/scripts/qdnaseq.R \
							--sample_name $1")
	
endef
$(foreach sample,$(SAMPLES),\
		$(eval $(call qdnaseq-extract,$(sample))))
		
..DUMMY := $(shell mkdir -p version; \
	     R --version > version/qdnaseq.txt;)
.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: qdnaseq
