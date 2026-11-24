# Name:
    New project setup (read this first)

# Description
    One command sets up a new project directory for this pipeline:
    `scripts/setup_project.py`. It writes project_config.yaml for the case
    (species, genome, sequencing type, panel), builds samples.yaml and
    sample.fastq.yaml, checks sample names and files, runs preflight checks
    of the reference, BED and environment paths, and writes SETUP_NOTES.md:
    a checklist of what you must still check or decide, and the next
    commands.

    The presets come from lab projects on lilac (section 6). They are data
    files that you can edit:
    - `default_yaml/presets/references.yaml`: one entry per `ref`
    - `default_yaml/presets/panels.yaml`: capture panels and exome kits
    - `default_yaml/project_config.setup_template.yaml`: the commented
      template of project_config.yaml

    Related: `_docs/mouse_and_seq_type_config.md` (what `seq_type`, `ref`,
    `SPECIES` and `call_intervals_bed` change), `_docs/cluster_backends.md`
    (LSF, Slurm, local), `_docs/pipeline_run_checklist.md`.

## 1. Decision tree

```
species ──┬── human ── ref b37 (default) | hg19 | hg38 (untested)
          │             │
          │             ├── seq_type WGS ─── whole-genome targets BED, FACETS 700/750/700
          │             ├── seq_type WES ─── exome kit: --panel xgen_exome_v2 | sureselect_exome_v4 (default)
          │             │                    | idt_exome_v1 | agilent_exome_v5 | --targets-file <BED>
          │             └── seq_type PANEL ─ --panel IMPACT505 | IMPACT468 | IMPACT410 | IMPACT341
          │                                  | HemePACT_v4 | --targets-file <BED>      FACETS 50/150/50
          │
          └── mouse ── ref GRCm38
                        ├── seq_type WGS ─── call_intervals_bed (svaba region BED), Strelka2,
                        │                    no realignment / BQSR, FACETS 700/750/700
                        ├── seq_type WES ─── known-gene exon BED of the genome include, FACETS 50/150/50
                        └── seq_type PANEL ─ a mouse capture-kit BED: --targets-file <BED>
```

    `python modules/scripts/setup_project.py --list-panels` prints the panel
    registry.

## 2. Commands for the five cases

    Run in the new project directory, with the modules tree cloned or
    linked as `modules/`, and the jrflab env active (PyYAML):

```bash
source ~/share/usr/anaconda-envs/jrflab-modules-0.1.4/bin/activate
cd /path/to/new_project          # modules/ is in here
S=modules/scripts/setup_project.py

# human WGS, b37, FASTQ from IGO
python $S --species human --seq-type WGS --fastq-dir /path/to/Project_12345 --dry-run
python $S --species human --seq-type WGS --fastq-dir /path/to/Project_12345

# human WES, xGen exome v2, sample sheet
python $S --species human --seq-type WES --panel xgen_exome_v2 --sample-sheet samples.tsv

# human panel, MSK-IMPACT 505, sample sheet
python $S --species human --seq-type PANEL --panel IMPACT505 --sample-sheet samples.tsv

# mouse WES, BAMs already processed
python $S --species mouse --seq-type WES --bam-dir /path/to/bams

# mouse WGS, FASTQ, svaba 2.0.0
python $S --species mouse --seq-type WGS --fastq-dir /path/to/fastq --svaba-version 2
```

    Other cases:

```bash
# custom FASTA (I-SceI hg19 build; its contigs are b37-style: 1..22 X Y MT)
python $S --species human --ref hg19 --seq-type WGS \
    --ref-fasta /data/riazlab/reference/hg19_IScel/hg19_Iscel_w_vector.fasta \
    --targets-file ~/share/reference/target_panels/whole_genome_1indexed_nochr_scalpel.bed \
    --sample-sheet samples.tsv
# custom panel BED
python $S --species human --seq-type PANEL --targets-file /path/panel_b37.bed --sample-sheet samples.tsv
# Slurm (iris) or no scheduler
python $S ... --cluster slurm      # see SETUP_NOTES.md: config.inc needs an iris site block
python $S ... --cluster local      # use_cluster: false, for tests only
# project_config.yaml and SETUP_NOTES.md only
python $S --species human --seq-type WGS --config-only
```

    Main options:

