# Run fusioncatcher
##### DEFAULTS ######

LOGDIR = log/fusioncatcher.$(NOW)

##### MAKE INCLUDES #####
include modules/Makefile.inc

FUSIONCATCHER = $(HOME)/share/usr/fusioncatcher/fusioncatcher_v0.99.2/fusioncatcher
FUSIONCATCHER_OPTS = -d $(HOME)/share/usr/fusioncatcher/data/current --extract-buffer-size=35000000000

.DELETE_ON_ERROR:
.SECONDARY: 
.PHONY: all

all : $(foreach sample,$(SAMPLES),fusioncatcher/$(sample).fusioncatcher_timestamp)

fusioncatcher/%.fusioncatcher_timestamp : fastq/%.1.fastq.gz fastq/%.2.fastq.gz
	$(call RUN,-n 8 -s 1G -m 4G,"$(FUSIONCATCHER) $(FUSIONCATCHER_OPTS) -p 8 -o $(@D)/$* -i $<$(,)$(<<) && touch $@")
