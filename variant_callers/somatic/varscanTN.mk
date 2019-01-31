# Run VarScan on tumour-normal matched pairs
# Detect point mutations
##### DEFAULTS ######

LOGDIR ?= log/varscanTN.$(NOW)

##### MAKE INCLUDES #####
include modules/Makefile.inc

IGNORE_FP_FILTER ?= true

FP_FILTER = $(PERL) $(HOME)/share/usr/bin/fpfilter.pl
BAM_READCOUNT = $(HOME)/share/usr/bin/bam-readcount

VARSCAN_TO_VCF = $(PERL) modules/variant_callers/somatic/varscanTNtoVcf.pl

MIN_MAP_QUAL ?= 1
VALIDATION ?= false
MIN_VAR_FREQ ?= $(if $(findstring false,$(VALIDATION)),0.05,0.000001)

#VARSCAN
VARSCAN_MEM = $(JAVA7) -Xmx$1 -jar $(VARSCAN_JAR)
VARSCAN = $(call VARSCAN_MEM,12G)
VARSCAN_OPTS = $(if $(findstring true,$(VALIDATION)),--validation 1 --strand-filter 0) --min-var-freq $(MIN_VAR_FREQ)

VARSCAN_SOURCE_ANN_VCF = python modules/vcf_tools/annotate_source_vcf.py --source varscan

VPATH ?= bam

VARSCAN_VARIANT_TYPES = varscan_indels varscan_snps

PHONY += varscan varscan_vcfs varscan_mafs
varscan : varscan_vcfs #varscan_mafs
varscan_vcfs : $(foreach type,$(VARSCAN_VARIANT_TYPES),$(foreach pair,$(SAMPLE_PAIRS),vcf/$(pair).$(type).vcf))
varscan_mafs : $(foreach type,$(VARSCAN_VARIANT_TYPES),$(foreach pair,$(SAMPLE_PAIRS),maf/$(pair).$(type).maf))


%.Somatic.txt : %.txt
	$(call RUN,-s 5G -m 8G,"$(call VARSCAN_MEM,8G) somaticFilter $< && $(call VARSCAN_MEM,8G) processSomatic $< && rename .txt.Somatic .Somatic.txt $** && rename .txt.Germline .Germline.txt $** && rename .txt.LOH .LOH.txt $** && rename .txt.hc .hc.txt $**")

define varscan-somatic-tumor-normal-chr
varscan/chr_tables/$1_$2.$3.varscan_timestamp : bam/$1.bam bam/$2.bam bam/$1.bam.bai bam/$2.bam.bai
	if [[ $$$$($$(SAMTOOLS) view $$< $3 | head -1 | wc -l) -gt 0 ]]; then \
		$$(call RUN,-s 12G -m 16G -w 7200,"$$(VARSCAN) somatic \
		<($$(SAMTOOLS) mpileup -A -r $3 -q $$(MIN_MAP_QUAL) -f $$(REF_FASTA) $$(word 2,$$^)) \
		<($$(SAMTOOLS) mpileup -A -r $3 -q $$(MIN_MAP_QUAL) -f $$(REF_FASTA) $$<) \
		$$(VARSCAN_OPTS) \
		--output-indel varscan/chr_tables/$1_$2.$3.indel.txt --output-snp varscan/chr_tables/$1_$2.$3.snp.txt && touch $$@"); \
	else \
		$$(INIT) \
		echo 'chrom	position	ref	var	normal_reads1	normal_reads2	normal_var_freq	normal_gt	tumor_reads1	tumor_reads2	tumor_var_freq	tumor_gt	somatic_status	variant_p_value	somatic_p_value	tumor_reads1_plus	tumor_reads1_minus	tumor_reads2_plus	tumor_reads2_minus	normal_reads1_plus	normal_reads1_minus	normal_reads2_plus	normal_reads2_minus' > varscan/chr_tables/$1_$2.$3.indel.txt; \
		echo 'chrom	position	ref	var	normal_reads1	normal_reads2	normal_var_freq	normal_gt	tumor_reads1	tumor_reads2	tumor_var_freq	tumor_gt	somatic_status	variant_p_value	somatic_p_value	tumor_reads1_plus	tumor_reads1_minus	tumor_reads2_plus	tumor_reads2_minus	normal_reads1_plus	normal_reads1_minus	normal_reads2_plus	normal_reads2_minus' > varscan/chr_tables/$1_$2.$3.snp.txt; \
		touch $$@; \
	fi

varscan/chr_tables/$1_$2.$3.indel.txt : varscan/chr_tables/$1_$2.$3.varscan_timestamp
varscan/chr_tables/$1_$2.$3.snp.txt : varscan/chr_tables/$1_$2.$3.varscan_timestamp

varscan/chr_tables/$1_$2.$3.%.fp_pass.txt : varscan/chr_tables/$1_$2.$3.%.txt bamrc/$1.$3.bamrc.gz
	$$(call RUN,-s 8G -m 55G -w 7200,"$$(VARSCAN) fpfilter $$< <(zcat $$(<<)) --output-file $$@")
endef
$(foreach chr,$(CHROMOSOMES), \
	$(foreach pair,$(SAMPLE_PAIRS), \
	$(eval $(call varscan-somatic-tumor-normal-chr,$(tumor.$(pair)),$(normal.$(pair)),$(chr)))))

define merge-varscan-pair-type
varscan/tables/$1.$2.txt : $$(foreach chr,$$(CHROMOSOMES),\
	$$(if $$(findstring true,$$(VALIDATION) $$(IGNORE_FP_FILTER)),\
	varscan/chr_tables/$1.$$(chr).$2.txt,\
	varscan/chr_tables/$1.$$(chr).$2.fp_pass.txt))
	$$(INIT) head -1 $$< > $$@ && for x in $$^; do sed 1d $$$$x >> $$@; done
endef
$(foreach pair,$(SAMPLE_PAIRS), \
	$(foreach type,snp indel,$(eval $(call merge-varscan-pair-type,$(pair),$(type)))))

define convert-varscan-tumor-normal
varscan/vcf/$1_$2.%.vcf : varscan/tables/$1_$2.%.txt
	$$(call RUN,-s 12G -m 16G -w 7200,"$$(VARSCAN_TO_VCF) -f $$(REF_FASTA) -t $1 -n $2 $$< | $$(VCF_SORT) $$(REF_DICT) - > $$@")
endef
$(foreach pair,$(SAMPLE_PAIRS), \
	$(eval $(call convert-varscan-tumor-normal,$(tumor.$(pair)),$(normal.$(pair)))))

vcf/%.varscan_indels.vcf : varscan/vcf/%.indel.Somatic.vcf
	$(INIT) $(VARSCAN_SOURCE_ANN_VCF) < $< > $@

vcf/%.varscan_snps.vcf : varscan/vcf/%.snp.Somatic.vcf
	$(INIT) $(VARSCAN_SOURCE_ANN_VCF) < $< > $@

define bamrc-chr
bamrc/%.$1.bamrc.gz : bam/%.bam
	$$(call RUN,-s 8G -m 12G,"$$(BAM_READCOUNT) -f $$(REF_FASTA) $$< $1 | gzip > $$@ 2> /dev/null")
endef
$(foreach chr,$(CHROMOSOMES),$(eval $(call bamrc-chr,$(chr))))

include modules/variant_callers/gatk.mk

.DELETE_ON_ERROR:
.SECONDARY: 
.PHONY: $(PHONY)

