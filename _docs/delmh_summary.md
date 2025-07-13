# Name: 
   delmh_summary

# Description
   Caculate:
    - tsv/delmh_found.tsv:    deletion with microhomology
    - tsv/delmh_filtered.tsv:  filter by apropriate deletion caller filter
    - tsv/delmh_summary.tsv:   sample level summary of deleltions/mh
                                (focusing on del-len>=4, mh-len>=3 for now)

# Input
    tsv/all.somatic_indels.tsv

    Required fields for input:
          - "SAMPLE.TUMOR", "SAMPLE.NORMAL", "variantCaller" (TODO: optional, refactor code to loosen these requirements )
          - 'CHROM', 'POS', 'REF', 'ALT' (required for detail calculation) 

    The convention for the indel postion is 1 based, eg:
      $ CHROM                 : chr  "1" "1" "1" "1" ... (X, Y etc.)
      $ POS                   : int  821023 1130880 1501479 1773873 
      $ REF                   : chr  "TAA" "CT" "TA" "CA" ...
      $ ALT                   : chr  "T" "C" "T" "C" ...


# Output
```
    - tsv/delmh_found.tsv:    deletion with microhomology
    - tsv/delmh_filtered.tsv:  filter by apropriate deletion caller filter
    - tsv/delmh_summary.tsv:   sample level summary of deleltions/mh
                                (focusing on del-len>=4, mh-len>=3 for now)
```

# Error
  1. This targets need to be submitted on head node; submitting from
  cluster node can result in some temp file not read errors etc.

  2. all.somatic_indels.tsv has different headers than the
     mutation_summary:
        in all.somatic_indels.tsv:
            - SAMPLE.TUMOR => corresponds to TUMOR_SAMPLE
            - SAMPLE.NORMAL =>      .........NORMAL_SAMPLE
     These fields names may need to be recoded before using
     mutation_summary as input.

# Examples
    `make delmh_summary`  # This will generate all 3 output 
