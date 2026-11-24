from abc import ABCMeta, abstractmethod
import os
import re
import datetime
import sys
import signal
import tempfile
import random
import time
import subprocess
import math
import shlex
import threading

DEVNULL = open(os.devnull, 'wb')


def time2secs(s):
    x = time.strptime(s, '%H:%M:%S')
    return datetime.timedelta(hours=x.tm_hour,
                              minutes=x.tm_min,
                              seconds=x.tm_sec).total_seconds()


def secs2time(s):
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def human2bytes(s):
    """
    >>> human2bytes('1M')
    1048576
    >>> human2bytes('1G')
    1073741824
    """
    symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    num, letter = re.match(r"([0-9.]+)([A-Za-z])", s).group(1, 2)
    letter = letter.upper()
    assert letter in symbols
    num = float(num)
    prefix = {symbols[0]: 1}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])


def bytes2human(n, format="%(value)i%(symbol)s"):
    """
    >>> bytes2human(10000)
    '9K'
    >>> bytes2human(100001221)
    '95M'
    """
    symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)


class Job:
    __metaclass__ = ABCMeta

    _kill_now = False

    def __init__(self, out_file=None):
        self.out_file = out_file

    @abstractmethod
    def check_file(self, max_retry=10):
        pass

    @abstractmethod
    def run_job(self):
        pass

    @abstractmethod
    def wait(self):
        pass

    @abstractmethod
    def is_finished(self):
        pass

    def _local_check_file(self, max_retry=10):
        for attempt in range(max_retry):
            try:
                local_file_size = int(
                    subprocess.check_output('stat -c%s "{}"'.format(
                        os.path.abspath(self.out_file)), stderr=DEVNULL, shell=True).strip())
                return local_file_size
            except:
                sys.stderr.write("Unable to stat {} locally\n".format(os.path.abspath(self.out_file)))
                time.sleep(10)
            else:
                sys.stderr.write("max retries for local file size check\n")
                return 0
            if self._kill_now:
                return 0

    def _check_alignment_integrity(self, max_retry=3):
        """For BAM/CRAM outputs, run quick integrity checks."""
        if self.out_file is None:
            return True

        lower = self.out_file.lower()
        if not (lower.endswith('.bam') or lower.endswith('.cram')):
            return True

        out_path = os.path.abspath(self.out_file)
        for attempt in range(max_retry):
            try:
                subprocess.check_output(
                    'samtools quickcheck "{}"'.format(out_path),
                    stderr=DEVNULL,
                    shell=True)
                return True
            except subprocess.CalledProcessError as e:
                # If samtools is not available, preserve previous behavior.
                if e.returncode == 127:
                    sys.stderr.write("samtools not found; skipping BAM integrity check\n")
                    return True
                sys.stderr.write("samtools quickcheck failed for {}\n".format(out_path))
                time.sleep(5)
            except:
                sys.stderr.write("failed to run samtools quickcheck for {}\n".format(out_path))
                time.sleep(5)

            if self._kill_now:
                return False
        return False


class LocalJob(Job):

    def __init__(self, job_script, shell=None, out_file=None, log_file=None):
        Job.__init__(self, out_file)
        self.job_script = job_script
        self.log_file = log_file
        self.retval = None
        self.shell = shell

    def run_job(self):
        job_script_file = tempfile.NamedTemporaryFile(mode='w',
                                                      suffix='.sh', delete=False)
        job_script_file.write(self.job_script)
        job_script_file.close()
        os.chmod(job_script_file.name, 0o555)
        with open(self.log_file, 'w') as err:
            self.process = subprocess.Popen([self.shell, job_script_file.name],
                                            stderr=err, stdout=err, shell=False)

    def wait(self):
        self.retval = self.process.wait()
        return self.retval

    def is_finished(self):
        return self.retval is not None and self.retval == 0

    def check_file(self, max_retry=10):
        time.sleep(10)
        if self.out_file is None:
            return True
        local_file_size = super(LocalJob, self)._local_check_file(max_retry)
        if local_file_size == 0:
            return False
        if not super(LocalJob, self)._check_alignment_integrity():
            return False
        return True


