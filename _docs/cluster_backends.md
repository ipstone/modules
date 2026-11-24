# Cluster backends: choosing and configuring the scheduler

Rules in the `.mk` files request resources in a form that does not depend on
the scheduler:

```make
$(call RUN,-n 8 -s 4G -m 6G -w 24:00:00 -v $(SOME_ENV) -c,"command")
```

`RUN` (Makefile.inc) pipes the command to `scripts/run.py`, which builds a
`JobOptions` request and asks `job.select_backend()` for a backend. Each
backend in `scripts/job.py` turns the request into the arguments of one
scheduler and submits the job. Moving to a new scheduler or site needs
configuration changes only (`project_config.inc` or `config.inc`); the `.mk`
files do not change.

## 1. Choose the engine

Set `CLUSTER_ENGINE` in `project_config.yaml` (`cluster_engine: LSF`), which
`configure.py` writes to `project_config.inc`. The name is case-insensitive in
`run.py`; the Makefile checks accept upper or lower case.

| `CLUSTER_ENGINE` | Backend | Submission | Waits with | Use |
|---|---|---|---|---|
| `LSF` | `LSFBackend` | `bsub -K` | bsub -K | MSK lilac (current production) |
| `SLURM` | `SlurmBackend` | `sbatch --wait --parsable` | sbatch --wait | e.g. iris |
| `SGE` | `SGEBackend` | DRMAA (`drmaa_job.py`) | DRMAA wait | legacy |
| `PBS` / `torque` | `PBSBackend` | `qsub` | qstat polling | legacy |
| `local` / `none` | `LocalBackend` | runs on the current host | process | testing |

`USE_CLUSTER=false` (run.py `-l`) runs every job on the current host,
whatever the engine.

Request flags and what each backend does with them:

| RUN flag | Meaning | LSF | Slurm | SGE | PBS |
|---|---|---|---|---|---|
| `-n N` | cores, one host | `-n N -R "span[hosts=1]"` (if N>1) | `--nodes=1 --ntasks=1 --cpus-per-task=N` | `-pe smp N` (if N>1) | `-l nodes=1:ppn=N` |
| `-m X` | hard memory **per core** | `-M ceil(X/1e9)` (GB) | `--mem-per-cpu=ceil(X/MiB)M` | `h_vmem=X` | `-l mem=N*X` (total) |
| `-s X` | soft memory per core | `-R "rusage[mem=ceil(X/1e9)]"` | dropped | `virtual_free=X` | dropped |
| `-w T` | walltime `HH:MM:SS` or minutes | `-W HH:MM` (seconds dropped) | `--time=T` | not passed | `-l walltime=T` |
| `-q Q` / `CLUSTER_QUEUE` | queue / partition | `-q Q` | `-p Q` | `-q Q` | `-q Q` |
| `--internet` | needs internet | see section 4 | see section 4 | runs locally | runs locally |

Memory units: `human2bytes` reads `4G` as 4 GiB (4294967296 bytes). LSF
receives that value rounded up to decimal GB (`4G` becomes `-M 5`), as it
always has. Slurm receives the exact value in MiB (`4G` becomes
`--mem-per-cpu=4096M`), so a Slurm job gets slightly less memory than the
same rule on lilac. If a tool is close to its limit, raise `-m` in the rule.

## 2. Variables

Scheduler variables (Makefile.inc, all `?=` defaults, empty unless noted):

| Variable | Default | Effect |
|---|---|---|
| `CLUSTER_ENGINE` | `SGE` | backend name (section 1). Project yaml sets `LSF`. |
| `USE_CLUSTER` | `true` | `false` runs every job locally. |
| `CLUSTER_QUEUE` | empty | default queue/partition. A `-q` inside a rule's RUN call takes precedence (it comes later on the command line). |
| `CLUSTER_EXTRA_ARGS` | empty | appended to every submission: `--account=x --qos=y` (Slurm), `-P proj` (LSF). Split with shell rules for Slurm; appended as a string for LSF/SGE/PBS. |
| `CLUSTER_INTERNET_ARGS` | empty | Slurm only: arguments that place an `--internet` job on a node with internet access, e.g. `-p internet` or `--constraint=internet`. Appended after `CLUSTER_QUEUE`, so a `-p` here wins. |
| `DRMAA_LIBRARY_PATH` | per engine | exported only for SGE (needed), and for LSF and PBS with their previous values so the job environment on those sites does not change. Not set for Slurm or local. |

When `CLUSTER_QUEUE`, `CLUSTER_EXTRA_ARGS` and `CLUSTER_INTERNET_ARGS` are
empty, the `RUN` command line is identical to the one before this change.

Site variables (config.inc):

| Variable | Default | Effect |
|---|---|---|
| `SITE` | derived from `CLUSTER_ENGINE`: `PBS` gives `legacy_pbs`, `SGE` gives `legacy_sge`, anything else (LSF, Slurm) gives `msk_lilac` | selects the site block below. |
| `MYSQLDB_HOST`, `EMBL_MYSQLDB_HOST/PORT/USER/PW/DB` | from the site block | database hosts used by annotation steps; also select `SNVBOX_CONF` and `FATHMM_CONF` (`modules/db/*-$(MYSQLDB_HOST).*`). Now `?=`, so a project can override one value. |
| `SITE_TMPDIR` | `$(HOME)/share/data/$(USER)/tmp` | exported as `TMPDIR` (section 5). |

Site blocks defined now:

