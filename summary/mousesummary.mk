include modules/Makefile.inc

LOGDIR ?= log/mouse_summary.$(NOW)

mouse_summary : mouse_summary/summary.xlsx

mouse_summary/summary.xlsx : $(foreach pair,$(SAMPLE_PAIRS),facets/cncf/$(pair).Rdata) \
			     $(foreach pair,$(SAMPLE_PAIRS),mutect/vcf/$(pair).vcf) \
			     $(foreach pair,$(SAMPLE_PAIRS),strelka/vcf/$(pair).vcf)
	$(call RUN,-n 1 -s 8G -m 12G,"set -o pipefail && \
				      $(RSCRIPT) modules/summary/mousesummary.R \
				      --sample_pairs '$(SAMPLE_PAIRS)' \
				      --out_file $(@)")

.DELETE_ON_ERROR:
.SECONDARY:
.PHONY: mouse_summary