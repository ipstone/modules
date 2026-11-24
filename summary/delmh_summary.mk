include modules/Makefile.inc

LOGDIR ?= log/delmh_summary.$(NOW)
PHONY += delmh_summary

delmh_summary : summary/tsv/delmh_summary.tsv

# DELMH_BSGENOME: BSgenome package with the reference sequence (UCSC, chr-
# prefixed). Unset: the script default, BSgenome.Hsapiens.UCSC.hg19 (b37/hg19).
# GRCm38.inc sets BSgenome.Mmusculus.UCSC.mm10.
summary/tsv/delmh_summary.tsv : summary/tsv/mutation_summary.tsv
	$(call RUN,-n 1 -s 8G -m 8G,"set -o pipefail && \
								 $(RSCRIPT) modules/summary/delmh_summary.R --input_file $(<)$(if $(DELMH_BSGENOME), --bsgenome $(DELMH_BSGENOME))")
	
.DELETE_ON_ERROR:
.SECONDARY:
.PHONY: $(PHONY)
