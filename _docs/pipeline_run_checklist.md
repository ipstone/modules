# Title:
   jrflab Pipeline Run Checklist

# Preparation
1. **Clone/refresh modules** – `git clone` or `git pull` to obtain the latest pipeline code.
2. **Bootstrap project** – run `perl modules/scripts/initProject.pl` (or the helper wrapper) to create the project skeleton.
3. **Stage raw data** – copy FASTQ or BAM inputs into the project `rawdata/` or `bam/` directories as appropriate.
4. **Generate draft YAML** – execute `python modules/scripts/create_sample_yaml2.py rawdata` to auto-build sample stanzas.  If you encounter `ImportError: No module named glob2`, activate the jrflab environment:
   ```bash
   source ~/share/usr/anaconda-envs/jrflab-modules-0.1.4/bin/activate ~/share/usr/anaconda-envs/jrflab-modules-0.1.4/
   ```

# Configure Project
5. **Edit YAML** – inspect and adjust `samples.yaml` and `project_config.yaml` (plus optional `sample_attr.yaml`, `sample.fastq.yaml`, `sample_merge.yaml`).
6. **Sanity check** – confirm pairings, bed files, and project switches are correct.
7. **Materialise Make variables** – run `make config` (wrapper for `modules/scripts/configure.py`).  Re-run this command any time the YAML files change.

# Core Workflow
8. `make bwamem` – aligns FASTQs and generates sorted BAMs.
9. `make bam_interval_metrics` – runs Picard metrics.  If `PercentTargetBases2X < 90%`, revisit the BED configuration in `project_config.yaml` and regenerate config (step 7).
10. `make cluster_samples` – prepares contamination/contest inputs (inspect resulting heatmaps).
11. Review `snps_filtered.heatmap` outputs to confirm tumor/normal pairings prior to variant calling.
12. `make somatic_variants` – executes the full somatic variant calling stack.  Troubleshooting tips:
    - If annotation modules are missing, source the jrflab Conda environment.
    - Set `ANN_PATHOGEN=false` in `project_config.yaml` if CRAVAT/OpenCravat is unavailable, then rerun `make config`.
13. `make hotspot` – genotypes hotspot panels once somatic calls succeed.
14. `make mutation_summary` – builds Excel/TSV summaries (prerequisite for downstream filtering).

# Post-run Reminders
- Inspect `summary/` outputs (Facets plots, TSVs) before distributing results.
- See `_docs/filtering_dataset.md` for recommended review steps prior to reporting.
- When adding new samples, follow `_docs/updating_projects_with_new_samples.md` to avoid rebuilding the entire workspace.
