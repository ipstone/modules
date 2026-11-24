# Setup notes: human_panel_impact505

Example written by `modules/scripts/setup_project.py` (`_docs/examples/make_examples.sh`).
Command: `python modules/scripts/setup_project.py --species human --seq-type PANEL --panel IMPACT505 --config-only`
Guide: `modules/_docs/new_project_setup.md`

| Setting | Value |
|---|---|
| species | human |
| ref | b37 |
| seq_type | PANEL |
| panel / kit | IMPACT505 |
| cluster | lsf |
| input | none (--config-only) |
| samples | 0 (0 tumors, 0 normals) |
| patients | 0 (0 with a normal) |
| SV callers | manta |
| indel callers | varscan_indels strelka_indels scalpel_indels lancet_indels platypus_indels |

## 1. Check or decide before the first run

- [ ] Write `samples.yaml` (and `sample.fastq.yaml` for FASTQ input): run setup_project.py again with --sample-sheet, --fastq-dir or --bam-dir and --force, or write them by hand.
- [ ] Panel BED: `targets_file` = `~/share/lib/bed_files/targets/IMPACT505/b37/IMPACT505_b37_targets.bed`. Confirm the panel version with IGO/CMO (IMPACT341, 410, 468 and 505 differ).
- [ ] `targets_list` = `~/share/lib/bed_files/targets/IMPACT505/b37/IMPACT505_b37_targets.list` (CollectHsMetrics in bam_metrics).
- [ ] CNVkit BEDs set (`make cnv_kit`): `~/share/lib/bed_files/IMPACT505_b37_CNVkit_on-target.bed` and `~/share/lib/bed_files/IMPACT505_b37_CNVkit_off-target.bed`.
- [ ] FACETS critical values 50/150/50, min_nhet 25 (lab values for exomes and panels).
- [ ] Manta runs with `--exome` (seq_type PANEL).
- [ ] Panel preset IMPACT505: Panel BED choice: the late_mosaicism project chose the targets BED; the selenicp projects use the bait tiling impact505.bed. Decide which one this project uses and keep it for all batches.
- [ ] Panel preset IMPACT505: qc/bam_interval_metrics.mk already defaults to the IMPACT505 baits and targets lists (genome_inc/b37.inc).
- [ ] Annotation: `ann_pathogen: true`, `vcf_post_ann_filter_expression: ExAC_AF > 0.01`.

## 2. Sample set-up messages

None.

## 3. Preflight

Not run (`--no-preflight`).

## 4. Next commands

```bash
cd <project>
source ~/share/usr/anaconda-envs/jrflab-modules-0.1.4/bin/activate   # configure.py needs PyYAML
make config                      # writes project_config.inc; re-run after every yaml change
make -n somatic_variants | grep -c run.py   # dry run: count the jobs it would submit
make -n facets manta_tumor_normal
```

On lilac, run make itself as an LSF job (survives a login-node reboot; skill `lilac-genomics-make-driver`):

```bash
D=~/.ipdot/skills/lilac-genomics-make-driver/scripts/jrflab_make_driver.sh
$D bwamem                         # 1. alignment (FASTQ input; skip when BAMs are in bam/)
for t in bam_metrics somatic_variants facets manta_tumor_normal cnv_kit gatk; do $D $t; done   # 2. read bam/ only; run in parallel
$D mutation_summary   # 3. after somatic_variants (needs a big driver: JRFLAB_DRIVER_MEM=64 JRFLAB_DRIVER_MAXMEM=96)
$D cravat_annotate    # 3. after gatk (germline), then cravat_summary
```

Related: `modules/_docs/mouse_and_seq_type_config.md`, `modules/_docs/cluster_backends.md`, `modules/_docs/pipeline_run_checklist.md`.
