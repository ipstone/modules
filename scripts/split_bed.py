#!/usr/bin/env python

import argparse
import math

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='split_bed.py',
                                     description='split a bed file into chunks')
    parser.add_argument('--num_chunks', '-c', type=int, default=100, help='number of chunks')
    parser.add_argument('--out_prefix', '-o', required=True, help='output prefix')
    parser.add_argument('bed_file', help='bed file to split')
    args = parser.parse_args()

    bed = [line for line in open(args.bed_file, 'r')]

    if 0 < len(bed) < args.num_chunks:
        # fewer intervals than chunks (for example a one-chromosome test BED):
        # cut the intervals into num_chunks pieces of about equal length, so
        # that every chunk file the make rules expect is written. Larger
        # BEDs keep the line-based split below unchanged.
        rows = [line.rstrip('\n').split('\t') for line in bed]
        total = sum(int(r[2]) - int(r[1]) for r in rows)
        if total < args.num_chunks:
            raise SystemExit('split_bed.py: {} bp cannot fill {} chunks'.format(total, args.num_chunks))
        size = int(math.ceil(total / float(args.num_chunks)))
        pieces = []
        for r in rows:
            start, end = int(r[1]), int(r[2])
            while start < end:
                stop = min(start + size, end)
                pieces.append([r[0], str(start), str(stop)] + r[3:])
                start = stop
        n = int(math.ceil(len(pieces) / float(args.num_chunks)))
        chunks = [pieces[i:i + n] for i in range(0, len(pieces), n)]
        while len(chunks) < args.num_chunks:
            # split the largest chunk until there are num_chunks
            big = max(range(len(chunks)), key=lambda k: len(chunks[k]))
            c = chunks.pop(big)
            chunks[big:big] = [c[:len(c) // 2], c[len(c) // 2:]]
        for x, c in enumerate(chunks[:args.num_chunks], 1):
            with open(args.out_prefix + '{0:03d}.bed'.format(x), 'w') as f:
                for r in c:
                    f.write('\t'.join(r) + '\n')
        raise SystemExit(0)

    # integer division as in Python 2 keeps the historical chunk boundaries
    n = int(math.ceil(len(bed) // args.num_chunks))
    x = 1
    for i in range(0, len(bed), n):
        f = open(args.out_prefix + '{0:03d}.bed'.format(x), 'w')
        if x == args.num_chunks:
            # last chunk, write everything
            for line in bed[i:]:
                f.write(line)
            f.close()
            break
        else:
            for line in bed[i:i + n]:
                f.write(line)
            f.close()
        x = x + 1
