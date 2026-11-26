# Setup notes: mouse_wgs

Example written by `modules/scripts/setup_project.py` (`_docs/examples/make_examples.sh`).
Command: `python modules/scripts/setup_project.py --species mouse --seq-type WGS --config-only`
Guide: `modules/_docs/new_project_setup.md`

| Setting | Value |
|---|---|
| species | mouse |
| ref | GRCm38 |
| seq_type | WGS |
| panel / kit | - |
| cluster | lsf |
| input | none (--config-only) |
| samples | 0 (0 tumors, 0 normals) |
| patients | 0 (0 with a normal) |
| SV callers | manta, svaba |
| indel callers | varscan_indels strelka_indels scalpel_indels platypus_indels |

## 1. Check or decide before the first run

- [ ] Write `samples.yaml` (and `sample.fastq.yaml` for FASTQ input): run setup_project.py again with --sample-sheet, --fastq-dir or --bam-dir and --force, or write them by hand.
- [ ] WGS chunking: `targets_file` = `(not set)` and `call_intervals_bed` = `/data/riazlab/lib/reference/svaba/mouse_mm10_removed_blacklist-region_no-chr.MT.bed`. Lab human WGS projects set the whole-genome BED as targets_file; mouse WGS sets call_intervals_bed only.
- [ ] FACETS critical values 700/750/700 (pre_cval/cval1/cval2), min_nhet 25. These are the lab WGS values. Earlier WGS projects used other values: WGS_CDH1SV 2050/2150/2050, I-SceI WGS 650/750/650. Decide before the first `make facets`.
- [ ] Resource profile `config/profiles/wgs.inc` (sized for 30-100x). For higher depth raise single values in project_config.yaml (for example `lancet_resources`).
- [ ] Run `make wgs_metrics` after alignment (coverage check before calling).
- [ ] Mouse: these targets stop with an explicit error: msisensor, mimsi, hotspot, hotspot_summary, hr_detect, cravat_annotate, cravat_summary. Do not run them.
- [ ] Mouse: `ann_pathogen: false` (pathogenicity annotation is human-only).
- [ ] Mouse: `cluster_samples` needs `dbsnp_subset` (a BED of common SNP sites); none exists on lilac yet.
- [ ] Mouse: `delmh_summary` needs BSgenome.Mmusculus.UCSC.mm10, which is not installed in jrflab-modules-0.1.4.
- [ ] Mouse: GRIDSS uses the mm10 blacklist and the riazlab FASTA copy (GRIDSS_REF_FASTA), without a PON.
- [ ] Mouse WGS: `bam_no_realn: true` and `bam_no_recal: true` skip GATK realignment and BQSR, and `strelka_version: 2` runs Strelka2, as in the mouse WGS example of mouse_and_seq_type_config.md. Set the two bam keys to false to realign and recalibrate with the MGP v5 known sites.
- [ ] Reference GRCm38: Mouse GRCm38 / mm10, Ensembl 71 FASTA, contigs 1..19 X Y MT (no chr prefix).
- [ ] Reference GRCm38: The WGS chunking BED is the svaba region BED with the mitochondrion renamed from 'M' to 'MT' (the FASTA name); the original file, which uses 'M', is unchanged next to it.
- [ ] svaba 1.1.0 from SVABA_ENV (`--svaba-version 2` switches to 2.0.0).
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
make -n facets manta_tumor_normal svaba_tumor_normal
```

On lilac, run make itself as an LSF job (survives a login-node reboot; skill `lilac-genomics-make-driver`):

```bash
D=~/.ipdot/skills/lilac-genomics-make-driver/scripts/jrflab_make_driver.sh
$D bwamem                         # 1. alignment (FASTQ input; skip when BAMs are in bam/)
for t in wgs_metrics somatic_variants facets manta_tumor_normal svaba_tumor_normal; do $D $t; done   # 2. read bam/ only; run in parallel
$D mutation_summary   # 3. after somatic_variants (needs a big driver: JRFLAB_DRIVER_MEM=64 JRFLAB_DRIVER_MAXMEM=96)
```

Related: `modules/_docs/mouse_and_seq_type_config.md`, `modules/_docs/cluster_backends.md`, `modules/_docs/pipeline_run_checklist.md`.
