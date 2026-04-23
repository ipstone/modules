# Name: svabaTN (legacy)

# Description
    Legacy SvABA wrapper implemented in `sv_callers/svabaTN.mk`.
    This target is **not exposed in the current top-level `Makefile`** and is
    kept mainly for historical reference / older projects that may still point
    at the legacy module file directly.

    For current WGS structural-variant calling, use:

```
make svaba_tumor_normal
```

    The active workflow is implemented in `sv_callers/svaba_tumor_normal.mk`
    and is the version documented for the merged WGS pipeline.

# Inputs
    - `bam/<tumor>.bam`, `bam/<normal>.bam` symlinks.
    - Legacy SvABA resources configured by `sv_callers/svabaTN.mk`
      (`SVABA_REF`, `SVABA_DBSNP`, `SVABA_BLACKLISTED`).

# Outputs
```
svaba/<pair>.svaba.somatic.indel.vcf
svaba/<pair>.svaba.somatic.indel.vcf.idx
svaba/<pair>.svaba.log
svaba/<pair>.svaba.somatic.sv.vcf        # SvABA also produces an SV VCF
```

# Current recommendation
- Prefer `make svaba_tumor_normal` for current WGS work.
- Prefer `vcf/<pair>.svaba_sv.vcf` from the active workflow when integrating
  with `make merge_sv`.

# Legacy usage
If you intentionally need the historical module behavior, invoke the module
makefile directly:

```
make -f modules/sv_callers/svabaTN.mk svabaTN USE_CLUSTER=false
```

# Notes
- This legacy module uses older hardcoded defaults and predates the queue-aware,
  parameterized WGS settings added in `svaba_tumor_normal.mk`.
- The blacklist variable name here is `SVABA_BLACKLISTED`; the current workflow
  uses `SVABA_BLACKLIST`.
- If you are unsure which SvABA workflow to use, use `svaba_tumor_normal`.
