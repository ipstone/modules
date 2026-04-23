# WGS Working Modules Merge Notes (2026-04-23)

## Overview
Merged improvements from four WGS-focused working branches into `ipstone_modules` master (`commit 295379b8`).  
These branches were developed over successive WGS projects on the lilac cluster (Powell VIP → CDH1 SV → alignment optimization → Shu WGS cohort).  
The goal was to consolidate all hard-won WGS fixes—alignment robustness, SV caller tuning, resource scaling, and QC metrics—into a single reproducible master branch that can be cloned and run directly on lilac.

## Source Branches (merged in reverse chronological order)

| Branch / Path | Focus | Key Contributions |
|---|---|---|
| `modules_jrflab_vip_wgs_15_032_Shu` | Latest WGS cohort (Shu) | Resource tuning for challenging samples, GATK interval splitting, improved wgs_metrics, queue support, cravat memory bump |
| `module_jrflab_vip_wgs.optimized_alignment` | Alignment robustness | Temp-file safety, samtools quickcheck integrity validation, samtools2 sort parallelization, job failure cleanup |
| `modules_jrflab_vip_wgs_WGS_CDH1SV` | SV calling for WGS | svaba parameter optimization, inclusion of svaba in merged SV calls, gatk multi-threading for WGS |
| `mdules_jrflab_Powell_vip/modules_jrflab` | Foundational WGS tweaks | BAM_SUFFIX generalization, removed hardcoded bam paths, alignment streamlining |

---

## Detailed Changes by Module

### 1. Alignment (`aligners/`)

#### `aligners/align.mk`
- **Walltime**: increased merge step from `24:00:00` → `72:00:00`  
  *Rationale*: large WGS BAM merges (30–60× coverage) routinely timed out on the 24h limit.
- **Robustness**: added `samtools quickcheck -v` loop before merge; on failure, removes corrupt inputs (`*.bam`, `*.bai`) so make can retry cleanly.
- **Atomic writes**: merge writes to `$@.tmp.$$$$` then `mv` into place. Prevents partially-written BAMs from being accepted as successful outputs.

#### `aligners/bwamemAligner.mk`
- **BAM_SUFFIX**: changed target from hardcoded `%.bwamem.sorted.filtered.bam` to `%.bwamem.$(BAM_SUFFIX)`.  
  *Rationale*: supports different BAM processing suffixes (e.g. `.sorted.bam` vs `.sorted.filtered.bam`) without editing the makefile.
- **Removed debug**: dropped `$(info BAM_SUFFIX is $(BAM_SUFFIX))` print statement.
- **Removed unprocessed_bam copy**: dropped `unprocessed_bam/%.bam` copy rule.  
  *Rationale*: redundant for WGS; saves disk space and I/O. If `MERGE_SPLIT_BAMS=true` is needed, `processBam.mk` already handles merging.

---

### 2. BAM Processing (`bam_tools/processBam.mk`)
This file received the most extensive overhaul, combining improvements from both the Shu and optimized_alignment branches.

#### Sorting (WGS-critical)
- **Replaced Picard SortSam with `samtools2` multi-threaded sort** for `%.sorted.bam`:
  ```make
  BAM_SORT_THREADS ?= 8
  BAM_SORT_MEM_PER_THREAD ?= 4G
  BAM_SORT_WALLTIME ?= 120:00:00
  ```
  *Rationale*: Picard SortSam is single-threaded and memory-hungry; `samtools sort -@ 8` is dramatically faster for 60–100 GB WGS BAMs.

#### Temp-file safety (atomic writes)
- Every major step now writes to a temporary file and moves on success:
  - `%.filtered.bam`, `%.markdup.bam`, `%.sorted.bam`
  - chromosome split realn/recal BAMs
  - merge steps (`%.realn.bam`, `%.recal.bam`)
- On failure, the temp file is removed and make exits with the original error code.  
  *Rationale*: prevents make from seeing a partially-written target and incorrectly marking it as up-to-date.

#### Integrity checks
- `%.bam.bai`: runs `samtools quickcheck -v` before indexing. If the BAM is corrupt, removes BAM + all index aliases so the job can be retried cleanly.

