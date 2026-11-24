include modules/Makefile.inc

LOGDIR ?= log/mosdepth_wgs.$(NOW)
PHONY += mosdepth_wgs 
MOSDEPTH_WINDOW = 10000

mosdepth_wgs : $(foreach sample,$(SAMPLES),mosdepth_wgs/$(sample).regions.bed.gz)

define mosdepth-wgs-window
mosdepth_wgs/%.regions.bed.gz : bam/%.bam
	$$(call RUN,-c -s 6G -m 8G,"mkdir -p mosdepth_wgs ; \
		mosdepth -t 4 -n --fast-mode --by $(MOSDEPTH_WINDOW) mosdepth_wgs/$$(*F) $$(<)")
endef
 $(foreach sample,$(SAMPLES),\
		$(eval $(call mosdepth-wgs-window,$(sample))))
				
.PHONY: $(PHONY)

