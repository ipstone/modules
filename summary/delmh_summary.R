## Summary for delmh calculated & filtered calc_delmh.py output:
##         tsv/all.delmh_filtered.tsv
##              (filtered from tsv/all.delmh_found.tsv)
##   The output is stored at: summary/delmh_summary.tsv
#
## Output fields Definition
#  $ del_count             : int  Total deletion counts (after filtering)
#  $ avg_delen             : num  Average/mean deletion length
#  $ median_delen          : num  Median deletion length
#  $ deln4_count           : int  Counts of deletions with 4 nucleotide or more
#  $ deln4_mhlen_3_counts  : num  Counts of del-len>=4, and mh>=3
#  $ deln4_mhlen_3_avg_deln: num  Same deleteion as the line above - average len
#  $ delmh_prop            : num  Proportion of deln4_mhlen3/total-deletion count
#  $ delmh_deln4_prop      : num  Proportions over del-len>=4 count

library(data.table)
rm(list = ls())

count_deln_with_microh_len <- function(df, cutoff, mhlen, final) {
    ## helper function to count deletions:
    ##   w. del-length >=cutoff, and microhomology-length >=mhlen
    count <- df[(deletion_length >= cutoff) & (mh_length >= mhlen), .N,
        by = SAMPLE.TUMOR
    ]
    fieldname <- paste("deln", cutoff, "_mhlen_", mhlen, "_counts", sep = "")
    count[[fieldname]] <- count$N
    count$N <- NULL

    ## Calculate the average deletion length for the critera
    avg_deln <- df[(deletion_length >= cutoff) & (mh_length >= mhlen),
        .(avg_delen = mean(deletion_length)),
        by = SAMPLE.TUMOR
    ]
    fieldname2 <- paste("deln", cutoff, "_mhlen_",
        mhlen, "_avg_deln",
        sep = ""
    )
    avg_deln[[fieldname2]] <- avg_deln$avg_delen
    avg_deln$avg_delen <- NULL

    # Merge the calculated counts and average deletion length with mh
    merge_count <- merge(final, count, by = "SAMPLE.TUMOR", all.x = TRUE)
    merge_count <- merge(merge_count, avg_deln, by = "SAMPLE.TUMOR", all.x = TRUE)
    merge_count[[fieldname]][is.na(merge_count[[fieldname]])] <- 0
    return(merge_count)
}

get_deln_with_microh <- function(del_count, mh) {
    ## helper function to call functions to calculate with different parameters
    del_mh_collections <- del_count
    # This function can be tweaked to add additional definitions of delmh, such as:
    #   For each of the del length of 3-10
    #   count microhomologies of 1+, 2+, 3+, 4+
    #   Actually for the moment only interested in del4 or more, and mh 3+
    for (del in c(4)) {
        for (mht in c(3)) {
            del_mh_collections <- count_deln_with_microh_len(
                mh, del, mht,
                del_mh_collections
            )
        }
    }
    return(del_mh_collections)
}

calc_delmh_summary <- function(input = "tsv/all.delmh_found.tsv") {
    ## Main function to calculate delmh_summary
    # Summary deletion, and delmh related metrics per SAMPLE.TUMOR
    mh <- fread(input, na = "") # na option here is just from previous code

    ## For microhomogy to start: explore the total length of microhomogy (not distinguish up/down)
    mh$up_mh_len <- ifelse(is.na(mh$up_mh), 0, nchar(mh$up_mh))
    mh$down_mh_len <- ifelse(is.na(mh$down_mh), 0, nchar(mh$down_mh))
    mh$mh_length <- pmax(mh$up_mh_len, mh$down_mh_len)
    mh[, deletion_length := .(end_position - start_position + 1)]

    # Calculate the generate deletion counts, average/mean deletion length
    # Input is the deletion call results - mh
    avg_del <- mh[, .(avg_delen = mean(deletion_length)), by = SAMPLE.TUMOR]
    median_del <- mh[, .(median_delen = median(deletion_length)), by = SAMPLE.TUMOR]
    del_count <- mh[, .N, by = SAMPLE.TUMOR]
    del_count$del_count <- del_count$N
    del_count$N <- NULL
    del_summary <- merge(del_count, avg_del, by = "SAMPLE.TUMOR")
    del_summary <- merge(del_summary, median_del, by = "SAMPLE.TUMOR")

    # Adding the counts for deletion-length>=4 per sample
    deln4_count <- mh[deletion_length >= 4, .N, by = SAMPLE.TUMOR]
    deln4_count$deln4_count <- deln4_count$N
    deln4_count$N <- NULL
    del_summary <- merge(del_summary, deln4_count, by = "SAMPLE.TUMOR")

    ## Calculate all different mutation counts and save
    delmh_summary <- get_deln_with_microh(del_summary, mh)
    delmh_summary$delmh_prop <- delmh_summary$deln4_mhlen_3_counts / delmh_summary$del_count
    delmh_summary$delmh_deln4_prop <- delmh_summary$deln4_mhlen_3_counts / delmh_summary$deln4_count
    return(delmh_summary)
}

# delmh_summary = calc_delmh_summary(input="tsv/all.delmh_found.tsv")
delmh_summary <- calc_delmh_summary(input = "tsv/delmh_filtered.tsv")
fwrite(delmh_summary, "tsv/delmh_summary.tsv", sep = "\t", na = "")
