include modules/Makefile.inc

LOGDIR ?= log/wgs_metrics.$(NOW)

METRICS_JAVA ?= $(JAVA8)
METRICS_PICARD_JAR ?= $(JARDIR)/picard-2.8.2.jar
METRICS_COMMON_OPTS ?= $(PICARD_OPTS) TMP_DIR=$(TMPDIR)

DEFAULT_METRICS_SWAP ?= 12G
DEFAULT_METRICS_MEM ?= 24G
DEFAULT_METRICS_WALLTIME ?= 24:00:00
DEFAULT_METRICS_HEAP ?= 10G

OXOG_METRICS_SWAP ?= $(DEFAULT_METRICS_SWAP)
OXOG_METRICS_MEM ?= $(DEFAULT_METRICS_MEM)
OXOG_METRICS_WALLTIME ?= 48:00:00
OXOG_METRICS_HEAP ?= $(DEFAULT_METRICS_HEAP)

WGS_METRICS_SWAP ?= $(DEFAULT_METRICS_SWAP)
WGS_METRICS_MEM ?= $(DEFAULT_METRICS_MEM)
WGS_METRICS_WALLTIME ?= 72:00:00
WGS_METRICS_HEAP ?= $(DEFAULT_METRICS_HEAP)

DUPLICATE_METRICS_SWAP ?= 16G
DUPLICATE_METRICS_MEM ?= 32G
DUPLICATE_METRICS_WALLTIME ?= 72:00:00
DUPLICATE_METRICS_HEAP ?= 12G

ENABLE_OXOG_METRICS ?= true
# MarkDuplicates is timing out for some samples; disable duplicate metrics until
# the WGS metrics path is stable again.
ENABLE_DUPLICATE_METRICS ?= false

WGS_METRICS_DEPS = $(foreach sample,$(SAMPLES),metrics/$(sample).idx_stats.txt) \
                   $(foreach sample,$(SAMPLES),metrics/$(sample).aln_metrics.txt) \
                   $(foreach sample,$(SAMPLES),metrics/$(sample).insert_metrics.txt) \
                   $(foreach sample,$(SAMPLES),metrics/$(sample).gc_metrics_summary.txt) \
                   $(foreach sample,$(SAMPLES),metrics/$(sample).wgs_metrics.txt) \
                   summary/idx_metrics.txt \
                   summary/aln_metrics.txt \
                   summary/insert_metrics.txt \
                   summary/gc_metrics.txt \
                   summary/wgs_metrics.txt

ifeq ($(filter false FALSE no NO 0,$(ENABLE_OXOG_METRICS)),)
WGS_METRICS_DEPS += $(foreach sample,$(SAMPLES),metrics/$(sample).oxog_metrics.txt) \
                    summary/oxog_metrics.txt
endif

ifeq ($(filter false FALSE no NO 0,$(ENABLE_DUPLICATE_METRICS)),)
WGS_METRICS_DEPS += $(foreach sample,$(SAMPLES),metrics/$(sample).duplicate_metrics.txt) \
                    summary/duplicate_metrics.txt
endif

wgs_metrics : $(WGS_METRICS_DEPS)

SAMTOOLS_THREADS = 4
SAMTOOLS_MEM_THREAD = 1G

GATK_THREADS = 4
GATK_MEM_THREAD = 2G

define picard-metrics
metrics/$1.idx_stats.txt : bam/$1.bam
	$$(call RUN, -c -n 1 -s $(DEFAULT_METRICS_SWAP) -m $(DEFAULT_METRICS_MEM) -w $(DEFAULT_METRICS_WALLTIME),"set -o pipefail && \
						$(METRICS_JAVA) -Xmx$(DEFAULT_METRICS_HEAP) -jar $(METRICS_PICARD_JAR) BamIndexStats \
						$(METRICS_COMMON_OPTS) \
						INPUT=$$(<) \
						> $$(@)")

metrics/$1.aln_metrics.txt : bam/$1.bam
	$$(call RUN, -c -n 1 -s $(DEFAULT_METRICS_SWAP) -m $(DEFAULT_METRICS_MEM) -w $(DEFAULT_METRICS_WALLTIME),"set -o pipefail && \
						$(METRICS_JAVA) -Xmx$(DEFAULT_METRICS_HEAP) -jar $(METRICS_PICARD_JAR) CollectAlignmentSummaryMetrics \
						$(METRICS_COMMON_OPTS) \
						REFERENCE_SEQUENCE=$$(REF_FASTA) \
						INPUT=$$(<) \
						OUTPUT=$$(@)")

metrics/$1.insert_metrics.txt : bam/$1.bam
	$$(call RUN, -c -n 1 -s $(DEFAULT_METRICS_SWAP) -m $(DEFAULT_METRICS_MEM) -w $(DEFAULT_METRICS_WALLTIME),"set -o pipefail && \
						$(METRICS_JAVA) -Xmx$(DEFAULT_METRICS_HEAP) -jar $(METRICS_PICARD_JAR) CollectInsertSizeMetrics \
						$(METRICS_COMMON_OPTS) \
						INPUT=$$(<) \
						OUTPUT=$$(@) \
						HISTOGRAM_FILE=metrics/$1.insert_metrics.pdf \
						MINIMUM_PCT=0.05")