class ClusterJob(Job):
    __metaclass__ = ABCMeta

    def __init__(self, out_file=None, remote_check_servers=None):
        Job.__init__(self, out_file)
        self.remote_check_servers = remote_check_servers
        signal.signal(signal.SIGINT, self.__exit_gracefully)
        signal.signal(signal.SIGTERM, self.__exit_gracefully)

    def check_file(self, max_retry=10):
        """ checks the file size of file f on remote servers and returns True
        if it matches local file size and also local file size > 0
        """
        time.sleep(10)
        if self.out_file is None:
            return True
        local_file_size = super(ClusterJob, self)._local_check_file(max_retry)
        if local_file_size == 0:
            return False
        if self.remote_check_servers is not None:
            for server in self.remote_check_servers:
                if not self._remote_check_file(local_file_size, server,
                                               max_retry):
                    return False
        return local_file_size > 0

    def _remote_check_file(self, local_file_size, server, max_retry):
        for attempt in range(max_retry):
            try:
                remote_file_size = int(subprocess.
                                       check_output('ssh {} stat -c%s "{}"'.
                                                    format(server, os.path.abspath(self.out_file)),
                                                    stderr=DEVNULL, shell=True).strip())
                if remote_file_size != local_file_size:
                    raise ValueError(
                        "{}: remote file size != local file size: {} != {}"
                        .format(server,
                                remote_file_size,
                                local_file_size))
                break
            except ValueError as e:
                sys.stderr.write(e + "\n")
                time.sleep(10)
            except:
                sys.stderr.write("{}: failed remote file size check\n"
                                 .format(server))
                time.sleep(10)
            else:
                sys.stderr.write("max connection retries for "
                                 "remote file size check\n")
                return False
            if self._kill_now:
                return False
        return True

    def __exit_gracefully(self, signum, frame):
        print("received interrupt")
        self._kill_now = True

    @abstractmethod
    def run_job(self):
        pass

    @abstractmethod
    def wait(self):
        pass


class LSFJob(ClusterJob):

    def __init__(self, job_script, qsub_args='', out_file=None,
                 remote_check_servers=None):
        ClusterJob.__init__(self, out_file, remote_check_servers)
        self.job_script = job_script
        if qsub_args is not None:
            self.qsub_args = qsub_args
        else:
            self.qsub_args = ''

    def run_job(self):
        """ qsub job
        """
        self.job_script_file = tempfile.NamedTemporaryFile(mode='w',
                                                           suffix='.sh',
                                                           delete=False)
        self.job_script_file.write(self.job_script)
        self.job_script_file.close()
        os.chmod(self.job_script_file.name, 0o555)

        cmd = "bsub -K {args} {script}".format(args=self.qsub_args, script=self.job_script_file.name)
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    def wait(self):
        self.retval = self.process.wait()
        return self.retval

    def is_finished(self):
        return self.retval is not None and self.retval == 0