#### Resource increases for WGS
| Step | Before | After | Reason |
|---|---|---|---|
| `.bam.bai` | `w 7200` | `w 8640` (2.4h) | Large WGS BAM indexing |
| `.filtered.bam` | `w 7200` | `w 8640` | Filtering 100 GB BAMs |
| `.sorted.bam` | Picard 30G/30G | `samtools2` 8 threads, 6G/7G, 120h | Parallel sort for WGS |
| `.markdup.bam` | 36G/48G, 2h | 42G/52G, 2.4h | MarkDuplicates on WGS depth |
| `chr_realn.bam` | `w 7200` | `w 8640` | Per-chromosome realignment |
| `chr_recal.bam` | `w 7200` | `w 8640` | BQSR PrintReads per chr |

#### Merging split BAMs
- `unprocessed_bam/$1.bam` merge now also uses `quickcheck` + atomic temp file pattern.
- `bam-header` fix: corrected loop variable from `$$(^M)` (typo) to `$$^`.

---

### 3. Job Runner (`scripts/`)

#### `scripts/job.py`
- Added `_check_alignment_integrity()` method to base `Job` class.
- After any job finishes, if the output is `.bam` or `.cram`, runs `samtools quickcheck` (with retry logic).
- If quickcheck fails, the job is marked as failed even if the file is non-zero size.  
  *Rationale*: WGS pipelines were occasionally producing truncated BAMs that passed file-size checks but crashed downstream callers.

#### `scripts/run.py`
- **Queue support**: added `-q / --queue` argument. Passed through to SGE (`-q`), PBS (`-q`), and LSF (`-q`) submissions.  
  *Rationale*: lilac has dedicated queues (e.g. `cpuqueue`) for long-running WGS jobs.
- **Failed-output cleanup**: on non-zero exit status, removes the target file plus known sidecars (`.bai`, `.tbi`, `.idx`).  
  *Rationale*: prevents make from accepting a failed target as up-to-date on retry.

---

### 4. Germline Variant Calling (`variant_callers/gatk.mk`)

#### HaplotypeCaller interval splitting (from Shu branch)
- Added `GATK_SPLIT_INTERVALS ?= true` and `GATK_INTERVAL_SIZE ?= 25000000` (25 Mb).
- When enabled, each chromosome is split into 25 Mb windows; HaplotypeCaller runs on each window independently, then `CombineVariants` merges them.
- **Why**: tumor/normal HaplotypeCaller on whole chromosomes for 60× WGS routinely exceeded 72h walltime. Splitting into ~120 windows per genome keeps jobs well under the limit and parallelizes better across the cluster.

#### Configurable walltime
- Added `GATK_HC_WALLTIME ?= 72:00:00` used throughout all HaplotypeCaller rules.

#### CDH1SV vs Shu conflict resolution
- The CDH1SV branch had increased GATK to `-n 4 -s 4G -m 6G -w 168:00:00` with `-nct 4`.
- **Decision**: kept the Shu branch’s interval-splitting approach instead of just adding threads.  
  *Reason*: interval splitting provides better walltime guarantees and cluster throughput than simply adding `-nct 4`, which is deprecated in GATK3 and can be unstable.

---

### 5. Somatic Variant Calling (`variant_callers/somatic/`)

#### `lancet.mk`
- Walltime: `36:00:00` → `144:00:00` (WGS chromosomes take much longer).
- Merge memory: `4G/8G` → `8G/16G` for combining per-chromosome lancet VCFs.

#### `scalpel.mk`
- **Target-only mode** (default): reduced per-chunk memory from `8G/10G` → `5G/6G`.  
  *Rationale*: Scalpel was over-allocating memory; lowering it allows more chunks to run concurrently on the cluster without sacrificing speed.

#### `somaticIndels.mk`
- Merge step memory: `9G/12G` → `16G/24G`.  
  *Rationale*: merging 6 caller VCFs for WGS samples requires more RAM.

---

### 6. Structural Variant Callers (`sv_callers/`)

#### `gridss_tumor_normal.mk`
- **Cores**: `8` → `16`.
- **Memory**: added `GRIDSS_SOFT_MEM ?= 6G`, `GRIDSS_HARD_MEM ?= 10G`.
- **Queue**: added `GRIDSS_QUEUE ?= cpuqueue`.
- **Walltime**: `72:00:00` → `168:00:00` (7 days). WGS gridss assemblies can take days.
- **Filter step**: added configurable `GRIDSS_FILTER_*` variables (soft/hard mem, queue, walltime, threads, env).  
  *Rationale*: gridss somatic filter spawns numpy/BLAS threads that can deadlock on multi-core nodes; `GRIDSS_FILTER_ENV` pins threads to 1.
