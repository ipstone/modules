define bam-header
$$(ALIGNER)/sam/$1.header.sam : $$(foreach split,$2,$$(ALIGNER)/bam/$$(split).$$(ALIGNER).sorted.bam)
	$$(INIT) $$(SAMTOOLS) view -H $$< | grep -v '^@RG' > $$@.tmp; \
	for bam in $$^; do $$(SAMTOOLS) view -H $$$$bam | grep '^@RG' >> $$@.tmp; done; \
	uniq $$@.tmp > $$@ && $$(RM) $$@.tmp
endef
$(foreach sample,$(SAMPLES),\
	$(eval $(call bam-header,$(sample),$(split.$(sample)))))

define merged-bam
$$(ALIGNER)/bam/$1.$$(ALIGNER).sorted.bam : $$(ALIGNER)/sam/$1.header.sam $$(foreach split,$2,$$(ALIGNER)/bam/$$(split).$$(ALIGNER).sorted.bam)
	$$(call RUN,-s 12G -m 15G -w 72:00:00,"for bam in $$(filter %.bam,$$^); do \
		$$(SAMTOOLS) quickcheck -v \$$$$bam || { status=\$$$$?; $$(RM) \$$$$bam \$$$$bam.bai \$$$$$${bam%.bam}.bai; exit \$$$$status; }; \
	done; \
	tmp=$$(@).tmp.$$$$$$$$; \
	$$(SAMTOOLS) merge -f -h $$< \$$$$tmp $$(filter %.bam,$$^) && mv \$$$$tmp $$(@) && $$(RM) $$^ || { status=\$$$$?; $$(RM) \$$$$tmp; exit \$$$$status; }")
endef
define rename-bam
$$(ALIGNER)/bam/$1.$$(ALIGNER).bam : $$(ALIGNER)/bam/$2.$$(ALIGNER).bam
	mv $$< $$@
$$(ALIGNER)/bam/$1.$$(ALIGNER).sorted.bam : $$(ALIGNER)/bam/$2.$$(ALIGNER).sorted.bam
	mv $$< $$@
endef
$(foreach sample,$(SAMPLES),\
	$(if $(word 2,$(split.$(sample))),\
	$(eval $(call merged-bam,$(sample),$(split.$(sample)))),\
	$(if $(split.$(sample)),\
	$(eval $(call rename-bam,$(sample),$(split.$(sample)))))))