class PBSJob(ClusterJob):

    def __init__(self, job_script, qsub_args='', out_file=None,
                 poll_interval=10, remote_check_servers=None):
        ClusterJob.__init__(self, out_file, remote_check_servers)
        self.poll_interval = poll_interval
        self.job_script = job_script
        if qsub_args is not None:
            self.qsub_args = qsub_args
        else:
            self.qsub_args = ''

    def run_job(self):
        """ qsub job
        """
        self.job_script_file = tempfile.NamedTemporaryFile(mode='w',
                                                           suffix='.sh',
                                                           delete=False)
        self.job_script_file.write(self.job_script)
        self.job_script_file.close()
        os.chmod(self.job_script_file.name, 0o555)

        cmd = "qsub"
        cmd += " " + self.qsub_args
        cmd += " " + self.job_script_file.name
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        proc.wait()
        if proc.returncode != 0:
            raise Exception('unable to qsub job: {}'.format(cmd))
        self.job_id = proc.stdout.read().rstrip()
        self.update_qstat()

    def update_qstat(self):
        """ update the job state using qstat
        """
        self.qstat = {}
        proc = subprocess.Popen(['qstat', '-f', self.job_id], stdout=subprocess.PIPE)
        proc.wait()
        job_id_line = proc.stdout.readline().strip()
        if proc.returncode != 0 or self.job_id not in job_id_line:
            raise Exception('unable to qstat job id: {}'.format(self.job_id))
        self.qstat = self._parse_qstat(proc.stdout)

    def _parse_qstat(self, f):
        qstat = {}
        while True:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            mo = re.search(r'([^=]+) = (.+)', line)
            if not mo:
                continue
            k = mo.group(1)
            v = mo.group(2)
            while line.endswith(','):
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                v += line
            if v.isdigit():
                qstat[k] = int(v)
            else:
                qstat[k] = v
        return qstat

    def wait(self):
        """ wait for job to finish and return qstat exit_status
        """
        while True:
            self.update_qstat()
            if self.qstat['job_state'] == "C":
                break
            if self.qstat['job_state'] == "H" or self.qstat['job_state'] == "S":
                raise Exception('job halted')
            time.sleep(random.randint(self.poll_interval, self.poll_interval + 20))
            if self._kill_now:
                sys.stderr.write("registering job for deletion\n")
                subprocess.Popen("qdel {}".format(self.job_id), shell=True)
                self.update_qstat()
                break
        if 'exit_status' in self.qstat:
            return self.qstat['exit_status']
        else:
            return 99

    def is_finished(self):
        return self.qstat is not None and 'exit_status' in self.qstat and \
            self.qstat['exit_status'] == 0 and not self._kill_now

    def hit_mem_limit(self):
        """ True if mem limit was hit
        """
        try:
            mem_used = human2bytes(self.qstat['resources_used.mem'])
            mem_alloc = human2bytes(self.qstat['Resource_List.mem'])
            return mem_used + human2bytes('100M') > mem_alloc
        except:
            return False

    def hit_walltime_limit(self):
        """ True if walltime limit hit
        """
        try:
            walltime_used = time2secs(self.qstat['resources_used.walltime'])
            walltime_alloc = time2secs(self.qstat['Resource_List.walltime'])
            return walltime_used + 5 > walltime_alloc
        except:
            return False

    def restart(self, resource_multiplier):
        """ restart with higher reqs if req'd
        """
        mem = human2bytes(self.qstat['Resource_List.mem'])
        walltime = self.qstat['Resource_List.walltime']
        if self.hit_walltime_limit():
            walltime_secs = time2secs(walltime) * resource_multiplier
            walltime = secs2time(walltime_secs)
            sys.stderr.write("increased walltime to {}\n".format(walltime))
        if self.hit_mem_limit():
            mem = int(mem * resource_multiplier)
            sys.stderr.write("increased mem to {}\n".format(bytes2human(mem)))

        if self.qsub_args is not None and self.qsub_args.find('-l mem') != -1:
            self.qsub_args = re.sub(r'-l mem=(\S+)', '-l mem={}'.format(mem), self.qsub_args)
        else:
            self.qsub_args += ' -l mem={}'.format(mem)

        if self.qsub_args is not None and self.qsub_args.find('-l walltime') != -1:
            self.qsub_args = re.sub(r'-l walltime=(\S+)', '-l walltime={}'.format(walltime), self.qsub_args)
        else:
            self.qsub_args += ' -l walltime={}'.format(walltime)

        self.run_job()


