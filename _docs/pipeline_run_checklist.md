# Title:
   jrflab Pipeline Run Checklist

# Preparation
1. **Sync modules** - `git pull` this repository to pick up the latest makefiles
   and scripts.
2. **Bootstrap project** - run `./init_project <project_name>` to scaffold the
   analysis directory (wrapper around `scripts/init_project.pl`).
3. **Stage raw data** - copy FASTQ or BAM inputs into `rawdata/` or `bam/`.
4. **Draft YAML** - `python scripts/create_sample_yaml2.py rawdata` generates
   starter `samples.yaml`/`sample.fastq.yaml` entries.  If Python complains about
   missing modules, activate `JRFLAB_MODULES_ENV` first.

# Configure Project
5. **Edit YAML** - update `samples.yaml`, `sample_attr.yaml`, and
   `project_config.yaml` with the correct pairings, capture kit, and tunables.
6. **Sanity check** - confirm BED paths, reference builds, and sample labels.
7. **Materialise Make variables** - run `make config` whenever YAML files
   change.  This regenerates `project_config.inc`.

# Core Workflow
8. `make bwamem` - aligns FASTQs and writes sorted BAMs to `bam/`.
9. `make bam_interval_metrics` - runs Picard metrics.  Investigate low target
   coverage (`PercentTargetBases2X < 90`) before proceeding.
10. `make cluster_samples` - builds contamination/contest heatmaps to validate
    tumor/normal pairings.
11. `make somatic_variants` - executes the somatic calling stack (Mutect,
    Strelka, VarScan, annotations).
12. `make hotspot_summary` - optional hotspot genotyping once somatic calls
    succeed.
13. `make mutation_summary` - produces `summary/mutation_summary.xlsx` plus TSVs
    under `summary/tsv/` for manual review.

# Post-run Reminders
- Inspect `summary/`, `facets/`, and log files (`log/<target>.<date>.log`) prior
  to sharing results.
- Follow `_docs/filtering_dataset.md` when curating the final `muts.csv`.
- For incremental cohorts, review `_docs/updating_projects_with_new_samples.md`.
- When custom environments are needed (e.g. Polysolver, Sufam), verify the paths
  in `config.inc` before launching those targets.
