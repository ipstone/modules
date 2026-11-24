#!/usr/bin/env python
""" add ups-coordinate to INFO of vcf file
"""

from __future__ import print_function
import argparse
import vcf
import pandas as pd
import sys

try:
    string_types = basestring  # Python 2
except NameError:
    string_types = str  # Python 3

UVCF_COLUMNS = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'UPS-COORDINATE', 'INFO']


def clean(value):
    """ strip a uvcf field; non-string (missing) values become '' """
    if isinstance(value, string_types):
        return value.strip()
    return ''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='merge_uvcf_vcf.py',
                                     description='add ups-coordinate to INFO of vcf file')
    parser.add_argument('uvcf_infile')
    parser.add_argument('vcf_infile')
    args = parser.parse_args()

    vcf_reader = vcf.Reader(open(args.vcf_infile, 'r'))
    # read every column as text with fixed names: the uvcf may have a
    # "CHROM ..." header line, blank fields or ';' comment rows from ups_indel
    uvcf = pd.read_csv(args.uvcf_infile, comment='#', sep='\t', header=None,
                       names=UVCF_COLUMNS, dtype=str, keep_default_na=False)

    vcf_reader.infos['UPS_Coord'] = vcf.parser._Info(id='UPS_Coord', num='.', type='String',
                                                     desc="UPS-coordinate", source=None, version=None)
    vcf_writer = vcf.Writer(sys.stdout, vcf_reader)

    ups_map = {}
    skipped_rows = 0
    for _, row in uvcf.iterrows():
        chrom = clean(row['CHROM'])
        if not chrom or chrom == 'CHROM' or chrom.startswith(';'):
            skipped_rows += 1
            continue
        ups_value = clean(row['UPS-COORDINATE']).replace(" ", "")
        pos = clean(row['POS'])
        ref = clean(row['REF'])
        alt = clean(row['ALT'])
        if not ups_value or not pos or not ref or not alt:
            skipped_rows += 1
            continue
        ups_map['{}:{}_{}/{}'.format(chrom, pos, ref, alt)] = ups_value

    if skipped_rows:
        print('merge_uvcf_vcf.py: skipped {} uvcf rows without a complete UPS coordinate'.format(skipped_rows),
              file=sys.stderr)

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
