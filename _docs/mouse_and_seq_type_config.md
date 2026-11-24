# Name:
    seq_type and mouse configuration (human WGS, human WES/panel, mouse WES, mouse WGS)

# Description
    One codebase runs four kinds of project. Two keys in project_config.yaml
    choose the behaviour:

    - `ref`: the genome. `b37`, `hg19`, `hg38` (human) or `GRCm38` (mouse).
      The genome include `genome_inc/<ref>.inc` sets the reference files and
      `SPECIES` (`GRCm38.inc` sets `SPECIES = mouse`; all others are human).
    - `seq_type`: `WGS`, `WES` or `PANEL`. The include `config/seq_type.inc`
      reads it before the genome include.

    This replaces the branches `mouse_wes` and `mouse_wgs`.

    To set up a new project for any of these cases, use
    `scripts/setup_project.py` (guide: `_docs/new_project_setup.md`).

## What each setting changes

| Setting | EXOME | TARGETS_FILE | Manta `--exome` | Resource profile | Strelka2 `--exome` |
|---|---|---|---|---|---|
| `seq_type: WGS` | false | project value (optional) | no | `config/profiles/wgs.inc` | no |
| `seq_type: WES` | true | `EXOME_BED` of the genome include | yes | `config/profiles/wes.inc` | yes |
| `seq_type: PANEL` | false | project value, required (stops with an error if empty) | yes | `config/profiles/wes.inc` | yes |
| `seq_type` unset (old projects) | as configured | as configured | yes only if TARGETS_FILE is set (old rule) | `config/profiles/wgs.inc` | no |

| Setting | Effect |
|---|---|
| `ref: GRCm38` | mouse FASTA (Ensembl 71, contigs `1..19 X Y MT`, no `chr`), MGP v5 dbSNP, MGP indels as `KNOWN_INDELS`, mouse svaba dbSNP and region BED, mm10 gene BED for FACETS gene calls, `NO_HOTSPOTS = true`, `SPECIES = mouse` |
| `SPECIES = mouse` | msisensor, mimsi, hotspot, hotspot_summary, hr_detect, cravat_annotate/cravat_summary stop with an explicit error; GRIDSS runs without the human blacklist and PON |
| `call_intervals_bed` | BED used to split the genome into chunks for mutect, mutect2, scalpel and lancet. Default: `targets_file`. Set it when the chunking BED is not the capture BED (for example mouse WGS) |
| `manta_exome: true/false` | forces Manta exome mode on or off |
| `resource_profile: wgs/wes` | forces a resource profile independent of seq_type |
| any `*_RESOURCES`, `*_THREADS`, `*_JAVA_MEM`, `PICARD_MEM` | overrides one value of the profile (all profile values are `?=`) |
| `strelka_version: 2` | runs Strelka2 from `STRELKA_ENV` instead of Strelka 1 (default `1`) |

## Resource profiles
    `config/profiles/wgs.inc` holds the values this fork used before seq_type
    existed (sized for 30-100x whole genomes). `config/profiles/wes.inc` holds
    the upstream jrflab values (`git show upstream/master:<file>`). Both cover
    bwamem, processBam (index, filter, markdup, realignment, BQSR), FACETS,
    MuTect, Scalpel, Lancet, Strelka and Picard memory. Each `*_RESOURCES`
    value is the option string given to `$(call RUN,...)` (`-s` soft memory,
    `-m` hard memory, `-w` walltime). The samtools sort step keeps its own
    `BAM_SORT_*` variables in `bam_tools/processBam.mk` for both profiles.

## BAM processing for mouse
    Duplicate marking stays ON by default for mouse WGS and WES
    (`bam_dup_type: markdup`, owner decision). GATK indel realignment and base
    quality recalibration can be switched off with the existing keys:

```
bam_dup_type: markdup   # keep duplicate marking (default); rmdup or none also work
bam_no_realn: true      # skip IndelRealigner
bam_no_recal: true      # skip BaseRecalibrator / PrintReads -BQSR
```
    With both left `false`, realignment uses the MGP v5 indels
    (`KNOWN_INDELS`) and BQSR uses the MGP v5 SNPs (`DBSNP`).

# Input
    `project_config.yaml` (converted to `project_config.inc` by
    `scripts/configure.py`), `samples.yaml`, and BAM or FASTQ files.

## Human WGS (b37)
```
ref: b37
seq_type: WGS
aligner: bwamem
bam_dup_type: markdup
# whole-genome BED, used for chunking (lab practice for WGS projects)
targets_file: ~/share/reference/target_panels/whole_genome_1indexed_nochr_scalpel.bed
snv_type: mutect
indel_types: varscan_indels strelka_indels scalpel_indels lancet_indels platypus_indels
ann_pathogen: true
facets_pre_cval: 700
facets_cval1: 750
facets_cval2: 700
```

