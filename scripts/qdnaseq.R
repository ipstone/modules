#!/usr/bin/env Rscript

suppressPackageStartupMessages(library("optparse"))
suppressPackageStartupMessages(library("dplyr"))
suppressPackageStartupMessages(library("readr"))
suppressPackageStartupMessages(library("magrittr"))
suppressPackageStartupMessages(library("QDNAseq"))
suppressPackageStartupMessages(library("QDNAseq.hg19"))


if (!interactive()) {
    options(warn = -1, error = quote({ traceback(); q('no', status = 1) }))
}

args_list <- list(make_option("--sample_name", default = NA, type = 'character', help = "sample name"))
parser <- OptionParser(usage = "%prog", option_list = args_list)
arguments <- parse_args(parser, positional_arguments = T)
opt <- arguments$options

bins = getBinAnnotations(binSize = 30)
read_counts = binReadCounts(bins, bamfiles = paste0("../bam/", as.character(opt$sample_name), ".bam"))
read_counts_ft = applyFilters(read_counts, residual = TRUE, blacklist = TRUE)
read_counts_ft = estimateCorrection(read_counts_ft)
copy_number = correctBins(read_counts_ft)
copy_number_nm = normalizeBins(copy_number)
copy_number_sm = smoothOutlierBins(copy_number_nm)
exportBins(copy_number_sm, file = paste0("qdnaseq/", as.character(opt$sample_name), ".txt"))
