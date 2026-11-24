#!/usr/bin/env python
""" Equivalence test for the scheduler backends in scripts/job.py.

Part 1 (always): rebuilds the submission arguments with a verbatim copy of the
engine dispatch of scripts/run.py before the backend refactor (reference_args)
and asserts the new backends give identical strings for LSF, SGE and PBS over
a grid of flag combinations, including which jobs run locally.
Part 2 (always): checks the Slurm sbatch argument list.
Part 3 (only when BACKEND_TEST_FAKE_SCHEDULER=1): runs the old run.py (given in
BACKEND_TEST_OLD_RUN_PY) and the new run.py end to end with fake bsub/sbatch/
scancel programs on PATH, and checks the recorded command lines and the
scancel-on-SIGTERM path. BACKEND_TEST_OLD_SCRIPTS names a directory with the
pre-refactor run.py and job.py, for example from
`git show consolidate/upstream-merge:scripts/run.py`. Writes only to a
temporary directory.

No external dependencies; Python 2.7 and 3 compatible.
usage: python scripts/tests/test_backends.py   (from the modules directory)
"""
from __future__ import print_function

import itertools
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)

import job  # noqa: E402

N_PASS = [0]
N_FAIL = [0]


def check(cond, msg):
    if cond:
        N_PASS[0] += 1
    else:
        N_FAIL[0] += 1
        print("FAIL: " + msg)


def reference_args(args, job_name, pwd):
    """ copy of scripts/run.py:122-175 at consolidate/upstream-merge (e4f1c224),
    with the Job constructors replaced by returning (kind, qsub_args) """
    cluster_engine = args.cluster_engine.lower()
    total_hard_mem = args.num_cores * job.human2bytes(args.hard_memory)
    if args.local or (args.internet and args.cluster_engine != 'lsf'):
        return ('local', None)
    elif cluster_engine == 'sge':
        qsub_args = "-V -wd {pwd} -now n -notify -b n -S {shell}".format(pwd=pwd, shell=args.shell)
        if args.queue is not None:
            qsub_args += " -q {}".format(args.queue)
        if job_name is not None:
            qsub_args += " -N {}".format(job_name)
        if args.log_file is not None:
            qsub_args += " -j y -o {}".format(args.log_file)
        if args.num_cores > 1:
            qsub_args += " -pe {penv} {num_cores}".format(penv=args.sge_parallel_env,
                                                          num_cores=args.num_cores)
        qsub_args += " -l virtual_free={soft_mem},h_vmem={hard_mem}".format(soft_mem=args.soft_memory,
                                                                            hard_mem=args.hard_memory)
        return ('sge', qsub_args)
    elif cluster_engine == 'pbs':
        qsub_args = "-d {pwd} -S {shell}".format(pwd=pwd, shell=args.shell)
        if args.queue is not None:
            qsub_args += " -q {}".format(args.queue)
        if job_name is not None:
            qsub_args += " -N {}".format(job_name)
        if args.log_file is not None:
            qsub_args += " -j oe -o {}".format(args.log_file)
        qsub_args += " -l nodes=1:ppn={num_cores}".format(num_cores=args.num_cores)
        if args.docker:
            qsub_args += ":docker"
        qsub_args += " -l walltime={walltime} -l mem={total_mem}".format(walltime=args.walltime,
                                                                         total_mem=total_hard_mem)
        return ('pbs', qsub_args)
    elif cluster_engine == 'lsf':
        qsub_args = "-cwd {pwd} -L {shell}".format(pwd=pwd, shell=args.shell)
        if args.queue is not None:
            qsub_args += " -q {}".format(args.queue)
        if job_name is not None:
            qsub_args += " -J {}".format(job_name)
        if args.log_file is not None:
            qsub_args += " -o {}".format(args.log_file)
        if args.internet:
            qsub_args += ' -R "select[internet]"'
        if args.num_cores > 1:
            qsub_args += ' -n {num_cores} -R "span[hosts=1]"'.format(num_cores=args.num_cores)
        hard_mem_gb = int(math.ceil(job.human2bytes(args.hard_memory) / 1000000000.0))
        soft_mem_gb = int(math.ceil(job.human2bytes(args.soft_memory) / 1000000000.0))
        walltime = re.sub(r'(\d+):(\d+):(\d+)', r'\g<1>:\g<2>', args.walltime)
        qsub_args += ' -M {hard_mem_gb} -R "rusage[mem={soft_mem_gb}]" -W {walltime}'.format(
            hard_mem_gb=hard_mem_gb, soft_mem_gb=soft_mem_gb, walltime=walltime)
        return ('lsf', qsub_args)
    else:
        raise ValueError("invalid cluster engine. supported engines are sge, pbs, and lsf")


