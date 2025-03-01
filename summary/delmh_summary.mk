include modules/Makefile.inc
# delmh_summary will generate deletion-micromology summary per samples
# the result is saved as tsv/delmh_summary.tsv 

LOGDIR ?= log/delmh_summary.$(NOW)
PHONY += delmh_summary
DEFAULT_ENV = $(HOME)/share/usr/anaconda-envs/jrflab-modules-0.1.4

delmh_summary : tsv/delmh_summary.tsv

# step 3: summary of filtered delmh
tsv/delmh_summary.tsv : tsv/delmh_filtered.tsv
	$(call RUN,-n 1 -s 24G -m 36G -v $(DEFAULT_ENV),"$(RSCRIPT) modules/summary/delmh_summary.R")

# step 2: filter delmh
tsv/delmh_filtered.tsv : tsv/delmh_found.tsv
	$(call RUN,-n 1 -s 24G -m 36G -v $(DEFAULT_ENV),"$(RSCRIPT) modules/summary/delmh_filter.R")

# step 1: calculate delmh
tsv/delmh_found.tsv : tsv/all.somatic_indels.tsv
	$(call RUN,-n 1 -s 24G -m 36G -v $(DEFAULT_ENV),"python modules/summary/calc_delmh.py" --ref-fasta $(REF_FASTA))

.DELETE_ON_ERROR:
.SECONDARY:
.PHONY: $(PHONY)