| Option | Values | Default |
|---|---|---|
| `--species` | human, mouse | required |
| `--ref` | b37, hg19, hg38, GRCm38 | b37 (human), GRCm38 (mouse) |
| `--seq-type` | WGS, WES, PANEL | required |
| `--panel` | a name from panels.yaml (`--list-panels`) | none |
| `--targets-file` | panel BED (PANEL), kit BED (WES), whole-genome BED (WGS) | preset |
| `--call-intervals-bed` | chunking BED for mutect, mutect2, scalpel, lancet | preset (mouse WGS) |
| `--sv-callers` | manta svaba gridss lumpy delly | WGS human: manta svaba gridss; WGS mouse: manta svaba; WES/PANEL: manta |
| `--indel-callers` | varscan_indels strelka_indels scalpel_indels lancet_indels platypus_indels pindel mutect_indels | the first five (lab practice) |
| `--snv-type` | mutect, mutect2 | mutect |
| `--svaba-version` | 1 (svaba 1.1.0), 2 (svaba 2.0.0) | 1 |
| `--strelka-version` | 1, 2 | 1; 2 for mouse WGS |
| `--cluster` | lsf, slurm, local | lsf |
| `--fastq-dir` / `--bam-dir` / `--sample-sheet` | sample input (give one) | |
| `--dry-run` | print what would be written; write nothing | |
| `--force` | replace existing files (old ones kept as `*.bak.<time>`) | refuse |
| `--fix-names` | underscores to hyphens (always on for folder input) | off for sheets |
| `--rawdata-link` | link the FASTQ folder as `rawdata/`, write `rawdata/...` paths | absolute paths |
| `--link-modules` | link `modules/` to this tree if it is missing | off |
| `--no-file-check`, `--no-preflight` | skip the checks | |

    SV callers are separate make targets; `--sv-callers` changes only the
    commands in SETUP_NOTES.md and the svaba keys of project_config.yaml.

## 3. Sample input and naming rules

    Three inputs, one per run:

    - `--fastq-dir DIR [DIR ...]`: IGO layout
      `Sample_<name>_IGO_<project>_<n>/<name>_IGO_..._S1_L001_R1_001.fastq.gz`.
      Every `_R1_` file needs its `_R2_` mate. One `[R1, R2]` entry per lane
      in sample.fastq.yaml. Without a `Sample_` folder the name is the file
      name before `_S<n>_L<nnn>_R1`.
    - `--bam-dir DIR`: `<sample>.bam` files, linked as `bam/<sample>.bam`
      and `bam/<sample>.bam.bai` (from `<sample>.bam.bai` or `<sample>.bai`).
      No alignment step follows.
    - `--sample-sheet TSV`: the explicit design. Use it when the names do not
      show which sample is a tumor and which a normal. Columns (tab-separated, header
      optional):

```
sample  type  patient  path
PT01-T  T     PT01     /path/Sample_PT01_T_IGO_12345_1/PT01_T_IGO_12345_1_S1_L001_R1_001.fastq.gz
PT01-T  T     PT01     /path/Sample_PT01_T_IGO_12345_1/PT01_T_IGO_12345_1_S1_L002_R1_001.fastq.gz
PT01-N  N     PT01     /path/Sample_PT01_N_IGO_12345_2
PT02-T  T     PT02     /path/bams/PT02-T.bam
PT02-N  N     PT02     /path/bams/PT02-N.bam
```
      `path` is an R1 FASTQ (R2 found by name), a folder of FASTQs, or one
      BAM. A sample may have several rows. Relative paths are read from the
      sheet's folder. Example: `_docs/examples/sample_sheet_example.tsv`.

    Rules checked (the run stops and writes nothing on an error):
    - No underscore in sample, tumor, normal or patient names; hyphens are
      allowed. Only letters, digits and hyphens. FASTQ file names on disk may
      keep underscores. Folder input replaces `_` by `-` and lists the
      renamed samples; for a sheet use `--fix-names`.
    - Names are unique; a sample has one type and one patient.
    - One normal per patient. A second normal needs its own patient id.
    - FASTQ R1/R2 and BAM files exist (`--no-file-check` skips this).
    - Warnings, not errors: tumor-only patients, a normal without a tumor, a
      BAM without index, a sheet that mixes FASTQ and BAM samples.

    Pairing guess for folder input (check samples.yaml afterwards): a name
    that ends in `N`, `Normal`, `Blood`, `PBMC` or `GL` (optionally with a
    number, after an optional hyphen) is a normal, and the part before it is
    the patient. A tumor joins the patient whose id is the longest prefix of
    its name, if the next character is not a digit (so `P10-T` does not join
    `P1`).

    samples.yaml has one entry per patient; `tumor` is always a list:
