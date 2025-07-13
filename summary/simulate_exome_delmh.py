#!/usr/bin/env python

# Calculate deletion with microhomogoy from tsv/all.somatic_indels.tsv
#   Input: tsv/all.somatic_indels.tsv
#   Output: tsv/all.delmh_found.tsv
import os, argparse
import numpy as np
import pandas as pd
from Bio import SeqIO

def find_mh_1d(direction, seq, start_coord, end_coord, coord2pyidx = -1): 
    """arguments: 
        seq - is the chromosome seq object
        start_coord: pos of the first deleted nt (1 indexed)
        end_coord: pos of the last deleted nt (1 indexed)
        as python is 0 indexed, conversion would be:
               python_index = coord - 1; coord = python_index + 1
    """
    if direction == 'up':
        step = -1
        offset = 0
    elif direction == 'down':
        step = 1
        offset = 1
    else:
        raise Exception('`direction` must be either \'up\' or \'down\'.')
    
    mh = ''
    left_idx = init_left_idx = int(start_coord) + coord2pyidx - 1 + offset # numpy.int64 is "Invalid index"
    right_idx = init_right_idx = int(end_coord) + coord2pyidx + offset
    while (
            left_idx >= 0 and right_idx < len(seq) # search within the bounds of reference sequence
        and 
            abs(left_idx - init_left_idx) <= end_coord - start_coord # one member of homology is within the deletion region
        and 
            seq[left_idx] == seq[right_idx] # homology detected
        ):
        mh += seq[left_idx]
        left_idx += step
        right_idx += step
    if left_idx == init_left_idx:
        found = False
        left_coords = right_coords = []
    else:
        found = True
        coords = [idx - coord2pyidx for idx in [init_left_idx, left_idx - step, init_right_idx, right_idx - step]]
        left_coords = coords[:2]
        right_coords = coords[2:]
        if direction == 'up':
            mh = mh[::-1]
            left_coords = left_coords[::-1]
            right_coords = right_coords[::-1]
    
    return {'found': found, 'mh': mh, 'left_coords': left_coords, 'right_coords': right_coords}
#

def find_mh_2d(seq, start_coord, end_coord, out_type='dict'):
    # idx is python style
    directions = ['up', 'down']
   
    # mh_dict is from find_mh_1d (including both up/down, all combined as rows)
    mh_dict = {direc: find_mh_1d(direc, seq, start_coord, end_coord) for direc in directions}

    # mh_srs is calculating up/down, adding results as columns
    mh_list = []
    for direc in directions:
        mh_dict_direc = mh_dict[direc]
        mh_srs_dict_direc = {key: mh_dict_direc[key] for key in ['found', 'mh']}
        for position in ['left', 'right']:
            coords = mh_dict_direc[position + '_coords']
            if len(coords) == 0:
                coords = [np.nan] * 2
            pos_dict = {position + '_start': coords[0], position + '_end': coords[1]}
            mh_srs_dict_direc.update(pos_dict)
        mh_srs_direc = pd.Series(mh_srs_dict_direc)
        mh_srs_direc.index = ['_'.join([direc, idx]) for idx in mh_srs_direc.index]
        mh_list.append(mh_srs_direc)

    mh_srs = pd.concat(mh_list, axis=0) # srs is for both directions
    
    if out_type == 'dict': # result as multple rows
        return mh_dict
    elif out_type == 'srs': # up/down result as multiple columns
        return mh_srs
    else:
        raise Exception('`out_type` must be either \'dict\' or \'srs\'.')
#

def find_mh_t2t(del_table, ref_dict): # from input table to output table
    select_cols = ['CHROM', 'start_position', 'end_position']

    del_mh = del_table.apply(lambda row: find_mh_2d(
                   ref_dict[row['CHROM']],
                   row['start_position'], 
                   row['end_position'], out_type='srs'), axis=1)
    return pd.concat([del_table[select_cols], del_mh], axis=1)
#

def gen_sliding_deletion(chromosome, start, end, del_len):
    # Giving the input positions, return a sliding deletion file containing deletions at every position with del_len 

    # Output: Generating a deletion table for every position : CHROM, start_position, end_position
    if (end-start+1)<4 :
        return(None)
    start_range=range(start, end-4+1)
    deletion_table = pd.DataFrame({'CHROM': chromosome, 
                                   'start_position':range(start, end-4+1),
                                   'end_position': range(start+4, end+1) })
    return(deletion_table)
#


def main():
    parser = argparse.ArgumentParser(description='Calculate microhomology.')
    parser.add_argument('--ref-fasta', help='Path to reference genome .fasta. Must be specified, no default.')
    args = parser.parse_args()
    ref_dict = SeqIO.to_dict(SeqIO.parse(args.ref_fasta, 'fasta')) 

    # Loading the sureselect exome bed regions
    exome_region=pd.read_table('sure_select_exome_v4_b37.bed_dataframe', dtype={'chr':str})
    chr1 = exome_region[ exome_region.chr =='1' ] # limiting to chromosome1
    # the bed contains these relevant fields:
    #         (['chr', 'start', 'end', 'feat', 'pos', 'strand', 'len'], dtype='object')


    # Looping through each deletion bed regions
    result = pd.concat([ find_mh_t2t(del_table, ref_dict) 
                            for del_table in
                                chr1.apply(lambda x: 
                                    gen_sliding_deletion(x.chr, x.start, x.end), axis=1) if del_table != None ])

    result.to_csv("simulation_exome_delmh_found.tsv", index=False, sep='\t')

    # previous delmh calculation - Load, process del, and output
        # del_table = pd.read_table("tsv/all.somatic_indels.tsv", low_memory=False, comment='#')
        # dm_out = find_mh_t2t(del_table, ref_dict)
        # dm_out.to_csv("tsv/simulation_exome_delmh_found.tsv", index=False, sep='\t')

#

if __name__ == '__main__':
    main()




