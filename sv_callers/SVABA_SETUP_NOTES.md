# SvABA setup — read before configuring or trusting any tumour/normal SV run

**Applies to:** svaba **2.0.0** (installed on lilac 2026-05-23) driven through
`jrflab/modules` `sv_callers/svaba_tumor_normal.mk`.
Written 2026-08-27 after an audit found both problems below in production output.

---

## 1. Check any existing output first — one command

`tovcf` writes germline records with **no** `SOMATIC` INFO flag. So a somatic
VCF that contains unflagged records was built from the wrong table:

```bash
p=<tumor>_<normal>
grep -v '^#' vcf/${p}.svaba_sv.vcf | grep -vc SOMATIC
```

| Result | Meaning |
|---|---|
| a large number | **contaminated** — germline calls are in your somatic VCF |
| 0, or a handful | correct |

Measured on this cohort's 76× pair:

| | records | without `SOMATIC` |
|---|---|---|
| before the fix | 17,720 | **16,131 (91%)** |
| after the fix | 1,557 | 4 (0.3%) |

**Anyone who ran this module between 2026-05-23 and 2026-08-27 has contaminated
somatic VCFs.** Repair is cheap — see §4. No re-alignment, no re-calling.

---

## 2. Defect A — `tovcf` must be given the somatic table

svaba 2.0.0 `postprocess` writes three breakpoint tables:

| File | Contents |
|---|---|
| `<id>.bps.sorted.dedup.txt.gz` | **all** breakpoints — somatic *and* germline |
| `<id>.bps.sorted.dedup.pass.txt.gz` | passing |
| `<id>.bps.sorted.dedup.pass.somatic.txt.gz` | passing **and somatic** ← use this |

`tovcf` converts whatever table it is handed and **applies no filtering of its
own**. The module was passing the combined table, so germline calls flowed into
`vcf/<pair>.svaba_sv.vcf` and into everything downstream — merged SV sets,
HRDetect, circos plots, SV counts.

It is easy to miss because the output *looks* fine: the records carry a
`SOMATIC` INFO flag, so the information needed to filter is present. Nothing in
the module ever acts on it.

```make
# wrong                                    # right
-i $1_$2.bps.sorted.dedup.txt.gz           -i $1_$2.bps.sorted.dedup.pass.somatic.txt.gz
```

## 3. Defect B — `wgs_blacklist_meres.bed` is an INCLUSION file

Despite the name, `$(HOME)/share/lib/resource_files/svaba/wgs_blacklist_meres.bed`
is the **genome minus centromere/telomere gaps** — a region list to analyse,
which svaba 1.1.0 took on `-k`.

Passing it to `--blacklist` in 2.0.0 **excludes** those regions instead, masking
~97% of the genome and producing near-empty output.

```make
-k $(SVABA_REGION)          # region restriction  <- wgs_blacklist_meres.bed
--blacklist $(SVABA_BLACKLIST)   # true exclusion list; empty by default
```

`SVABA_BLACKLIST` is empty by default on purpose: the blacklists bundled with
svaba are hg38 and chr-prefixed, so they are unusable on b37 projects. Do not
point it at the meres file.

---

## 4. Repairing existing runs

Only the `tovcf` step is re-run. The `.pass.somatic` table already sits beside
the combined one from the original run.

```bash
cd svaba
svaba tovcf -i <pair>.bps.sorted.dedup.pass.somatic.txt.gz \
            -b ../bam/<tumor>.bam -a <pair>
# writes <pair>.sv.vcf.gz and <pair>.indel.vcf.gz in the current directory
```

Then rebuild whatever consumed the old VCF — merged SV sets, HRDetect inputs,
counts, figures. In this project that changed SV counts materially for one
library and shifted an HRDetect probability from 0.508 to 0.314.

---

## 5. Setting up a new SvABA run — checklist

1. Confirm the module is the fixed version:
   `grep pass.somatic modules/sv_callers/svaba_tumor_normal.mk` — must match.
2. Confirm the region file goes to `-k`, not `--blacklist`:
   `grep -E '\-k |blacklist' modules/sv_callers/svaba_tumor_normal.mk`.
3. Expand the recipe before launching and read it:
   `make -Bn -f modules/sv_callers/svaba_tumor_normal.mk svaba/<pair>.sv.vcf.gz`
4. After the run, apply the §1 check to every pair.
5. Only then merge, count, or plot.

---

## 6. Provenance

| Item | Location |
|---|---|
| Fix commit | `modules_jrflab_vip_wgs`, branch `fix/svaba-2.0.0-somatic-tovcf`, `6e686f6d` |
| Exported patch + apply instructions | `identify_CDH1_SVs/patches/` |
| Root-cause analysis | `specs/04_audit_fix_round_2026-08-18.md` §S1 |
| Rebuild consequences | `identify_CDH1_SVs/docs/sv_set_rebuild_2026-08.md` |

The modules checkout is deliberately left **on the fix branch**. Checking out
`master` reverts the fix in the working tree and the next run silently produces
contaminated calls again.

Not yet pushed upstream. Contributing it needs a fork of `jrflab/modules` and a
pull request from that branch; any group running svaba 2.0.0 through this
module is affected.