```
- name: PT02
  normal: PT02-N
  tumor: [PT02-T1, PT02-T2]
```

## 4. What each case sets

    Values written to project_config.yaml. All other keys are the lab
    defaults (bwamem, markdup, MuTect 1, five indel callers, ann_facets).
    Keys not used for the case are written commented out with an example.

| Key | human WGS | human WES | human PANEL | mouse WES | mouse WGS |
|---|---|---|---|---|---|
| `ref` | b37 | b37 | b37 | GRCm38 | GRCm38 |
| `seq_type` | WGS | WES | PANEL | WES | WGS |
| `targets_file` | whole_genome_1indexed_nochr_scalpel.bed | (from EXOME_BED) | panel BED | (genome include) | not set |
| `exome_bed` | - | kit BED if not the default | - | - | - |
| `targets_list` | - | kit list (preset) | panel list (preset) | - | - |
| `call_intervals_bed` | (targets_file) | (targets_file) | (targets_file) | (targets_file) | mouse_mm10_removed_blacklist-regon_no-chr.bed |
| `ontarget_file` / `offtarget_file` | - | - | CNVkit BEDs (preset) | - | - |
| `facets_pre_cval / cval1 / cval2` | 700 / 750 / 700 | 50 / 150 / 50 | 50 / 150 / 50 | 50 / 150 / 50 | 700 / 750 / 700 |
| `facets_min_nhet` | 25 | 25 | 25 | 25 | 25 |
| `ann_pathogen` | true | true | true | false | false |
| `bam_no_realn` / `bam_no_recal` | false | false | false | false | true / true |
| `strelka_version` | (1) | (1) | (1) | (1) | 2 |
| `svaba_version` | 1 | - | - | - | 1 |
| `merge_split_bams` | false | false | false | false | false |
| Manta `--exome` (from seq_type) | no | yes | yes | yes | no |
| resource profile (from seq_type) | wgs | wes | wes | wes | wgs |

    Generated examples (regenerate with `bash _docs/examples/make_examples.sh`):
    `_docs/examples/human_wgs/`, `human_wes/`, `human_panel_impact505/`,
    `mouse_wes/`, `mouse_wgs/`, each with project_config.yaml and
    SETUP_NOTES.md. The RNA-seq example `project_config.yaml_RNAseq_star` is
    unchanged (setup_project.py does not cover RNA-seq).

    Panel and kit presets (all b37 BEDs use contigs 1..22 X Y, no `chr`;
    paths checked on lilac 2026-11-24):

| Preset | Kind | targets BED | CNVkit BEDs | Used by |
|---|---|---|---|---|
| IMPACT505 | panel | `~/share/lib/bed_files/targets/IMPACT505/b37/IMPACT505_b37_targets.bed` | `~/share/lib/bed_files/IMPACT505_b37_CNVkit_{on,off}-target.bed` | late_mosaicism |
| IMPACT468 | panel | `~/share/reference/target_panels/impact468.bed` | `~/share/lib/bed_files/IMPACT468_b37_CNVkit_{on,off}-target.bed` | Fresia 17318 |
| IMPACT410 | panel | `~/share/lib/bed_files/targets/IMPACT410/b37/IMPACT410_b37_targets.bed` | yes | - |
| IMPACT341 | panel | `~/share/lib/bed_files/targets/IMPACT341/b37/IMPACT341_b37_targets.bed` | yes | - |
| HemePACT_v4 | panel | `~/share/lib/bed_files/targets/HemePACT_v4/b37/HemePACT_v4_b37_targets.bed` | none | - |
| xgen_exome_v2 | exome | `~/share/lib/bed_files/targets/IDT_Exome_xGen_v2/b37/IDT_Exome_xGen_v2_b37_targets.bed` | none | neogenomics_Atif (own copy) |
| sureselect_exome_v4 | exome | `~/share/reference/target_panels/sure_select_exome_v4_b37.bed` (b37 default) | none | - |
| idt_exome_v1 | exome | `~/share/lib/bed_files/targets/IDT_Exome_v1_FP/b37/IDT_Exome_v1_FP_b37_targets.bed` | none | - |
| agilent_exome_v5 | exome | `~/share/lib/bed_files/targets/AgilentExon_v5/b37/AgilentExon_v5_b37_targets.bed` | none | - |
| mouse_known_exons | exome | `~/share/reference/mus_musculus_known_genes_exons_GRCm38_noheader.bed` (GRCm38 default) | none | - |

    Not found on lilac: any mouse capture-kit BED (searched
    `~/share/reference`, `~/share/reference/target_panels`,
    `~/share/lib/bed_files`, `/data/riazlab/lib/reference`;
    `Agilent_SureSelectBedFiles/S03723314_*` is the human All Exon V4).