## Human WES (b37)
```
ref: b37
seq_type: WES           # TARGETS_FILE = EXOME_BED of genome_inc/b37.inc
aligner: bwamem
bam_dup_type: markdup
# no targets_file needed; for another capture kit set exome_bed: <kit BED>
snv_type: mutect
indel_types: varscan_indels strelka_indels scalpel_indels lancet_indels platypus_indels
ann_pathogen: true
facets_pre_cval: 50
facets_cval1: 150
facets_cval2: 50
```
    For a targeted panel use `seq_type: PANEL` and set
    `targets_file: <panel BED>`.

## Mouse WES (GRCm38)
```
ref: GRCm38
seq_type: WES           # TARGETS_FILE = mus_musculus_known_genes_exons_GRCm38_noheader.bed
aligner: bwamem
bam_dup_type: markdup
bam_no_realn: false
bam_no_recal: false
snv_type: mutect
indel_types: varscan_indels strelka_indels scalpel_indels lancet_indels platypus_indels
ann_pathogen: false     # pathogenicity annotation is human-only (b37/hg19)
facets_pre_cval: 50
facets_cval1: 150
facets_cval2: 50
```

## Mouse WGS (GRCm38)
```
ref: GRCm38
seq_type: WGS
aligner: bwamem
bam_dup_type: markdup   # duplicate marking stays on
bam_no_realn: true      # optional: skip indel realignment
bam_no_recal: true      # optional: skip BQSR
# whole genome minus gaps/blacklist, no chr prefix; used only for chunking
call_intervals_bed: /data/riazlab/lib/reference/svaba/mouse_mm10_removed_blacklist-regon_no-chr.bed
snv_type: mutect
indel_types: varscan_indels strelka_indels scalpel_indels lancet_indels platypus_indels
strelka_version: 2      # Strelka2, as the mouse WGS projects used
ann_pathogen: false
facets_pre_cval: 700
facets_cval1: 750
facets_cval2: 700
```

## Custom hg19 build (I-SceI palindrome project)
    `genome_inc/hg19.inc` now points to the standard UCSC hg19 FASTA. The
    I-SceI project sets its own FASTA in project_config.yaml. The project
    used `hg19_Iscel_w_vector.fasta` (its modules/genome_inc/hg19.inc,
    checked 2026-11-24); `hg19_IScel_palindrom.fasta`, named here before,
    does not exist on lilac. The FASTA has b37-style contig names (`1`, not
    `chr1`), so its BEDs must have no `chr` prefix.
```
ref: hg19
ref_fasta: /data/riazlab/reference/hg19_IScel/hg19_Iscel_w_vector.fasta
nochr_ref_fasta: /data/riazlab/reference/hg19_IScel/hg19_Iscel_w_vector.fasta
chr_ref_fasta: /data/riazlab/reference/hg19_IScel/hg19_Iscel_w_vector.fasta
```

# Output
    Same targets and file names as before. Only resource options, reference
    paths and tool options change.

# Error
    - `SEQ_TYPE=PANEL needs targets_file ...`: set `targets_file`.
    - `SEQ_TYPE='x' is not valid`: use WGS, WES or PANEL (lower case also works).
    - `<tool> is a human-only tool and cannot run with REF=GRCm38`: the target
      has no mouse resources (msisensor, mimsi, hotspot, hotspot_summary,
      hr_detect, cravat).
    - `DBSNP_SUBSET (BED of common SNP sites) is not set for REF=GRCm38`:
      `snp_cluster` (contamination/clusterSamples.mk) has no mouse SNP-site
      BED yet; build one and set `dbsnp_subset`.
    - `non-hg19/b37 pathogen annotation unsupported`: set `ann_pathogen: false`.

# Known limitations (mouse)
    - `DBSNP_SUBSET` for mouse is a TODO: no SNP-site BED exists on lilac.
    - `delmh_summary` uses `BSgenome.Mmusculus.UCSC.mm10` for mouse; it is not
      installed in the default R environment (jrflab-modules-0.1.4).
    - `CENTROMERE_TABLE` (`centromere_mm10.txt`) is the UCSC gap table with
      `chr` names, the same format as the human `centromere.txt`.
    - `gridss_somatic_filter` runs without a PON and with its default `--ref`.

# Post-processing

# Examples
```
make -n USE_CLUSTER=false manta      # check --exome and REF_FASTA before a run
make somatic_variants
```
