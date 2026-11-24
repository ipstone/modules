# vim: set ft=make :
# WGS resource profile: cluster memory (-s soft / -m hard), walltime (-w)
# and thread counts for the steps that need more resources on whole genomes.
# Used when SEQ_TYPE = WGS or SEQ_TYPE is unset (the values this fork used
# before SEQ_TYPE existed). All values are ?= defaults: override any one of
# them in project_config.inc or config.inc.
# *_RESOURCES values are passed to $(call RUN,...) as the resource options.
# The WES/PANEL equivalent is config/profiles/wes.inc (upstream jrflab values).

# aligners/bwamemAligner.mk
BWAMEM_THREADS ?= 12
BWAMEM_MEM_PER_THREAD ?= $(if $(findstring true,$(PDX)),8G,6G)
BWAMEM_RESOURCES ?= -s 6G -m $(BWAMEM_MEM_PER_THREAD)
BWAMEM_SPLIT_RESOURCES ?= -s 4G -m $(BWAMEM_MEM_PER_THREAD) -w 7200

# bam_tools/processBam.mk
BAM_BASE_RECAL_JAVA_MEM ?= 8G
BAM_BASE_RECAL_RESOURCES ?= -s 36G -m 48G -w 8640
BAM_CHR_PRINTREADS_JAVA_MEM ?= 16G
BAM_CHR_REALN_JAVA_MEM ?= 8G
BAM_CHR_REALN_RESOURCES ?= -s 32G -m 32G -w 8640
BAM_CHR_RECAL_JAVA_MEM ?= 8G
BAM_CHR_RECAL_RESOURCES ?= -s 32G -m 48G -w 8640
BAM_FILTER_RESOURCES ?= -s 36G -m 48G -w 8640
BAM_INDEX_RESOURCES ?= -s 36G -m 48G -w 8640
BAM_MARKDUP_JAVA_MEM ?= 15G
BAM_MARKDUP_RESOURCES ?= -s 42G -m 52G -w 8640
BAM_MERGE_CHR_RESOURCES ?= -n 6 -s 10G -m 12G -w 8640
BAM_REALN_TARGET_RESOURCES ?= -s 4G -m 6G -w 8640
BAM_REALN_TARGET_THREADS ?= 8
BAM_RECAL_RESOURCES ?= -s 14G -m 15G -w 8640

# copy_number/facets.mk
FACETS_COMBINE_VARIANTS_RESOURCES ?= -s 18G -m 24G -w 7200
FACETS_CONVERT_BC_RESOURCES ?= -s 18G -m 48G -w 7200
FACETS_GENE_CN_RESOURCES ?= -s 18G -m 48G -w 7200
FACETS_HET_RESOURCES ?= -s 18G -m 24G -w 7200
FACETS_PILEUP_RESOURCES ?= -s 18G -m 48G -w 7200
FACETS_PLOT_GENE_CN_RESOURCES ?= -s 18G -m 48G
FACETS_PLOT_RESOURCES ?= -s 12G -m 48G -w 7200
FACETS_RUN_RESOURCES ?= -s 18G -m 60G -w 7200
FACETS_SUMMARY_RESOURCES ?= -s 18G -m 24G -w 7200

# Makefile.inc (Picard tools)
PICARD_MAX_RECORDS_IN_RAM ?= 8000000
PICARD_MEM ?= 20G

# variant_callers/somatic/lancet.mk
LANCET_FILTER_RESOURCES ?= -s 8G -m 16G
LANCET_MERGE_RESOURCES ?= -s 8G -m 16G
LANCET_RESOURCES ?= -s 4G -m 6G -w 144:00:00
LANCET_THREADS ?= 8

# variant_callers/somatic/mutect.mk
MUTECT_CHR_RESOURCES ?= -s 18G -m 24G -w 7200
MUTECT_JAVA_MEM ?= 16G
MUTECT_MERGE_RESOURCES ?= -s 12G -m 24G -w 7200

# variant_callers/somatic/scalpel.mk
SCALPEL_CHR_RESOURCES ?= -s 8G -m 10G -w 7200
SCALPEL_CHUNK_RESOURCES ?= -s 5G -m 6G -w 7200
SCALPEL_MERGE_RESOURCES ?= -s 16G -m 24G
SCALPEL_THREADS ?= 16

# variant_callers/somatic/strelka.mk
STRELKA_RUN_RESOURCES ?= -s 4G -m 6G -w 7200
STRELKA_SWAP_RESOURCES ?= -s 8G -m 16G -w 7200