## 5. Preflight checks

    Results go to the screen and to SETUP_NOTES.md (FAIL = fix before the
    run, WARN = check). Off lilac most paths are missing; that is expected.
    - reference FASTA, its `.fai` and `.dict`
    - every BED that the config uses (targets_file, exome_bed or the genome
      default exome BED, call_intervals_bed, CNVkit BEDs) and targets_list
      exist
    - contig style of each BED (`chr` or no `chr`) equals the FASTA; contigs
      of the BED that are not in the FASTA `.fai` are listed (for example
      `M` against `MT`)
    - environments: JRFLAB_MODULES_ENV, CNVKIT_ENV (PANEL), GRIDSS_ENV
      (gridss), SVABA_ENV (svaba 1), STRELKA_ENV (Strelka2), the svaba 2.0.0
      binary
    - SITE_TMPDIR (exported as TMPDIR by Makefile.inc) exists, is writable
      and is not node-local (`/tmp`, `/scratch`, ...); a node-local TMPDIR
      of the current shell is a warning (cluster_backends.md section 5)
    - `modules/Makefile` exists in the project
    - mouse: dbsnp_subset is missing (warning)

## 6. Lab projects the presets come from (read only, 2026-11-24)

| Project (lilac) | ref | Type | targets_file | FACETS pre/c1/c2 |
|---|---|---|---|---|
| /data/reis-filho/data/parejaf/WGS_CDH1SV | b37 | WGS | whole_genome_1indexed_nochr_scalpel.bed | 2050 / 2150 / 2050 |
| .../peix/ISceI_integrated_analysis_Philip/.../run_wgs_Iscel_experiment_tumor_normal | hg19 + custom FASTA | WGS | whole_genome_0indexed_nochr.bed | 650 / 750 / 650 |
| .../peix/hpv_wgs/pipelines/hpv_structural_variant_call | b37 | WGS (SV only) | not set | 50 / 150 / 50 |
| .../peix/parejaf/late_mosaicism/pipeline_runs | b37 | IMPACT505 | IMPACT505_b37_targets.bed (+ targets_list) | 50 / 150 / 50 |
| .../peix/parejaf/Fresia_Project_17318/run_pipelines | b37 | IMPACT468 | impact468.bed | 50 / 150 / 50 |
| /data/reis-filho/data/selenicp/MSK_IMPACT_synchronous_pair (and MSK_IMPACT_pole_herman) | b37 | IMPACT505 | impact505.bed (bait tiling) | 50 / 150 / 50 |
| .../peix/neogenomics_Atif/pipeline_alignment_run | b37 | xGen exome v2, tumor-only | own xgen v2 targets BED | not set |

    None of these projects sets `seq_type` (they predate it) or
    `merge_split_bams` (default false).

## 7. After setup

```bash
cat SETUP_NOTES.md                      # tick every item of section 1
make config                             # project_config.yaml -> project_config.inc; after every yaml change
make -n bwamem | grep -c run.py         # FASTQ input: alignment jobs
make -n somatic_variants | grep -c run.py
make -n facets manta_tumor_normal
```
    On lilac run make as an LSF job, not on the login node (skill
    `lilac-genomics-make-driver`; SETUP_NOTES.md lists the targets in the
    order they can run):
```bash
D=~/.ipdot/skills/lilac-genomics-make-driver/scripts/jrflab_make_driver.sh
$D bwamem
for t in wgs_metrics somatic_variants facets manta_tumor_normal svaba_tumor_normal gatk; do $D $t; done
```

