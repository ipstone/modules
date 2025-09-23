# Title:
   Adding New Samples to an Existing Project

# Goal
   Incorporate additional samples without rebuilding existing outputs.

# Steps
1. **Cleanup selectively** – remove only the directories that must be regenerated:
   - `summary/`
   - Any sample-specific outputs (e.g. alignment or variant call directories) that will change.
2. **Stage new data** – copy the new FASTQ/BAM files into the appropriate raw directories.
3. **Update YAML** – append entries to `samples.yaml`, `sample_attr.yaml`, and related files.
4. **Regenerate Make variables** – run `make config` after every YAML change.
5. **Re-run incremental targets**:
   - Align new samples: `make bwamem`.
   - Update metrics: `make bam_interval_metrics`.
   - Refresh variant calling/summary targets (`make somatic_variants`, `make mutation_summary`, etc.) as required.

# Tips
- Avoid deleting alignment directories for previously processed samples to save time.
- Keep versioned copies of previous results until the new run is validated.
- Re-check pairing heatmaps after adding new tumor/normal samples (`make cluster_samples`).
