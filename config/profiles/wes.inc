# vim: set ft=make :
# WES / PANEL resource profile: cluster memory (-s soft / -m hard), walltime
# (-w) and thread counts. Used when SEQ_TYPE = WES or PANEL. Values are the
# upstream jrflab/modules defaults (git show upstream/master:<file>), which
# are sized for exome and targeted panels. All values are ?= defaults:
# override any one of them in project_config.inc or config.inc.
# *_RESOURCES values are passed to $(call RUN,...) as the resource options.
# The WGS equivalent is config/profiles/wgs.inc.

# aligners/bwamemAligner.mk
BWAMEM_THREADS ?= 8
BWAMEM_MEM_PER_THREAD ?= $(if $(findstring true,$(PDX)),4G,2G)
BWAMEM_RESOURCES ?= -s 1G -m $(BWAMEM_MEM_PER_THREAD)
BWAMEM_SPLIT_RESOURCES ?= -s 1G -m $(BWAMEM_MEM_PER_THREAD)

# bam_tools/processBam.mk
BAM_BASE_RECAL_JAVA_MEM ?= 7G
BAM_BASE_RECAL_RESOURCES ?= -s 15G -m 15G
BAM_CHR_PRINTREADS_JAVA_MEM ?= 8G
BAM_CHR_REALN_JAVA_MEM ?= 4G
BAM_CHR_REALN_RESOURCES ?= -s 16G -m 16G
BAM_CHR_RECAL_JAVA_MEM ?= 6G
BAM_CHR_RECAL_RESOURCES ?= -s 11G -m 15G
BAM_FILTER_RESOURCES ?= -s 6G -m 7G
BAM_INDEX_RESOURCES ?= -s 4G -m 8G
BAM_MARKDUP_JAVA_MEM ?= 10G
BAM_MARKDUP_RESOURCES ?= -s 22G -m 22G
BAM_MERGE_CHR_RESOURCES ?= -n 2 -s 10G -m 11G
BAM_REALN_TARGET_RESOURCES ?= -s 4G -m 4G
BAM_REALN_TARGET_THREADS ?= 4
BAM_RECAL_RESOURCES ?= -s 14G -m 15G

# copy_number/facets.mk
FACETS_COMBINE_VARIANTS_RESOURCES ?= -s 4G -m 6G
FACETS_CONVERT_BC_RESOURCES ?= -s 12G -m 14G
FACETS_GENE_CN_RESOURCES ?= -s 8G -m 30G
FACETS_HET_RESOURCES ?= -s 9G -m 12G
FACETS_PILEUP_RESOURCES ?= -s 8G -m 20G
FACETS_PLOT_GENE_CN_RESOURCES ?= -s 8G -m 10G
FACETS_PLOT_RESOURCES ?= -s 4G -m 6G
FACETS_RUN_RESOURCES ?= -s 8G -m 60G
FACETS_SUMMARY_RESOURCES ?= -s 8G -m 12G

# Makefile.inc (Picard tools)
PICARD_MAX_RECORDS_IN_RAM ?= 4000000
PICARD_MEM ?= 10G

# variant_callers/somatic/lancet.mk
LANCET_FILTER_RESOURCES ?= -s 1G -m 2G
LANCET_MERGE_RESOURCES ?= -s 4G -m 8G
LANCET_RESOURCES ?= -s 2G -m 3G -w 36:00:00
LANCET_THREADS ?= 4

# variant_callers/somatic/mutect.mk
MUTECT_CHR_RESOURCES ?= -s 12G -m 15G
MUTECT_JAVA_MEM ?= 11G
MUTECT_MERGE_RESOURCES ?= -s 4G -m 8G

# variant_callers/somatic/scalpel.mk
SCALPEL_CHR_RESOURCES ?= -s 2G -m 3G
SCALPEL_CHUNK_RESOURCES ?= -s 2G -m 3G
SCALPEL_MERGE_RESOURCES ?= -s 4G -m 8G
SCALPEL_THREADS ?= 4

# variant_callers/somatic/strelka.mk
STRELKA_RUN_RESOURCES ?= -s 1G -m 1.5G
STRELKA_SWAP_RESOURCES ?= -s 1G -m 2G