- **Cleanup bugfix**: corrected hardcoded sample name `FL001-101CD_FL001-101NL` → generic `$1_$2` in working-directory cleanup.
- **ulimit**: added `ulimit -c 0` to prevent gridss from dumping multi-GB core files on OOM kills.

#### `svaba_tumor_normal.mk`
- **Queue**: added `SVABA_QUEUE ?= cpuqueue`.
- **Walltime**: `144:00:00` → `120:00:00` (Shu branch) but parameterized via `SVABA_WALLTIME`.
- **Mate lookup**: `SVABA_MATE_LOOKUP_MIN ?= 100000` (was 100000 in Shu, 200000 in CDH1SV).
- **Max reads**: `SVABA_MAX_READS ?= 25000`.
- **Memory**: parameterized `SVABA_SOFT_MEM ?= 4G`, `SVABA_MEM_CORE ?= 6G`.
- **CDH1SV vs Shu conflict**: CDH1SV used `-s 8G -m 14G` and higher mate lookup (200000).  
  *Decision*: kept Shu’s softer defaults (4G/6G, 100000) as parameterized variables. Users can override per-project in `config.inc` or on the command line.

---

### 7. SV Merging (`vcf_tools/merge_sv.mk`)
- `SV_CALLERS`: `gridss manta` → `svaba manta`.  
  *Rationale*: CDH1SV project found svaba + manta gave the best WGS SV callset for that cohort. gridss calls are kept available but not merged by default.  
  *To revert*: override `SV_CALLERS = gridss manta` in your project config.

---

### 8. VCF Annotation (`vcf_tools/cravat_annotation.mk`)
- Added configurable memory:
  ```make
  CRAVAT_FILTER_MEM ?= 48G
  CRAVAT_SUMMARY_MEM ?= 48G
  ```
  *Rationale*: WGS samples with >50k variants crash the filter/summary steps at 12G.

---

### 9. WGS QC Metrics (`wgs_metrics.mk` + `scripts/wgs_metrics.R`)

#### `wgs_metrics.mk`
- Completely restructured from simple hardcoded Picard calls to a parameterized system:
  - `METRICS_JAVA`, `METRICS_PICARD_JAR`, `METRICS_COMMON_OPTS`
  - `DEFAULT_METRICS_*`, `OXOG_METRICS_*`, `WGS_METRICS_*`, `DUPLICATE_METRICS_*`
- **Toggleable metrics**:
  - `ENABLE_OXOG_METRICS ?= true`
  - `ENABLE_DUPLICATE_METRICS ?= true`  
    *Rationale*: duplicate metrics are useful default WGS QC output, and the workflow now reuses `metrics/<sample>.dup_metrics.txt` from alignment whenever available. It only falls back to a fresh `MarkDuplicates` metrics pass if no prior duplicate-metrics file exists.
- **Duplicate metrics**: switched from `CollectDuplicateMetrics` (deprecated) to `MarkDuplicates` with `OUTPUT=/dev/null`, with reuse of alignment-stage duplicate-metrics files when present.
- **Walltimes**: OxoG 48h, WGS 72h, Duplicates 72h (up from uniform 24h).

#### `scripts/wgs_metrics.R`
- Added `combine_metrics()` helper that handles missing columns across samples.  
  *Rationale*: different WGS samples occasionally have slightly different Picard metric columns (e.g. if a BAM lacks certain read groups). The old `do.call(rbind, metrics)` would crash with "numbers of columns do not match".
- Added `select_existing()` to safely drop `SAMPLE` / `READ_GROUP` columns only if they exist.

---

### 10. Top-Level `Makefile`
- `wgs_metrics` target now points to `modules/wgs_metrics.mk` (root-level) instead of `modules/qc/wgs_metrics.mk`.  
  *Rationale*: the root-level `wgs_metrics.mk` is the actively maintained, parameterized version.
- Added `SVABA_NUM_ATTEMPTS ?= 1` and set `NUM_ATTEMPTS` for the `svaba_tumor_normal` target. Supports automatic retry.
- The active top-level SvABA target is now `svaba_tumor_normal`. The legacy `svabaTN` module file remains in the repository for historical reference, but it is not wired into the current top-level `Makefile`.
- Kept ipstone-specific `hotspot_summary` and `viral_detection` targets in the top-level `Makefile` instead of dropping them during the WGS merge.

