# Name: svaba_tumor_normal

# Description
    Runs the current WGS SvABA structural-variant workflow implemented in
    `sv_callers/svaba_tumor_normal.mk`.

    This is the active SvABA target exposed by the top-level `Makefile` and the
    recommended SvABA entry point for lilac WGS tumor/normal projects.

# Inputs
    - `bam/<tumor>.bam`, `bam/<normal>.bam` (coordinate-sorted and indexed).
    - `SAMPLE_PAIRS` populated via `make config`.
    - SvABA executable and resources configured through:
      - `SVABA`
      - `SVABA_REF`
      - `SVABA_DBSNP`
      - `SVABA_BLACKLIST`
      - optional resource knobs such as `SVABA_CORES`, `SVABA_WALLTIME`,
        `SVABA_QUEUE`, `SVABA_MATE_LOOKUP_MIN`, `SVABA_MAX_READS`.

# Outputs
```
svaba/<tumor>_<normal>.svaba.somatic.sv.vcf
vcf/<tumor>_<normal>.svaba_sv.vcf
```
    SvABA also leaves its working files under `svaba/` for troubleshooting.

# Usage
```
make svaba_tumor_normal USE_CLUSTER=false
```
    Omit `USE_CLUSTER=false` to submit through qmake / the configured cluster
    backend.

    Useful overrides:

```
make svaba_tumor_normal SVABA_QUEUE=cpuqueue SVABA_CORES=16 SVABA_WALLTIME=168:00:00
```

# Notes
- `Makefile` sets `SVABA_NUM_ATTEMPTS ?= 1` for this target; increase it if you
  want automatic retries for unstable long-running samples.
- This workflow is tuned for WGS SV discovery and is the SvABA caller used by
  the current merged `merge_sv` defaults.
- If you need the historical indel-oriented SvABA wrapper, see
  `_docs/svabaTN.md` (legacy).
