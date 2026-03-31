#!/usr/bin/env Rscript

suppressPackageStartupMessages(library("optparse"))
suppressPackageStartupMessages(library("readr"))
suppressPackageStartupMessages(library("dplyr"))
suppressPackageStartupMessages(library("magrittr"))
suppressPackageStartupMessages(library("fuzzyjoin"))

if (!interactive()) {
    options(warn = -1, error = quote({ traceback(); q('no', status = 1) }))
}

optList = list(make_option("--option", default = NA, type = 'character', help = "analysis type"),
               make_option("--sample_set", default = NA, type = 'character', help = "sample set"),
		       make_option("--tumor_sample", default = NA, type = 'character', help = "tumor sample"),
		       make_option("--normal_sample", default = NA, type = 'character', help = "normal sample"),
		       make_option("--input_file", default = NA, type = 'character', help = "input file"),
		       make_option("--output_file", default = NA, type = 'character', help = "output file"))
parser = OptionParser(usage = "%prog", option_list = optList)
arguments = parse_args(parser, positional_arguments = T)
opt = arguments$options

if (as.numeric(opt$option)==1) {
	sample_set = unlist(strsplit(x = as.character(opt$sample_set), split = " ", fixed=TRUE))
	normal_sample = unlist(strsplit(x = as.character(opt$normal_sample), split = " ", fixed=TRUE))
	sample_set = setdiff(sample_set, normal_sample)
	smry = readr::read_tsv(file = as.character(opt$input_file), col_names = TRUE, col_types = cols(.default = col_character())) %>%
	       readr::type_convert() %>%
	       dplyr::filter(TUMOR_SAMPLE %in% sample_set) %>%
	       dplyr::filter(NORMAL_SAMPLE == normal_sample) %>%
	       dplyr::mutate(UUID = paste0(CHROM, ":", POS, "_", REF, ">", ALT)) %>%
	       dplyr::filter(!duplicated(UUID)) %>%
	       dplyr::mutate(`#CHROM` = CHROM,
			     POS = POS,
			     ID = ".",
			     REF = REF,
			     ALT = ALT,
			     QUAL = 100,
			     FILTER = "PASS",
			     INFO = ".") %>%
	       dplyr::select(`#CHROM`, POS, ID, REF, ALT, QUAL, INFO) %>%
	       dplyr::mutate(`#CHROM` = as.character(`#CHROM`)) %>%
	       dplyr::mutate(chr_n = case_when(
		       `#CHROM` == "X" ~ "23",
		       `#CHROM` == "Y" ~ "24",
		       TRUE ~ `#CHROM`
	       )) %>%
	       readr::type_convert() %>%
	       dplyr::arrange(chr_n) %>%
	       dplyr::select(-chr_n)
	cat("##fileformat=VCFv4.2\n", file = as.character(opt$output_file), append=FALSE)
	readr::write_tsv(x = smry, path = as.character(opt$output_file), append = TRUE, col_names = TRUE)

} else if (as.numeric(opt$option)==2) {
	sample_set = unlist(strsplit(x = as.character(opt$sample_set), split = " ", fixed=TRUE))
	normal_sample = unlist(strsplit(x = as.character(opt$normal_sample), split = " ", fixed=TRUE))
	sample_set = setdiff(sample_set, normal_sample)
	smry = readr::read_tsv(file = as.character(opt$input_file), col_names = TRUE, col_types = cols(.default = col_character())) %>%
	       readr::type_convert() %>%
	       dplyr::filter(TUMOR_SAMPLE %in% sample_set) %>%
	       dplyr::filter(NORMAL_SAMPLE == normal_sample) %>%
	       dplyr::mutate(UUID = paste0(CHROM, ":", POS, "_", REF, ">", ALT)) %>%
	       dplyr::filter(!duplicated(UUID)) %>%
	       dplyr::mutate(`#CHROM` = CHROM,
			     POS = POS,
			     ID = ".",
			     REF = REF,
			     ALT = ALT,
			     QUAL = 100,
			     FILTER = "PASS",
			     INFO = ".") %>%
	       dplyr::select(`#CHROM`, POS, ID, REF, ALT, QUAL, INFO) %>%
	       dplyr::mutate(`#CHROM` = as.character(`#CHROM`)) %>%
	       dplyr::mutate(chr_n = case_when(
		       `#CHROM` == "X" ~ "23",
		       `#CHROM` == "Y" ~ "24",
		       TRUE ~ `#CHROM`
	       )) %>%
	       readr::type_convert() %>%
	       dplyr::arrange(chr_n) %>%
	       dplyr::select(-chr_n)
	cat("##fileformat=VCFv4.2\n", file = as.character(opt$output_file), append=FALSE)
	readr::write_tsv(x = smry, path = as.character(opt$output_file), append = TRUE, col_names = TRUE)

} else if (as.numeric(opt$option)==3) {
	tumor_sample = unlist(strsplit(x = as.character(opt$tumor_sample), split = " ", fixed=TRUE))
	normal_sample = unlist(strsplit(x = as.character(opt$normal_sample), split = " ", fixed=TRUE))
	
	t_maf = readr::read_tsv(file = paste0("sufam/", tumor_sample, ".maf"), comment = "#", col_names = TRUE, col_types = cols(.default = col_character())) %>%
		    readr::type_convert()
	t_gt = readr::read_tsv(file = paste0("sufam/", tumor_sample, ".txt"), col_names = TRUE, col_types = cols(.default = col_character())) %>%
		   readr::type_convert() %>%
		   dplyr::select(CHROM = chrom,
					     POS = pos,
					     REF = val_ref,
					     ALT = val_alt,
					     t_depth = cov,
					     t_alt_count = val_al_count)
	t_cn = readr::read_tsv(file = paste0("facets/cncf/", tumor_sample, "_", normal_sample, ".txt"), col_names = TRUE, col_types = cols(.default = col_character())) %>%
		   dplyr::mutate(chrom = case_when(
							 chrom == "23" ~ "X",
							 TRUE ~ chrom
			)) %>%
			readr::type_convert() %>%
			dplyr::mutate(qt = tcn.em,
					      q2 = tcn.em - lcn.em) %>%
			dplyr::select(Chromosome = chrom,
						  Start_Position = loc.start,
						  End_Position = loc.end,
						  qt, q2)

	n_maf = readr::read_tsv(file = paste0("sufam/", normal_sample, ".maf"), comment = "#", col_names = TRUE, col_types = cols(.default = col_character())) %>%
		    readr::type_convert()
	n_gt = readr::read_tsv(file = paste0("sufam/", normal_sample, ".txt"), col_names = TRUE, col_types = cols(.default = col_character())) %>%
		   readr::type_convert() %>%
		   dplyr::select(CHROM = chrom,
					     POS = pos,
					     REF = val_ref,
					     ALT = val_alt,
					     n_depth = cov,
					     n_alt_count = val_al_count)
					     
	t_maf = t_maf %>%
			dplyr::select(-t_depth, -t_ref_count, -t_alt_count, -n_depth, -n_ref_count, -n_alt_count) %>%
			dplyr::bind_cols(t_gt) %>%
		    dplyr::mutate(t_ref_count = t_depth - t_alt_count) %>%
		    dplyr::mutate(Chromosome = as.character(Chromosome)) %>%
		    dplyr::left_join(n_maf %>%
		    				 dplyr::select(-t_depth, -t_ref_count, -t_alt_count, -n_depth, -n_ref_count, -n_alt_count) %>%
		  					 dplyr::bind_cols(n_gt) %>%
		  					 dplyr::select(Chromosome, Start_Position, End_Position, Reference_Allele, Tumor_Seq_Allele2,
		  					 			   n_depth, n_alt_count) %>%
		  					 dplyr::mutate(Chromosome = as.character(Chromosome)),
		  					 by = c("Chromosome", "Start_Position", "End_Position", "Reference_Allele", "Tumor_Seq_Allele2")) %>%
		  	dplyr::mutate(n_ref_count = n_depth - n_alt_count) %>%
		  	dplyr::mutate(Tumor_Sample_Barcode = tumor_sample,
		  				  Matched_Norm_Sample_Barcode = normal_sample) %>%
		  	dplyr::mutate(Chromosome = as.character(Chromosome)) %>%
	        fuzzyjoin::genome_left_join(t_cn, by = c("Chromosome", "Start_Position", "End_Position")) %>%
	        dplyr::select(-Chromosome.y, -Start_Position.y, -End_Position.y) %>%
	        dplyr::rename(Chromosome = Chromosome.x,
	    				  Start_Position = Start_Position.x,
	    				  End_Position = End_Position.x)
			
	write_tsv(x = t_maf, path = as.character(opt$output_file), append = FALSE, col_names = TRUE)

} else if (as.numeric(opt$option)==4) {
	sample_pairs = unlist(strsplit(x = as.character(opt$sample_set), split = " ", fixed=TRUE))
	maf = list()
	for (i in 1:length(sample_pairs)) {
		maf[[i]] = readr::read_tsv(file = paste0("sufam/", sample_pairs[i], ".ann.maf"), comment = "#", col_names = TRUE, col_types = cols(.default = col_character()))
	}
	maf = do.call(bind_rows, maf) %>%
	      readr::type_convert()
	smry = readr::read_tsv(file = as.character(opt$input_file), col_names = TRUE, col_types = cols(.default = col_character())) %>%
	       dplyr::mutate(HOTSPOT = case_when(
		       is.na(HOTSPOT) ~ FALSE,
		       HOTSPOT == "True" ~ TRUE,
		       HOTSPOT == "False" ~ FALSE,
		       HOTSPOT == "TRUE" ~ TRUE,
		       HOTSPOT == "FALSE" ~ FALSE
	       )) %>%
	       dplyr::mutate(HOTSPOT_INTERNAL = case_when(
		       is.na(HOTSPOT_INTERNAL) ~ FALSE,
		       HOTSPOT_INTERNAL == "True" ~ TRUE,
		       HOTSPOT_INTERNAL == "False" ~ FALSE,
		       HOTSPOT_INTERNAL == "TRUE" ~ TRUE,
		       HOTSPOT_INTERNAL == "FALSE" ~ FALSE
	       )) %>%
	       dplyr::mutate(cmo_hotspot = case_when(
		       is.na(cmo_hotspot) ~ FALSE,
		       cmo_hotspot == "True" ~ TRUE,
		       cmo_hotspot == "False" ~ FALSE,
		       cmo_hotspot == "TRUE" ~ TRUE,
		       cmo_hotspot == "FALSE" ~ FALSE
	       )) %>%
	       dplyr::mutate(is_Hotspot = HOTSPOT | HOTSPOT_INTERNAL | cmo_hotspot) %>%
	       dplyr::mutate(facetsLOHCall = case_when(
		       is.na(facetsLOHCall) ~ FALSE,
		       facetsLOHCall == "True" ~ TRUE,
		       facetsLOHCall == "False" ~ FALSE,
		       facetsLOHCall == "TRUE" ~ TRUE,
		       facetsLOHCall == "FALSE" ~ FALSE
	       )) %>%
	       dplyr::mutate(is_LOH = facetsLOHCall) %>%
	       readr::type_convert()
	maf = maf %>%
	      dplyr::left_join(smry %>%
					       dplyr::group_by(CHROM, POS, REF, ALT) %>%
		       		       dplyr::summarize(is_Hotspot = unique(is_Hotspot)) %>%
					       dplyr::ungroup(),
					       by = c("CHROM", "POS", "REF", "ALT"))
	maf = maf %>%
	      dplyr::left_join(smry %>%
					       dplyr::select(CHROM, POS, REF, ALT, Tumor_Sample_Barcode = TUMOR_SAMPLE, is_LOH) %>%
					       dplyr::mutate(is_present = TRUE),
					       by = c("CHROM", "POS", "REF", "ALT", "Tumor_Sample_Barcode")) %>%
	      dplyr::mutate(is_present = case_when(
						      is.na(is_present) ~ FALSE,
						      TRUE ~ is_present
	      ))
	write_tsv(x = maf, path = as.character(opt$output_file), append = FALSE, col_names = TRUE)

} else if (as.numeric(opt$option)==5) {
	maf = readr::read_tsv(file = as.character(opt$input_file), col_names = TRUE, col_types = cols(.default = col_character())) %>%
	      readr::type_convert() %>%
	      dplyr::filter(is_present)
	write_tsv(x = maf, path = as.character(opt$output_file), append = FALSE, col_names = TRUE)
}