| `SITE` | MySQL host | EMBL port / db |
|---|---|---|
| `msk_lilac` | `swan` | 38493 / `homo_sapiens_core_75_37` |
| `legacy_sge` | `ika` | 38493 / `homo_sapiens_core_75_37` |
| `legacy_pbs` | `cpu-6-2` | 9992 / `homo_sapiens_core_85_37` |

Projects that set only `CLUSTER_ENGINE` get the same hosts as before. One
difference: a lower-case `lsf` or an unknown engine (e.g. `SLURM`) used to
leave the hosts empty and now gets the `msk_lilac` hosts. A Slurm site must
therefore set `SITE`.

## 3. Add a new site (example: iris, Slurm)

1. Add a block to the site section of `config.inc`:

   ```make
   ifeq ($(SITE),msk_iris)
   MYSQLDB_HOST ?= <iris db host>
   EMBL_MYSQLDB_HOST ?= <iris db host>
   EMBL_MYSQLDB_PORT ?= <port>
   EMBL_MYSQLDB_USER ?= embl
   EMBL_MYSQLDB_PW ?= embl
   EMBL_MYSQLDB_DB ?= homo_sapiens_core_75_37
   SITE_TMPDIR ?= /data1/riazn/tmp/$(USER)
   endif
   ```

   The block must come before the generic `SITE_TMPDIR ?=` line. Add
   `modules/db/snv_box-<host>.conf` and `fathmm_config-<host>.ini` if the
   annotation steps that use them will run.

2. In the project's `project_config.inc` (or yaml):

   ```make
   CLUSTER_ENGINE = SLURM
   SITE = msk_iris
   CLUSTER_QUEUE = cpu
   CLUSTER_EXTRA_ARGS = --account=<account>
   # optional: send --internet jobs to a node with internet access
   # CLUSTER_INTERNET_ARGS = -p <partition with internet>
   ```

3. Check the request without submitting: `make -n <target>` shows the RUN
   lines; `python modules/scripts/tests/test_backends.py` checks the argument
   builders.

4. Repoint the tool and environment paths (section 6). This is the main
   remaining work for a new site.

To add a new scheduler, write a `Backend` subclass in `scripts/job.py`
(`submit_args`, `make_job`, optionally `internet_runs_locally`), decorate it
with `@register_backend`, and add tests to `scripts/tests/test_backends.py`.

## 4. Jobs that need internet access (`--internet`)

The historical rule in run.py was `local or (internet and engine != 'lsf')`:
the comparison used the raw engine name and is case-sensitive. It is kept
unchanged:

- `-g lsf` (lower case): submitted with `-R "select[internet]"`.
- `-g LSF` (upper case, as the project yaml writes it): runs **locally on the
  submit host**. On lilac today the three `--internet` rules in
  `vcf_tools/vcfPostAnnotations.mk` (indel pathogenicity, MutationTaster,
  PROVEAN) therefore run on the host where make runs.
- Slurm: runs locally unless `CLUSTER_INTERNET_ARGS` is set; then submitted
  with those arguments appended.
- SGE, PBS: run locally.

## 5. TMPDIR must be shared with the compute nodes

run.py writes each job script with `NamedTemporaryFile` into `$TMPDIR` and
passes that path to `bsub`/`sbatch`/`qsub`. The compute node must be able to
read it, so `TMPDIR` must be on a shared file system, never node-local
`/tmp`. Makefile.inc exports `TMPDIR := $(SITE_TMPDIR)`
(default `$(HOME)/share/data/$(USER)/tmp`); java steps also use it via
`-Djava.io.tmpdir`. When make itself runs inside a batch job, the scheduler
may set a node-local `TMPDIR`; the Makefile value overrides it for the jobs
make starts.

## 6. Known limits

- **Rshell modules stay SGE-only.** Six legacy files set
  `SHELL = modules/scripts/Rshell` with `.SHELLFLAGS`, which bypasses `RUN`
  and the backends: `clonality/absoluteSeq.mk`, `copy_number/gistic.mk`,
  `copy_number/gisticFacets.mk`, `copy_number/exomeCNVLOHHeatmap.mk`,
  `ploidy/expands.mk`, `ploidy/bicseq.mk`.
- **Hardcoded site paths.** Counted on branch `consolidate/cluster-backends`
  (excluding `_docs/`): `$(HOME)/share` appears on 289 lines in 89 files
  (282 lines in 87 `.mk`/`.inc` files), `~/share` on 34 lines in 21 files,
  and `/data/riazlab` on 12 lines in 7 files. These tool, environment and
  reference paths need a site layer (for example `SITE_SHARE ?= $(HOME)/share`)
  before the pipeline runs unchanged on another cluster.
- `SGE_ROOT`, `SGE_NODES` and `PBS_NODES` are still exported/defined
  unconditionally in Makefile.inc. `--servers` (remote file-size check) is
  used by SGE and PBS only.
- `provean_query.py` (used by indel pathogenicity) now submits LSF and Slurm
  jobs through the backends; before, `cluster_mode LSF` stopped with
  "Invalid cluster mode". Each concurrent query installs its own signal
  handler, so on SIGTERM only the last Slurm query is cancelled.
- Slurm: the job id is read from `sbatch --parsable` output while `sbatch
  --wait` runs (`stdbuf -oL` is used when available). If the id is not known
  when a signal arrives, the job is cancelled by name (`scancel
  --name=<job name> --user=$USER`). `-d/--docker` is ignored.
- The equivalence test (`scripts/tests/test_backends.py`) checks argument
  strings against a copy of the pre-refactor code; it does not submit jobs.
  The first real Slurm run should be one small target with `make -n` first.