class Args(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


def new_args(a, job_name, pwd):
    opts = job.JobOptions(engine=a.cluster_engine, local=a.local, internet=a.internet,
                          docker=a.docker, num_cores=a.num_cores,
                          soft_memory=a.soft_memory, hard_memory=a.hard_memory,
                          walltime=a.walltime, queue=a.queue, job_name=job_name,
                          log_file=a.log_file, out_file=None, shell=a.shell, cwd=pwd,
                          servers=None, sge_parallel_env=a.sge_parallel_env)
    backend = job.select_backend(opts)
    return (backend.name, backend.submit_args(opts))


MEMS = ['1G', '1.5G', '2G', '3.5G', '4G', '6G', '12G', '24G', '128G', '500M', '1024M']
WALLTIMES = ['6:00:00', '24:00:00', '72:00:00', '256:00:00', '1:00:00', '7200', '8640', '00:30:00']
CORES = [1, 2, 4, 8, 16]


def test_equivalence():
    pwd = '/data/riazlab/projects/x'
    grid = itertools.product(['lsf', 'LSF', 'Lsf', 'sge', 'SGE', 'pbs', 'PBS'],
                             [False, True],          # local
                             [False, True],          # internet
                             [False, True],          # docker
                             CORES,
                             ['1G', '4G', '1.5G'],   # soft
                             MEMS,                   # hard
                             WALLTIMES,
                             [None, 'cpuqueue'],
                             [None, 'proj_target.bam'],
                             [None, '/p/log/x.log'],
                             ['/bin/bash', None])
    n = 0
    for (eng, local, inet, docker, cores, soft, hard, wall, queue, jname, log, shell) in grid:
        # thin the grid deterministically: full product is ~2.4M combinations
        n += 1
        if n % 7 != 0 and not (eng in ('lsf', 'LSF') and n % 3 == 0):
            continue
        a = Args(cluster_engine=eng, local=local, internet=inet, docker=docker,
                 num_cores=cores, soft_memory=soft, hard_memory=hard, walltime=wall,
                 queue=queue, log_file=log, shell=shell, sge_parallel_env='smp')
        ref = reference_args(a, jname, pwd)
        new = new_args(a, jname, pwd)
        check(ref == new, "{} -> ref {!r} != new {!r}".format(a.__dict__, ref, new))

    # an unknown engine still raises unless the job runs locally
    for local, inet, expect_local in [(True, False, True), (False, True, True), (False, False, False)]:
        a = Args(cluster_engine='bogus', local=local, internet=inet, docker=False, num_cores=1,
                 soft_memory='1G', hard_memory='1G', walltime='6:00:00', queue=None,
                 log_file=None, shell='/bin/bash', sge_parallel_env='smp')
        try:
            ref = reference_args(a, None, pwd)
        except ValueError:
            ref = 'error'
        try:
            new = new_args(a, None, pwd)
        except ValueError:
            new = 'error'
        check(ref == new, "unknown engine local={} internet={}: {!r} != {!r}".format(local, inet, ref, new))

    # empty CLUSTER_EXTRA_ARGS must not change LSF args; non-empty is appended
    opts = job.JobOptions(engine='LSF', num_cores=4, hard_memory='4G', soft_memory='2G',
                          walltime='24:00:00', cwd=pwd, extra_args='')
    base = job.get_backend('LSF').submit_args(opts)
    check(base == '-cwd {} -L /bin/bash -n 4 -R "span[hosts=1]" -M 5 -R "rusage[mem=3]" -W 24:00'.format(pwd),
          "LSF literal: " + base)
    opts.extra_args = '-P myproj'
    check(job.get_backend('lsf').submit_args(opts) == base + ' -P myproj', "LSF extra args")


def test_registry():
    for name in ['lsf', 'LSF', 'Slurm', 'SLURM', 'slurm', 'sge', 'Sge', 'pbs', 'torque', 'local', 'NONE']:
        try:
            b = job.get_backend(name)
            check(b.name == name.lower() or name.lower() in b.aliases, "registry " + name)
        except ValueError:
            check(False, "registry lookup failed for " + name)
    try:
        job.get_backend('htcondor')
        check(False, "unknown engine accepted")
    except ValueError:
        check(True, "")


def test_slurm():
    pwd = '/data1/riazn/projects/x'
    b = job.get_backend('SLURM')
    opts = job.JobOptions(engine='SLURM', num_cores=8, hard_memory='3G', soft_memory='2G',
                          walltime='24:00:00', queue='cpu', job_name='proj_a.bam',
                          log_file='/p/log/a.bam.log', cwd=pwd,
                          extra_args="--account=riaz --qos='normal'")
    expect = ['--wait', '--parsable', '--nodes=1', '--ntasks=1', '--cpus-per-task=8',
              '--mem-per-cpu=3072M', '--time=24:00:00', '-p', 'cpu', '-J', 'proj_a.bam',
              '-o', '/p/log/a.bam.log', '--chdir=' + pwd, '--account=riaz', '--qos=normal']
    got = b.submit_args(opts)
    check(got == expect, "slurm full: {!r}".format(got))

    opts = job.JobOptions(engine='slurm', cwd=pwd)
    got = b.submit_args(opts)
    check(got == ['--wait', '--parsable', '--nodes=1', '--ntasks=1', '--cpus-per-task=1',
                  '--mem-per-cpu=1024M', '--time=6:00:00', '--chdir=' + pwd],
          "slurm defaults: {!r}".format(got))

    # memory is per core and rounded up to MiB; soft memory never appears
    for mem, mb in [('1.5G', 1536), ('1.2G', 1229), ('500M', 500), ('128G', 131072), ('2.8G', 2868)]:
        opts = job.JobOptions(engine='slurm', hard_memory=mem, soft_memory='99G', num_cores=4, cwd=pwd)
        got = b.submit_args(opts)
        check('--mem-per-cpu={}M'.format(mb) in got, "slurm mem {}: {!r}".format(mem, got))
        check(not [x for x in got if '99' in x], "slurm soft mem leaked: {!r}".format(got))
    # minutes-only walltime (used by several .mk files, e.g. -w 7200) passes through
    opts = job.JobOptions(engine='slurm', walltime='7200', cwd=pwd)
    check('--time=7200' in b.submit_args(opts), "slurm minutes walltime")

    # internet: local unless CLUSTER_INTERNET_ARGS is set
    opts = job.JobOptions(engine='slurm', internet=True, cwd=pwd)
    check(job.select_backend(opts).name == 'local', "slurm internet without args runs locally")
    opts = job.JobOptions(engine='slurm', internet=True, cwd=pwd, internet_args='-p internet')
    sel = job.select_backend(opts)
    check(sel.name == 'slurm', "slurm internet with args submits")
    check(sel.submit_args(opts)[-2:] == ['-p', 'internet'], "slurm internet args appended")
    opts = job.JobOptions(engine='slurm', internet=False, cwd=pwd, internet_args='-p internet')
    check('internet' not in ' '.join(b.submit_args(opts)), "internet args only for internet jobs")


###############################################################################
# Part 3: end-to-end with fake schedulers
###############################################################################

FAKE_BSUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$FAKE_LOG"
exit 0
"""

FAKE_SBATCH = """#!/bin/sh
printf 'sbatch %s\\n' "$*" >> "$FAKE_LOG"
echo 4242
if [ -n "$FAKE_SBATCH_SLEEP" ]; then
  i=0
  while [ $i -lt "$FAKE_SBATCH_SLEEP" ]; do
    [ -e "$FAKE_DIR/cancelled" ] && exit 1
    sleep 1; i=$((i+1))
  done
fi
exit 0
"""

FAKE_SCANCEL = """#!/bin/sh
printf 'scancel %s\\n' "$*" >> "$FAKE_LOG"
touch "$FAKE_DIR/cancelled"
"""


def _write_exe(path, text):
    with open(path, 'w') as f:
        f.write(text)
    os.chmod(path, 0o755)


def _run(cmd, env, stdin_text='true'):
    import subprocess
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, env=env, universal_newlines=True)
    p.communicate(stdin_text)
    return p.returncode


def test_end_to_end():
    import shutil
    import signal
    import subprocess
    import tempfile
    import time
    old_scripts = os.environ.get('BACKEND_TEST_OLD_SCRIPTS')
    tmp = tempfile.mkdtemp(prefix='backend_test_')
    try:
        bindir = os.path.join(tmp, 'bin')
        os.mkdir(bindir)
        _write_exe(os.path.join(bindir, 'bsub'), FAKE_BSUB)
        _write_exe(os.path.join(bindir, 'sbatch'), FAKE_SBATCH)
        _write_exe(os.path.join(bindir, 'scancel'), FAKE_SCANCEL)
        env = dict(os.environ)
        env['PATH'] = bindir + os.pathsep + env['PATH']
        env['FAKE_DIR'] = tmp
        env['TMPDIR'] = tmp
        new_run = os.path.join(SCRIPTS, 'run.py')

        if old_scripts:
            old_dir = os.path.join(tmp, 'old')
            os.mkdir(old_dir)
            shutil.copy(os.path.join(old_scripts, 'run.py'), os.path.join(old_dir, 'run.py'))
            shutil.copy(os.path.join(old_scripts, 'job.py'), os.path.join(old_dir, 'job.py'))
            cases = [
                ['-g', 'lsf', '-n', '8', '-s', '4G', '-m', '6G', '-w', '72:00:00', '-q', 'cpuqueue', '-N', 'x'],
                ['-g', 'LSF', '-n', '1', '-s', '1.5G', '-m', '3.5G', '-w', '7200', '-p', 'proj'],
                ['-g', 'lsf', '--internet', '-s', '2G', '-m', '5G', '-p', 'proj'],
                ['-g', 'LSF', '-n', '16', '-s', '5G', '-m', '6G', '-N', 'scalpel', '-p', 'p'],
            ]
            for i, case in enumerate(cases):
                logs = []
                for run_py in (os.path.join(old_dir, 'run.py'), new_run):
                    env['FAKE_LOG'] = os.path.join(tmp, 'log{}'.format(i))
                    if os.path.exists(env['FAKE_LOG']):
                        os.remove(env['FAKE_LOG'])
                    cmd = [sys.executable, run_py, '-o', os.path.join(tmp, 'out', 'x.bam'),
                           '--log_file', os.path.join(tmp, 'log', 'x.log'), '-S', '/bin/bash'] + case
                    _run(cmd, env)
                    with open(env['FAKE_LOG']) as f:
                        # script file name differs between runs; compare the args only
                        logs.append(re.sub(r'\S+\.sh$', 'SCRIPT', f.read().strip()))
                check(logs[0] == logs[1] and logs[0] != '',
                      "end-to-end bsub case {}: old {!r} new {!r}".format(i, logs[0], logs[1]))

        # slurm: sbatch is called with the expected list, and SIGTERM -> scancel <id>
        env['FAKE_LOG'] = os.path.join(tmp, 'slurm.log')
        env['FAKE_SBATCH_SLEEP'] = '30'
        cmd = [sys.executable, new_run, '-g', 'SLURM', '-n', '2', '-m', '3G', '-w', '1:00:00',
               '-N', 'job1', '--log_file', os.path.join(tmp, 'log', 's.log')]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, env=env, universal_newlines=True)
        p.stdin.write('true')
        p.stdin.close()
        time.sleep(3)
        p.send_signal(signal.SIGTERM)
        deadline = time.time() + 60
        while p.poll() is None and time.time() < deadline:
            time.sleep(1)
        rc = p.poll()
        if rc is None:
            p.kill()
        with open(env['FAKE_LOG']) as f:
            lines = f.read().splitlines()
        check(rc == 1, "slurm run.py exit status after SIGTERM: {}".format(rc))
        check(len(lines) >= 2 and lines[0].startswith('sbatch --wait --parsable --nodes=1 --ntasks=1 '
                                                       '--cpus-per-task=2 --mem-per-cpu=3072M '
                                                       '--time=1:00:00 -J job1 -o '),
              "slurm sbatch line: {!r}".format(lines))
        check('scancel 4242' in lines, "scancel by job id: {!r}".format(lines))
    finally:
        shutil.rmtree(tmp)


if __name__ == '__main__':
    print("python {}".format(sys.version.split()[0]))
    test_equivalence()
    test_registry()
    test_slurm()
    if os.environ.get('BACKEND_TEST_FAKE_SCHEDULER') == '1':
        test_end_to_end()
    else:
        print("skipping end-to-end test (set BACKEND_TEST_FAKE_SCHEDULER=1)")
    print("passed: {}  failed: {}".format(N_PASS[0], N_FAIL[0]))
    sys.exit(1 if N_FAIL[0] else 0)
