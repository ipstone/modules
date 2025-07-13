#!/usr/bin/env python

# Use the input files list, to generate the samples.yaml

current_sample = ""
samples_stack = []

with open("fq_filelist.txt") as f:

    for l in f:
        line = l.strip()
        fs = line.split("/")
        # coding sample name
        o_sample = fs[1]
        oss = o_sample.split("_")
        
        sname = oss[0]

        # When encounter a new sample but not the first, output
        if current_sample != "" and sname != current_sample:
            print("- name: " + current_sample)
            tname = current_sample + "-T"
            nname = current_sample + "-N"
            print("  normal: " + nname)
            print("  tumor: [" + tname + "]")
            current_sample = sname

        elif current_sample == "":
            current_sample = sname
    
    # For the last sample print out result
    current_sample = sname
    tname = current_sample + "-T"
    nname = current_sample + "-N"
    print("- name: " + current_sample)
    print("  normal: " + nname)
    print("  tumor: [" + tname + "]")