metrics/$1.oxog_metrics.txt : bam/$1.bam
	$$(call RUN, -c -n 1 -s $(OXOG_METRICS_SWAP) -m $(OXOG_METRICS_MEM) -w $(OXOG_METRICS_WALLTIME),"set -o pipefail && \
						$(METRICS_JAVA) -Xmx$(OXOG_METRICS_HEAP) -jar $(METRICS_PICARD_JAR) CollectOxoGMetrics \
						$(METRICS_COMMON_OPTS) \
						REFERENCE_SEQUENCE=$$(REF_FASTA) \
						INPUT=$$(<) \
						OUTPUT=$$(@)")

metrics/$1.gc_metrics_summary.txt : bam/$1.bam
	$$(call RUN, -c -n 1 -s $(DEFAULT_METRICS_SWAP) -m $(DEFAULT_METRICS_MEM) -w $(DEFAULT_METRICS_WALLTIME),"set -o pipefail && \
						$(METRICS_JAVA) -Xmx$(DEFAULT_METRICS_HEAP) -jar $(METRICS_PICARD_JAR) CollectGcBiasMetrics \
						$(METRICS_COMMON_OPTS) \
						INPUT=$$(<) \
						OUTPUT=metrics/$1.gc_metrics.txt \
						CHART_OUTPUT=metrics/$1.gc_metrics.pdf \
						REFERENCE_SEQUENCE=$$(REF_FASTA) \
						SUMMARY_OUTPUT=$$(@)")

metrics/$1.wgs_metrics.txt : bam/$1.bam
	$$(call RUN, -c -n 1 -s $(WGS_METRICS_SWAP) -m $(WGS_METRICS_MEM) -w $(WGS_METRICS_WALLTIME),"set -o pipefail && \
						$(METRICS_JAVA) -Xmx$(WGS_METRICS_HEAP) -jar $(METRICS_PICARD_JAR) CollectWgsMetrics \
						$(METRICS_COMMON_OPTS) \
						INPUT=$$(<) \
						OUTPUT=$$(@) \
						REFERENCE_SEQUENCE=$$(REF_FASTA)")

metrics/$1.duplicate_metrics.txt : bam/$1.bam
	$$(call RUN, -c -n 1 -s $(DUPLICATE_METRICS_SWAP) -m $(DUPLICATE_METRICS_MEM) -w $(DUPLICATE_METRICS_WALLTIME),"set -o pipefail && \
						$(METRICS_JAVA) -Xmx$(DUPLICATE_METRICS_HEAP) -jar $(METRICS_PICARD_JAR) MarkDuplicates \
						$(METRICS_COMMON_OPTS) \
						INPUT=$$(<) \
						ASSUME_SORT_ORDER=coordinate \
						OUTPUT=/dev/null \
						METRICS_FILE=$$(@)")

endef
$(foreach sample,$(SAMPLES),	$(eval $(call picard-metrics,$(sample))))

summary/idx_metrics.txt : $(foreach sample,$(SAMPLES),metrics/$(sample).idx_stats.txt)
	$(call RUN, -c -n 1 -s 8G -m 12G,"set -o pipefail && \
			  $(RSCRIPT) $(SCRIPTS_DIR)/wgs_metrics.R --option 1 --sample_names '$(SAMPLES)'")

summary/aln_metrics.txt : $(foreach sample,$(SAMPLES),metrics/$(sample).aln_metrics.txt)
	$(call RUN, -c -n 1 -s 8G -m 12G,"set -o pipefail && \
			  $(RSCRIPT) $(SCRIPTS_DIR)/wgs_metrics.R --option 2 --sample_names '$(SAMPLES)'")

summary/insert_metrics.txt : $(foreach sample,$(SAMPLES),metrics/$(sample).insert_metrics.txt)
	$(call RUN, -c -n 1 -s 8G -m 12G,"set -o pipefail && \
			  $(RSCRIPT) $(SCRIPTS_DIR)/wgs_metrics.R --option 3 --sample_names '$(SAMPLES)'")

summary/oxog_metrics.txt : $(foreach sample,$(SAMPLES),metrics/$(sample).oxog_metrics.txt)
	$(call RUN, -c -n 1 -s 8G -m 12G,"set -o pipefail && \
			  $(RSCRIPT) $(SCRIPTS_DIR)/wgs_metrics.R --option 4 --sample_names '$(SAMPLES)'")

summary/gc_metrics.txt : $(foreach sample,$(SAMPLES),metrics/$(sample).gc_metrics_summary.txt)
	$(call RUN, -c -n 1 -s 8G -m 12G,"set -o pipefail && \
			  $(RSCRIPT) $(SCRIPTS_DIR)/wgs_metrics.R --option 5 --sample_names '$(SAMPLES)'")

summary/wgs_metrics.txt : $(foreach sample,$(SAMPLES),metrics/$(sample).wgs_metrics.txt)
	$(call RUN, -c -n 1 -s 8G -m 12G,"set -o pipefail && \
			  $(RSCRIPT) $(SCRIPTS_DIR)/wgs_metrics.R --option 6 --sample_names '$(SAMPLES)'")

summary/duplicate_metrics.txt : $(foreach sample,$(SAMPLES),metrics/$(sample).duplicate_metrics.txt)
	$(call RUN, -c -n 1 -s 8G -m 12G,"set -o pipefail && \
			  $(RSCRIPT) $(SCRIPTS_DIR)/wgs_metrics.R --option 7 --sample_names '$(SAMPLES)'")

.SECONDARY:
.DELETE_ON_ERROR:
.PHONY: wgs_metrics