class SlurmJob(ClusterJob):
    """ submit with `sbatch --wait` and block until the job ends.

    sbatch_args is a list of arguments (no shell parsing). On SIGINT/SIGTERM
    the job is cancelled with scancel so that a retry by qmake does not leave
    an orphan job running on the cluster.
    """

    def __init__(self, job_script, sbatch_args=None, out_file=None,
                 job_name=None, poll_interval=5, cancel_grace=120):
        ClusterJob.__init__(self, out_file, None)
        self.job_script = job_script
        self.sbatch_args = list(sbatch_args) if sbatch_args else []
        self.job_name = job_name
        self.poll_interval = poll_interval
        self.cancel_grace = cancel_grace
        self.job_id = None
        self.retval = None
        self.process = None
        self._cancelled = False
        signal.signal(signal.SIGINT, self._slurm_exit_gracefully)
        signal.signal(signal.SIGTERM, self._slurm_exit_gracefully)

    def command(self, script_path):
        cmd = ['sbatch'] + self.sbatch_args + [script_path]
        # sbatch prints the job id before it waits; line-buffer its stdout so
        # the id reaches us while the job runs (needed for scancel)
        stdbuf = _find_executable('stdbuf')
        if stdbuf is not None:
            cmd = [stdbuf, '-oL'] + cmd
        return cmd

    def run_job(self):
        self.job_script_file = tempfile.NamedTemporaryFile(mode='w',
                                                           suffix='.sh',
                                                           delete=False)
        self.job_script_file.write(self.job_script)
        self.job_script_file.close()
        os.chmod(self.job_script_file.name, 0o555)

        self.process = subprocess.Popen(self.command(self.job_script_file.name),
                                        stdout=subprocess.PIPE,
                                        universal_newlines=True, shell=False)
        reader = threading.Thread(target=self._read_job_id)
        reader.daemon = True
        reader.start()

    def _read_job_id(self):
        for line in iter(self.process.stdout.readline, ''):
            line = line.strip()
            if self.job_id is None and line:
                # --parsable prints "jobid" or "jobid;cluster"
                job_id = line.split(';')[0]
                if job_id.isdigit():
                    self.job_id = job_id
                    sys.stderr.write("submitted slurm job {}\n".format(job_id))

    def cancel(self):
        if self._cancelled:
            return
        if self.job_id is not None:
            cmd = ['scancel', self.job_id]
        elif self.job_name is not None:
            user = os.environ.get('USER')
            cmd = ['scancel', '--name={}'.format(self.job_name)]
            if user:
                cmd.append('--user={}'.format(user))
        else:
            sys.stderr.write("no slurm job id known; nothing to cancel\n")
            return
        self._cancelled = True
        sys.stderr.write("cancelling slurm job: {}\n".format(' '.join(cmd)))
        try:
            subprocess.call(cmd, stdout=DEVNULL, stderr=DEVNULL)
        except OSError as e:
            sys.stderr.write("scancel failed: {}\n".format(e))

    def _slurm_exit_gracefully(self, signum, frame):
        sys.stderr.write("received signal {}\n".format(signum))
        self._kill_now = True
        self.cancel()

    def wait(self):
        waited_after_cancel = 0
        while self.process.poll() is None:
            if self._kill_now:
                self.cancel()
                if waited_after_cancel >= self.cancel_grace:
                    self.process.terminate()
                    break
                waited_after_cancel += self.poll_interval
            time.sleep(self.poll_interval)
        self.retval = self.process.wait()
        return self.retval

    def is_finished(self):
        return self.retval is not None and self.retval == 0 and not self._kill_now


