# Name:
    svabaTN

# Description
    Executes SvABA on each tumor/normal pair using `sv_callers/svabaTN.mk`.  The
    pipeline wraps `svaba run`, supplying project-specific defaults for the
    reference, dbSNP indel resource, and blacklist BED.

# Inputs
    - `bam/<tumor>.bam`, `bam/<normal>.bam` symlinks.
    - `SVABA` binary and reference resources configured in `config.inc`
      (`SVABA_REF`, `SVABA_DBSNP`, `SVABA_BLACKLISTED`).

# Outputs
```
svaba/<pair>.svaba.somatic.indel.vcf
svaba/<pair>.svaba.somatic.indel.vcf.idx
svaba/<pair>.svaba.log
svaba/<pair>.svaba.somatic.sv.vcf        # produced by SvABA but not a make target
```
    Additional SvABA intermediate files (.bam, .txt) are retained inside the
    `svaba/` directory for troubleshooting.

# Usage
```
make svabaTN USE_CLUSTER=false   # run locally; omit to submit through qmake
```
    Override `SVABA_CORES` or `SVABA_MEM_CORE` on the command line if your queue
    has different resource limits.

# Post-processing
- Use `make merge_sv` / `make annotate_sv` to integrate SvABA outputs with other
  SV callers (GRIDSS, Manta).  Those targets look under `svaba/` for VCFs ending
  in `.svaba.somatic.indel.vcf`.
- When manual annotation is needed, SvABA’s upstream repository provides the
  R-based annotators referenced in the comments of `svabaTN.mk`.

# Troubleshooting
- Ensure BAMs are coordinate-sorted and indexed; SvABA fails fast if either file
  is missing an index.
- The blacklist (`SVABA_BLACKLISTED`) filters centromeres/telomeres; adjust if
  working on non-human genomes.
