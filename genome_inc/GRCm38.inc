# vim: set ft=make:
ifndef GRCM38_INC
# Mouse GRCm38 (mm10), Ensembl release 71 FASTA. Contig names have no "chr"
# prefix (1..19, X, Y, MT); the MGP dbSNP VCFs, the svaba region BED and the
# FACETS gene BED below use the same names. Paths checked on lilac 2026-11-24.
REF = GRCm38
SPECIES = mouse
TOPHAT_REF = GRCm38
REF_DIR = $(HOME)/share/reference

INTEGRATE_ANN = $(REF_DIR)/mm10_annot.ucsc.txt
INTEGRATE_BWTS =$(REF_DIR)/Mus_musculus_GRCm38/bwts

GENES_GTF = $(REF_DIR)/Mus_musculus/NCBI/$(TOPHAT_REF)/Annotation/Genes/genes.gtf

REF_FASTA ?= $(REF_DIR)/Mus_musculus_GRCm38/Mus_musculus.GRCm38.71.dna.chromosome.genome.fa
REF_DICT ?= $(REF_DIR)/Mus_musculus_GRCm38/Mus_musculus.GRCm38.71.dna.chromosome.genome.dict
SNP_EFF_GENOME = GRCm38.86 # == mm10
DBSNP ?= $(REF_DIR)/mgp.v5.merged.snps_all.dbSNP142.vcf.gz
MGP_SNP_DBSNP := $(DBSNP)
MGP_INDEL_DBSNP := $(REF_DIR)/mgp.v5.merged.indels.dbSNP142.normed.vcf.gz
# known indels for GATK IndelRealigner (bam_tools/processBam.mk)
KNOWN_INDELS ?= $(MGP_INDEL_DBSNP)

# written to the pindel VCF header only (-R / -d of pindel2vcf)
REF_NAME := GRCm38
# GRCm38 assembly date (GCA_000001635.2); not verified against NCBI
REF_DATE := 20120109

# UCSC gap table (chr-prefixed, like the human centromere.txt)
CENTROMERE_TABLE = $(REF_DIR)/centromere_mm10.txt

# FACETS gene-level copy number: mm10 gene BED (chrom start end hgnc band),
# from the mouse_wgs branch facetsGeneCN.R default
FACETS_GENE_ANNOT ?= /data/riazlab/reference/mm10_genes/output_mm10_known_gene.bed

# svaba (sv_callers/svaba_tumor_normal.mk, svabaTN.mk)
# SVABA_DBSNP: MGP v5 indels (uncompressed VCF, as svaba -D needs)
SVABA_DBSNP ?= /data/riazlab/lib/reference/dbsnp/mouse/mgp.v5.merged.indels.dbSNP142.normed.vcf
# region-INCLUSION BED for -k (genome minus blacklisted/gap regions), no chr
SVABA_BLACKLIST ?= /data/riazlab/lib/reference/svaba/mouse_mm10_removed_blacklist-regon_no-chr.bed
SVABA_REGION ?= $(SVABA_BLACKLIST)

# contamination/clusterSamples.mk needs a BED of common SNP sites.
# TODO: no mouse SNP-site BED exists on lilac (checked 2026-11-24). The
# mouse_wgs branch used the exon BED here, which is not a SNP-site file.
# Build one from MGP_SNP_DBSNP (for example, biallelic PASS SNPs in
# EXOME_BED_NOHEADER) and set DBSNP_SUBSET in the project config.
DBSNP_SUBSET ?=

# summary/delmh_summary.mk: BSgenome package for the reference sequence.
# Not installed in jrflab-modules-0.1.4 on lilac (checked 2026-11-24).
DELMH_BSGENOME ?= BSgenome.Mmusculus.UCSC.mm10

# no mouse hotspot VCFs: hotspot genotyping and hotspot summary tables are off
NO_HOTSPOTS ?= true

EXOME_BED ?= $(REF_DIR)/mus_musculus_known_genes_exons_GRCm38.bed
EXOME_BED_NOHEADER ?= $(REF_DIR)/mus_musculus_known_genes_exons_GRCm38_noheader.bed

FREEC_REF := $(REF_DIR)/Mus_musculus_GRCm38/freec
CHR_LEN = $(REF_DIR)/Mus_musculus_GRCm38/mm10.len

BOWTIE_REF = $(REF_DIR)/Mus_musculus_GRCm38/Mus_musculus.GRCm38.71.dna.chromosome.genome

ENSEMBL_TXDB = $(REF_DIR)/mus_musculus_ensembl_biomart.2014-04-28.sqlite

#TXDB = $(HOME)/ensmusg70.08032013.sqlite

RIBOSOMAL_INTERVALS = $(REF_DIR)/mm10_rrna_intervals.txt
GENE_REF_FLAT = $(REF_DIR)/mm10_genes.refFlat.txt

EXOME ?= false
ifeq ($(EXOME),true)
TARGETS_FILE = $(EXOME_BED_NOHEADER)
QUALIMAP_TARGETS_FILE = $(TARGETS_FILE)
endif

INCLUDE_CHR_Y ?= true
ifneq ($(and $(TARGETS_FILE),$(findstring false,$(EXOME))),)
CHROMOSOMES := $(shell grep -v '@' $(TARGETS_FILE) | cut -f1 | sort | uniq)
else
CHROMOSOMES := $(shell seq 1 19) X $(if $(findstring true,$(INCLUDE_CHR_Y)),Y) MT
endif


endif
GRCM38_INC = true