def _find_executable(name):
    for d in os.environ.get('PATH', '').split(os.pathsep):
        path = os.path.join(d, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


###############################################################################
# Scheduler backends
#
# A backend turns the scheduler-neutral resource request of run.py
# (-n cores, -s soft mem per core, -m hard mem per core, -w walltime, -q queue,
# ...) into the submission arguments of one scheduler, and builds the Job
# object that submits and waits. Backends are looked up by engine name
# (case-insensitive) in BACKENDS; add a new scheduler with @register_backend.
###############################################################################

class JobOptions(object):
    """ scheduler-neutral job request (the fields run.py parses) """

    defaults = dict(engine='sge', local=False, internet=False, docker=False,
                    num_cores=1, soft_memory='1G', hard_memory='1G',
                    walltime='6:00:00', queue=None, job_name=None,
                    log_file=None, out_file=None, shell='/bin/bash', cwd=None,
                    servers=None, sge_parallel_env='smp', extra_args=None,
                    internet_args=None)

    def __init__(self, **kwargs):
        for k, v in self.defaults.items():
            setattr(self, k, kwargs.pop(k, v))
        if kwargs:
            raise TypeError("unknown job options: {}".format(sorted(kwargs)))
        if self.cwd is None:
            self.cwd = os.getcwd()


BACKENDS = {}


def register_backend(cls):
    for name in (cls.name,) + tuple(cls.aliases):
        BACKENDS[name.lower()] = cls
    return cls


def get_backend(engine):
    try:
        return BACKENDS[engine.lower()]()
    except KeyError:
        raise ValueError("invalid cluster engine '{}'. supported engines are {}".format(
            engine, ", ".join(sorted(set(c.name for c in BACKENDS.values())))))


def select_backend(opts):
    """ return the backend that runs this job; mirrors the historical rule
    `local or (internet and engine != 'lsf')` -> run locally """
    if opts.local:
        return LocalBackend()
    try:
        backend = get_backend(opts.engine)
    except ValueError:
        # historical behaviour: internet jobs ran locally before the engine
        # name was validated
        if opts.internet and opts.engine != 'lsf':
            return LocalBackend()
        raise
    if opts.internet and backend.internet_runs_locally(opts):
        return LocalBackend()
    return backend


class Backend(object):
    name = None
    aliases = ()

    def internet_runs_locally(self, opts):
        """ True if a job that needs internet access must run on the submit host """
        return True

    def submit_args(self, opts):
        raise NotImplementedError

    def make_job(self, job_script, opts):
        raise NotImplementedError


@register_backend
class LocalBackend(Backend):
    name = 'local'
    aliases = ('none',)

    def submit_args(self, opts):
        return None

    def make_job(self, job_script, opts):
        return LocalJob(job_script=job_script, out_file=opts.out_file,
                        log_file=opts.log_file, shell=opts.shell)


@register_backend
class LSFBackend(Backend):
    """ IBM LSF (MSK lilac). Arguments are built exactly as run.py did before
    the backend refactor; scripts/tests/test_backends.py checks this. """
    name = 'lsf'

    def internet_runs_locally(self, opts):
        # historical rule compared the raw engine name, case-sensitively:
        # `-g lsf` submits with select[internet], `-g LSF` runs locally
        return opts.engine != 'lsf'

    def submit_args(self, opts):
        qsub_args = "-cwd {pwd} -L {shell}".format(pwd=opts.cwd, shell=opts.shell)
        if opts.queue is not None:
            qsub_args += " -q {}".format(opts.queue)
        if opts.job_name is not None:
            qsub_args += " -J {}".format(opts.job_name)
        if opts.log_file is not None:
            qsub_args += " -o {}".format(opts.log_file)
        if opts.internet:
            qsub_args += ' -R "select[internet]"'
        if opts.num_cores > 1:
            qsub_args += ' -n {num_cores} -R "span[hosts=1]"'.format(num_cores=opts.num_cores)
        hard_mem_gb = int(math.ceil(human2bytes(opts.hard_memory) / 1000000000.0))
        soft_mem_gb = int(math.ceil(human2bytes(opts.soft_memory) / 1000000000.0))
        walltime = re.sub(r'(\d+):(\d+):(\d+)', r'\g<1>:\g<2>', opts.walltime)
        qsub_args += ' -M {hard_mem_gb} -R "rusage[mem={soft_mem_gb}]" -W {walltime}'.format(
            hard_mem_gb=hard_mem_gb, soft_mem_gb=soft_mem_gb, walltime=walltime)
        if opts.extra_args:
            qsub_args += " " + opts.extra_args
        return qsub_args

    def make_job(self, job_script, opts):
        return LSFJob(job_script=job_script, qsub_args=self.submit_args(opts),
                      out_file=opts.out_file,
                      remote_check_servers=None)  # checking filesize on remote servers not supported


@register_backend
class SGEBackend(Backend):
    """ Sun/Univa Grid Engine through DRMAA (needs DRMAA_LIBRARY_PATH) """
    name = 'sge'

    def submit_args(self, opts):
        qsub_args = "-V -wd {pwd} -now n -notify -b n -S {shell}".format(pwd=opts.cwd, shell=opts.shell)
        if opts.queue is not None:
            qsub_args += " -q {}".format(opts.queue)
        if opts.job_name is not None:
            qsub_args += " -N {}".format(opts.job_name)
        if opts.log_file is not None:
            qsub_args += " -j y -o {}".format(opts.log_file)
        if opts.num_cores > 1:
            qsub_args += " -pe {penv} {num_cores}".format(penv=opts.sge_parallel_env,
                                                          num_cores=opts.num_cores)
        qsub_args += " -l virtual_free={soft_mem},h_vmem={hard_mem}".format(soft_mem=opts.soft_memory,
                                                                            hard_mem=opts.hard_memory)
        if opts.extra_args:
            qsub_args += " " + opts.extra_args
        return qsub_args

    def make_job(self, job_script, opts):
        import drmaa_job
        return drmaa_job.DRMAAJob(job_script=job_script, qsub_args=self.submit_args(opts),
                                  out_file=opts.out_file, remote_check_servers=opts.servers)


@register_backend
class PBSBackend(Backend):
    """ PBS/Torque through qsub + qstat polling """
    name = 'pbs'
    aliases = ('torque',)

    def submit_args(self, opts):
        total_hard_mem = opts.num_cores * human2bytes(opts.hard_memory)
        qsub_args = "-d {pwd} -S {shell}".format(pwd=opts.cwd, shell=opts.shell)
        if opts.queue is not None:
            qsub_args += " -q {}".format(opts.queue)
        if opts.job_name is not None:
            qsub_args += " -N {}".format(opts.job_name)
        if opts.log_file is not None:
            qsub_args += " -j oe -o {}".format(opts.log_file)
        qsub_args += " -l nodes=1:ppn={num_cores}".format(num_cores=opts.num_cores)
        if opts.docker:
            qsub_args += ":docker"
        qsub_args += " -l walltime={walltime} -l mem={total_mem}".format(walltime=opts.walltime,
                                                                         total_mem=total_hard_mem)
        if opts.extra_args:
            qsub_args += " " + opts.extra_args
        return qsub_args

    def make_job(self, job_script, opts):
        return PBSJob(job_script=job_script, qsub_args=self.submit_args(opts),
                      out_file=opts.out_file, remote_check_servers=opts.servers)


def mem_per_cpu_mb(mem):
    """ '1.5G' -> 1536: memory per core in MiB, rounded up (Slurm M = MiB) """
    return int(math.ceil(human2bytes(mem) / 1048576.0))


@register_backend
class SlurmBackend(Backend):
    """ Slurm through `sbatch --wait`.

    -m (hard memory per core) maps to --mem-per-cpu, the same per-core meaning
    as LSF -M; -s (soft memory) has no Slurm equivalent and is dropped.
    Internet jobs run on the submit host unless CLUSTER_INTERNET_ARGS
    (--internet_args) names the partition/constraint that has internet.
    """
    name = 'slurm'

    def internet_runs_locally(self, opts):
        return not opts.internet_args

    def submit_args(self, opts):
        args = ['--wait', '--parsable', '--nodes=1', '--ntasks=1',
                '--cpus-per-task={}'.format(opts.num_cores),
                '--mem-per-cpu={}M'.format(mem_per_cpu_mb(opts.hard_memory)),
                '--time={}'.format(opts.walltime)]
        if opts.queue is not None:
            args += ['-p', opts.queue]
        if opts.job_name is not None:
            args += ['-J', opts.job_name]
        if opts.log_file is not None:
            args += ['-o', opts.log_file]
        args.append('--chdir={}'.format(opts.cwd))
        if opts.extra_args:
            args += shlex.split(opts.extra_args)
        if opts.internet and opts.internet_args:
            args += shlex.split(opts.internet_args)
        return args

    def make_job(self, job_script, opts):
        return SlurmJob(job_script=job_script, sbatch_args=self.submit_args(opts),
                        out_file=opts.out_file, job_name=opts.job_name)