---

## Conflict Resolutions & Design Decisions

| Conflict | Options | Decision | Reasoning |
|---|---|---|---|
| GATK HaplotypeCaller parallelization | CDH1SV: `-nct 4` multi-thread per chr | Shu: split into 25 Mb intervals | Interval splitting scales better on cluster, avoids GATK3 `-nct` deprecation issues |
| svaba memory / mate lookup | CDH1SV: 8G/14G, 200000 mates | Shu: 4G/6G, 100000 mates | Kept Shu defaults as parameterized variables; CDH1SV values can be set per-project |
| gridss filter output | CDH1SV: `--fulloutput` + `--gc` | Shu: no `--fulloutput`, thread-env | Kept Shu’s env/thread controls for stability; `--fulloutput` can be re-added if needed |
| BAM sort method | ipstone: Picard SortSam | optimized_alignment: `samtools2` multi-thread | `samtools2` is faster and more memory-efficient for WGS; only change is in `%.sorted.bam` rule |
| SV merge callers | ipstone: gridss + manta | CDH1SV: svaba + manta | WGS experience showed svaba + manta combination works well; gridss calls remain available separately |
| wgs_metrics location | ipstone: `qc/wgs_metrics.mk` | Shu: root `wgs_metrics.mk` | Root-level version is newer and more configurable |

---

## Files Modified (16 total)

```
Makefile
aligners/align.mk
aligners/bwamemAligner.mk
bam_tools/processBam.mk
scripts/job.py
scripts/run.py
scripts/wgs_metrics.R
sv_callers/gridss_tumor_normal.mk
sv_callers/svaba_tumor_normal.mk
variant_callers/gatk.mk
variant_callers/somatic/lancet.mk
variant_callers/somatic/scalpel.mk
variant_callers/somatic/somaticIndels.mk
vcf_tools/cravat_annotation.mk
vcf_tools/merge_sv.mk
wgs_metrics.mk
```

---

## Compatibility & Validation Checklist

1. **Reference paths**: `GRIDSS_REF` still points to `/data/riazlab/lib/reference/b37_dmp/b37.fasta`. Confirm this exists on lilac compute nodes.
2. **Picard jar**: `wgs_metrics.mk` defaults to `$(JARDIR)/picard-2.8.2.jar`. Override `METRICS_PICARD_JAR` if your environment uses a different version.
3. **samtools2**: `processBam.mk` now calls `$(SAMTOOLS2)` for sorting. Ensure `SAMTOOLS2 ?= samtools` is defined (already in `config.inc`). If you have a newer samtools module, set `SAMTOOLS2` accordingly.
4. **Queue submission**: `run.py` now accepts `-q cpuqueue`. If your cluster uses a different queue name, export or pass the appropriate value.
5. **Gridss filter env**: if gridss somatic filter crashes with BLAS threading errors, confirm `GRIDSS_FILTER_ENV` is being applied.
6. **Test alignment**: run `make bwamem` on a small WGS sample; verify `.sorted.bam` is produced by `samtools sort` and that `.bai` indexing runs `quickcheck` first.
7. **Test wgs_metrics**: run `make wgs_metrics` on a subset; confirm `summary/wgs_metrics.txt` and `summary/duplicate_metrics.txt` are generated, preferably reusing alignment-stage `metrics/*.dup_metrics.txt` files when present.
8. **Test SV calling**: run `make svaba_tumor_normal` and `make gridss_tumor_normal` on one tumor-normal pair; verify VCFs appear in `vcf/`.

---

## Next Steps / Known Limitations

- `Makefile.inc` still uses `PICARD_MEM = 20G` and `PICARD_OPTS` from ipstone. The `wgs_metrics.mk` now overrides these locally; verify no other modules are affected.
- `config.inc` has a typo `PICAD_OPTS` (vs `PICARD_OPTS`) in the upstream jrflab branch. This was **not** merged because ipstone’s `Makefile.inc` already defines `PICARD_OPTS` correctly.
- `configure.py` in the Shu branch reverted to `yaml.load` without safe loader. ipstone’s version (with `yaml_load()` safe loader) was **retained** for security/compatibility.
- Future work: consider parameterizing `SURVIVOR` merge parameters (`MAX_DIST`, `NUM_CALLERS`, `MIN_SIZE`) per project for WGS vs exome differences.
