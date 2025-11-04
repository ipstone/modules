#!/usr/bin/env python
""" add ups-coordinate to INFO of vcf file
"""

from __future__ import print_function
import argparse
import vcf
import pandas as pd
import sys
import copy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='merge_uvcf_vcf.py',
                                     description='add ups-coordinate to INFO of vcf file')
    parser.add_argument('uvcf_infile')
    parser.add_argument('vcf_infile')
    args = parser.parse_args()

    vcf_reader = vcf.Reader(open(args.vcf_infile, 'r'))
    columns = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'UPS-COORDINATE', 'INFO']
    uvcf = pd.read_csv(args.uvcf_infile, comment='#', sep='\t',
                       header=None, names=columns, dtype=str, keep_default_na=False)

    vcf_reader.infos['UPS_Coord'] = vcf.parser._Info(id='UPS_Coord', num='.', type='String',
                                                     desc="UPS-coordinate", source=None, version=None)
    vcf_writer = vcf.Writer(sys.stdout, vcf_reader)

    ups_map = {}
    skipped_rows = 0
    for _, row in uvcf.iterrows():
        chrom = row['CHROM'].strip() if isinstance(row['CHROM'], str) else ''
        if not chrom or chrom.startswith(';'):
            skipped_rows += 1
            continue
        ups_value = row['UPS-COORDINATE'].replace(" ", "") if isinstance(row['UPS-COORDINATE'], str) else ''
        if not ups_value:
            skipped_rows += 1
            continue
        pos = row['POS'].strip() if isinstance(row['POS'], str) else str(row['POS'])
        ref = row['REF'].strip() if isinstance(row['REF'], str) else str(row['REF'])
        alt = row['ALT'].strip() if isinstance(row['ALT'], str) else str(row['ALT'])
        if not pos or not ref or not alt:
            skipped_rows += 1
            continue
        key = '{}:{}_{}/{}'.format(chrom, pos, ref, alt)
        ups_map[key] = ups_value

    if skipped_rows:
        print('# merge_uvcf_vcf.py skipped {} rows without UPS coordinates'.format(skipped_rows), file=sys.stderr)

    for record in vcf_reader:
        ups_coords = []
        for alt in record.ALT:
            alt = str(alt)
            key = '{}:{}_{}/{}'.format(record.CHROM, record.POS, record.REF, alt)
            if key in ups_map:
                ups_coords.append(ups_map[key])
            else:
                ups_coords.append('N/A[]')
        record.INFO['UPS_Coord'] = ups_coords
        vcf_writer.write_record(record)
    vcf_writer.close()
