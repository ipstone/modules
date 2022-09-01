#!/usr/bin/env python

# Use the input files list, to generate the sample.fastq.yaml

current_sample = ""
samples_stack = []

with open("fq_filelist.txt") as f:

    for l in f:
        line = l.strip()
        fs = line.split("/")
        # coding sample name
        o_sample = fs[1]
        o_sample_file = "rawdata/" + o_sample
        oss = o_sample.split("_")
        n_sample_name = "-".join(oss[0:2])
        # print(n_sample_name)

        # When encounter a new sample but not the first, output
        if current_sample != "" and n_sample_name != current_sample:
            print(current_sample + ":")
            print( "- [" + samples_stack[0] + ",")
            print( "  " + samples_stack[1] + "]")
            samples_stack = [ o_sample_file ]
            current_sample = n_sample_name
        elif current_sample == "":
            samples_stack = [ o_sample_file ]
            current_sample = n_sample_name
        else:
            samples_stack.append(o_sample_file)
    
    # For the last sample print out result
    current_sample = n_sample_name
    print(current_sample + ":")
    print( "- [" + samples_stack[0] + ",")
    print( "  " + samples_stack[1] + "]")

