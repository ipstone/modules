# Name: 
    mosdepth_wgs
    https://github.com/brentp/mosdepth

# Description
    This receipe calculates whole genome copy number coverage for all
    the samples (tumors and normals separately), with the
    mosdepth_wgs_window parameter specified in the the mk file.

    For a 50x genome, it takes about 50 mins to finish.

# Input
    WGS bam files in the bam/ folder. (bam/%.bam)

# Output
    mosdepth_wgs/ (folder) 
        sample.regions.bed.gz ...

# Error

# Key code:
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

