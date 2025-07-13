#!/usr/bin/env python

# Calculate the homopolymer lenght for 1 bd indels from tsv/all.somatic_indels.tsv
#   Input: tsv/all.somatic_indels.tsv
#   Output: tsv/indel_homopolymer_count.tsv
# -- Note:
    # Deletion is easy - use the deleted nucleotides to check
    # Insertion is complex - to calculate homopolyer seq before insertion

import os, argparse
import numpy as np
import pandas as pd
from Bio import SeqIO

def calc_homopolyer(seq, change_base, start, end):
    # Return the homopolymer length of change_base, start/end -/+4 bps
    # seq is the ref dict object pointing to the chromosome
    count_up = 0
    count_down = 0
    seq_len = len(seq) # the length of the chromosome

    # count homopolymer upstream
    for i in range(5):
        left_index = start - i - 1 # python left index
        if (left_index<0 or seq[left_index] != change_base):
            break
        else:
            count_up += 1

    # count homopolymer downstream
    for i in range(5):
        right_index = end + i - 1 # python left index
        if (right_index>= seq_len or seq[right_index] != change_base):
            break
        else:
            count_down += 1

    total_count = count_up + count_down
    return(total_count)

def get_homopolymer_table(indel_table, ref_dict):
    # Return the homopolymer table merged with indel table
    select_cols = ["SAMPLE.TUMOR", "SAMPLE.NORMAL", "variantCaller",
    'CHROM', 'POS', 'REF', 'ALT', 'start_position', 'end_position']

    indel_table['homopolymer_count'] = indel_table.apply(lambda row: calc_homopolyer(
                   ref_dict[row['CHROM']],
                   row['change_base'],
                   row['start_position'], 
                   row['end_position']), axis=1)

    # For deletions, the homopolyer_count + 1 as counting for the deleted bp
    indel_table["homopolymer_count"] = np.where(
        indel_table.indel_length==-1, 
        indel_table.homopolymer_count+1, 
        indel_table.homopolymer_count)

    return(indel_table)

def main():
    parser = argparse.ArgumentParser(description='Calculate homopolymer length for 1bp indel (insertion or deletion).')
    parser.add_argument('--ref-fasta', help='Path to reference genome .fasta. Must be specified, no default.')
    args = parser.parse_args()
    ref_dict = SeqIO.to_dict(SeqIO.parse(args.ref_fasta, 'fasta')) 

    # Load, process del, and output
    indel_table = pd.read_table("tsv/all.somatic_indels.tsv", low_memory=False, comment='#')
    indel_table['CHROM'] = indel_table.CHROM.apply(str)
    indel_table["indel_length"] =  indel_table.ALT.apply(len) - indel_table.REF.apply(len) 
    # Keep only insertion or deletion of length 1bp
    indel_table = indel_table[ abs(indel_table.indel_length) == 1  ]

    # start_position is where the counts start for up-stream sequence
    indel_table["start_position"] = np.where(indel_table.indel_length==-1, indel_table.POS-1, indel_table.POS)

    # end_position is the starting pos for down-stream sequence
    indel_table["end_position"] = indel_table.POS + 1

    # change_base: if deletion:deleted, if insertion inserted
    indel_table["change_base"] = np.where(indel_table.indel_length==-1, indel_table.REF.str[-1], indel_table.ALT.str[-1] )

    final = get_homopolymer_table(indel_table, ref_dict)
    final.to_csv("tsv/indel_homopolymer_count.tsv", index=False, sep='\t')
    return(final)

    # dm_out = find_mh_t2t(indel_table, ref_dict)
    # dm_out.to_csv("tsv/delmh_found.tsv", index=False, sep='\t')
#

if __name__ == '__main__':
    a=main()




