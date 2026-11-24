# Setup notes: mouse_wes

Example written by `modules/scripts/setup_project.py` (`_docs/examples/make_examples.sh`).
Command: `python modules/scripts/setup_project.py --species mouse --seq-type WES --config-only`
Guide: `modules/_docs/new_project_setup.md`

| Setting | Value |
|---|---|
| species | mouse |
| ref | GRCm38 |
| seq_type | WES |
| panel / kit | - |
| cluster | lsf |
| input | none (--config-only) |
| samples | 0 (0 tumors, 0 normals) |
| patients | 0 (0 with a normal) |
| SV callers | manta |
| indel callers | varscan_indels strelka_indels scalpel_indels lancet_indels platypus_indels |

## 1. Check or decide before the first run

- [ ] Write `samples.yaml` (and `sample.fastq.yaml` for FASTQ input): run setup_project.py again with --sample-sheet, --fastq-dir or --bam-dir and --force, or write them by hand.
- [ ] Capture kit: the targets are `~/share/reference/mus_musculus_known_genes_exons_GRCm38_noheader.bed`. Confirm the kit with IGO or the vendor; for another kit use `--panel <kit>` or `--targets-file`.
- [ ] `QUALIMAP_TARGETS_FILE` and `EMU_TARGETS_FILE` stay the SureSelect 50 Mb BEDs of the genome include, whatever the kit.
- [ ] FACETS critical values 50/150/50, min_nhet 25 (lab values for exomes and panels).
- [ ] Manta runs with `--exome` (seq_type WES).
- [ ] Mouse: these targets stop with an explicit error: msisensor, mimsi, hotspot, hotspot_summary, hr_detect, cravat_annotate, cravat_summary. Do not run them.
- [ ] Mouse: `ann_pathogen: false` (pathogenicity annotation is human-only).
- [ ] Mouse: `cluster_samples` needs `dbsnp_subset` (a BED of common SNP sites); none exists on lilac yet.
- [ ] Mouse: `delmh_summary` needs BSgenome.Mmusculus.UCSC.mm10, which is not installed in jrflab-modules-0.1.4.
- [ ] Mouse: GRIDSS runs without the human blacklist and PON.
- [ ] Mouse WES: targets are the known-gene exon BED of genome_inc/GRCm38.inc, not a capture-kit BED. No mouse kit BED was found on lilac. For a kit BED use `--seq-type PANEL --targets-file <kit BED>`.
- [ ] Reference GRCm38: Mouse GRCm38 / mm10, Ensembl 71 FASTA, contigs 1..19 X Y MT (no chr prefix).
- [ ] Annotation: `ann_pathogen: false`, `vcf_post_ann_filter_expression: ExAC_AF > 0.01`.

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
for t in bam_metrics somatic_variants facets manta_tumor_normal; do $D $t; done   # 2. read bam/ only; run in parallel
$D mutation_summary   # 3. after somatic_variants (needs a big driver: JRFLAB_DRIVER_MEM=64 JRFLAB_DRIVER_MAXMEM=96)
```

Related: `modules/_docs/mouse_and_seq_type_config.md`, `modules/_docs/cluster_backends.md`, `modules/_docs/pipeline_run_checklist.md`.
