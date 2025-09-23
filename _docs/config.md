# Name:
   config

# Description
   The `make config` target runs `modules/scripts/configure.py` to convert project
   YAML files into a Make include (`project_config.inc`).  That include is loaded
   by `modules/Makefile.inc` and provides sample lists, sample set mappings, and
   project-wide options that the pipeline requires before any analysis targets
   can be executed.

# Prerequisites
   * Python with the `pyyaml` package available (the site default Python or the
     `enable.conda` miniconda environment both satisfy this requirement).
   * Current working directory should contain the YAML inputs described below.
   * Optional: set up your preferred Python environment first, e.g. `enable.conda`
     or your lab-specific module.  This ensures `configure.py` can import PyYAML
     and that any virtualenv-specific paths resolve correctly.

# Input
   By default `configure.py` reads the following files from the repository root:

   * `project_config.yaml` – top-level project switches (e.g. `USE_CLUSTER`,
     reference assembly, pipeline flags).
   * `samples.yaml` – list of tumor/normal samples with pairing information.
   * `sample_attr.yaml` – optional per-sample attributes exported as Make
     variables.
   * `sample.fastq.yaml` – maps logical samples to FASTQ paths and split chunk
     identifiers.
   * `sample_merge.yaml` – optional merge groups for BAM consolidation.

   You can override any of these locations by running the script manually, e.g.:

   ```bash
   ./modules/scripts/configure.py \
     --project_config_file custom/project.yaml \
     --samples_file metadata/samples.yaml \
     --sample_attr_file metadata/sample_attr.yaml \
     --sample_fastq_file metadata/sample.fastq.yaml \
     --sample_merge_file metadata/sample_merge.yaml \
     --out_file project_config.inc
   ```

# Output
```
   project_config.inc   # Make include consumed by modules/Makefile.inc
```
   The include defines variables such as `SAMPLES`, `SAMPLE_PAIRS`, `tumor.<pair>`,
   `normal.<pair>`, split sample mappings, and any project-level flags.  Once this
   file exists, subsequent `make` targets automatically pick up the configuration.

# Behaviour Notes
   * Entries in `samples.yaml` with a `normal` key are paired with each `tumor`
     entry to produce `SAMPLE_PAIRS` and helper variables like
     `tumor.<tumor>_<normal>` and `normal.<tumor>_<normal>`.
   * `sample.fastq.yaml` is used to emit `split.*` variables so the aligner
     makefiles can iterate over chunked FASTQs.
   * `sample_merge.yaml` populates `merge.<sample>` lists consumed by
     `bam_tools/merge_bam.mk`.
   * Any key/value pairs from `sample_attr.yaml` are flattened into `attr.sample`
     style Make variables for downstream rules.

# Usage
   ```bash
   # from /home/peix/Workbench/toolsets/modules/ipstone_modules
   enable.conda        # optional – ensure PyYAML is available
   make config         # generates / updates project_config.inc
   ```

# Common Errors
   1. **Missing YAML inputs** – `configure.py` exits with a traceback if any of
      the expected YAML files are absent.  Create or symlink the files before
      running `make config`.
   2. **PyYAML not installed** – if you see `ModuleNotFoundError: No module named
      'yaml'`, activate the lab conda environment with `enable.conda` (or
      `pip install pyyaml` in your preferred environment) and retry.
   3. **Permission issues** – ensure `project_config.inc` is writable in the
      repository root; the target will overwrite the file on each run.

# Examples
   * Basic project setup: `make config`
   * Custom YAML locations (run script directly):
     ```bash
     ./modules/scripts/configure.py --project_config_file config/pdx.yaml \
                                    --samples_file config/pdx.samples.yaml
     ```
