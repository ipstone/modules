
** activate isaac's conda environment using jrflab 
    jrflab modules use run.py to submit the cluster jobs :
        it uses -v option to give the conda envionment path.
        Within the script, it calls:a
            source {env}/bin/activate {env}

    in my current conda environments located at:
            /lila/data/riazlab/lib/miniconda3/envs/lumpy/bin
                1. I need to manually copy the activate script into the bin folder,
                2. and then specify the environment as:
                    /data/riazlab/lib/miniconda3/envs/lumpy
        Then the conda environment works fine.
        (it's kind of tweaking the miniconda environment to fit the call
        pattern in jrflab modules)