## 8. Known pitfalls

    - `merge_split_bams: true` (the old default of
      default_yaml/project_config.yaml) stops `make bwamem` from FASTQ with
      "No rule to make target 'unprocessed_bam/<sample>.bam'" under GNU make
      3.82 (the lilac default, /usr/bin/make) and 4.0; make 4.4.1 finds the
      alignment chain (dry runs on lilac, 2026-11-24: 0 jobs against 695 with
      `false`). setup_project.py and the default yaml now write `false`.
    - IMPACT505 has two BEDs: the targets BED (9,360 regions, 2.01 Mb) and
      the bait tiling `impact505.bed` (39,012 probes). Lab projects use
      both. Choose one per project and keep it for every batch.
    - FACETS critical values for WGS differ between projects (700/750/700
      lab value; 2050/2150/2050 and 650/750/650 in two projects). Decide
      before the first `make facets`.
    - `whole_genome_0indexed_nochr.bed` and the mouse svaba region BED name
      the mitochondrion `M`; b37 and GRCm38 name it `MT`. The preflight
      lists it.
    - The I-SceI "hg19" FASTA has b37-style contig names (`1`, not `chr1`):
      use no-`chr` BEDs with it. The hg19 default WGS BED of the preset is
      chr-prefixed, so give `--targets-file`.
    - Mouse WES with a capture kit: genome_inc/GRCm38.inc sets TARGETS_FILE
      with `=`, so `exome_bed` has no effect. Use `--seq-type PANEL
      --targets-file <kit BED>`.
    - WES: QUALIMAP_TARGETS_FILE stays the SureSelect 50 Mb BED of the
      genome include, whatever the kit.

## 9. Old setup scripts

| Script | Decision | Reason |
|---|---|---|
| `init_project`, `scripts/init_project.pl` | keep | Copy the generic yaml files and write the Makefile. Now print a pointer to setup_project.py. setup_project.py writes the Makefile and summary_config.yaml itself. |
| `scripts/configure.py` | keep | Converts the yaml files to project_config.inc (`make config`). Unchanged. |
| `scripts/create_sample_yaml.py` | deprecate (header) | Needs glob2; `FileType('w', 0)` fails on Python 3; deletes underscores (`P1_T2` becomes `P1T2`); `tums is not None` is always true; prefix pairing joins `P10T` to normal `P1N`. Replaced by `--fastq-dir`. |
| `scripts/create_sample_yaml2.py` | deprecate (header) | Same pairing defects; needs glob2. Replaced by `--fastq-dir`. |
| `scripts/create_sample_sets.pl` | deprecate (header) | Pairs by the first number in the name; the "no tumor" warning never prints (`next and print`, a precedence defect). Replaced by `--sample-sheet`. |
| `scripts/convert_sample_txt2yaml.py` | keep | Correct for its input (old samples.txt / sample_sets.txt: tumors then the normal on one line). |
| `scripts/prepare_samples/fastq_to_samples/` | deprecate (headers) | Assumes one lane (two FASTQ files) per sample, a fixed `rawdata/` layout and `-T`/`-N` names; writes `_samples.yaml`. Replaced by `--fastq-dir`. |
| `scripts/create_iontorrent_sample_yaml.py`, `create_iontorrent_sample_merge_yaml.py` | keep (not tested) | Ion Torrent sample-map input, which setup_project.py does not cover. Python 2 only (`FileType('w', 0)`), needs glob2. |

# Input
    Command-line options (section 2), FASTQ or BAM folders or a sample sheet
    (section 3), the presets in `default_yaml/presets/`.

# Output
    In the project directory: `project_config.yaml`, `samples.yaml`,
    `sample.fastq.yaml` (FASTQ input), `bam/<sample>.bam` links (BAM input),
    `SETUP_NOTES.md`, and, if absent, `Makefile` and `summary_config.yaml`.
    Existing files are not replaced without `--force`.

# Error
    - `sample name 'X_1' contains an underscore`: rename, or `--fix-names`.
    - `patient P has 2 normals`: give the second normal its own patient id.
    - `panel X is a panel preset; use it with --seq-type PANEL`: kits are
      `kind: exome` (WES), panels `kind: panel` (PANEL).
    - `--ref b37 is a human genome but --species is mouse`.
    - `<file> exists (use --force ...)`: nothing was written.
    - `setup_project.py needs PyYAML`: activate the jrflab env.

# Examples
```bash
python modules/scripts/setup_project.py --list-panels
python modules/scripts/setup_project.py --species human --seq-type PANEL --panel IMPACT505 \
    --sample-sheet samples.tsv --dry-run
```
