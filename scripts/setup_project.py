#!/usr/bin/env python
"""Set up a new jrflab-modules project directory.

Writes, in the project directory:
    Makefile              (include modules/Makefile; only if absent)
    summary_config.yaml   (copy of default_yaml/summary_config.yaml; only if absent)
    project_config.yaml   (from default_yaml/project_config.setup_template.yaml,
                           every key commented, unused keys commented out)
    samples.yaml          (tumor/normal pairs)
    sample.fastq.yaml     (FASTQ input only)
    bam/<sample>.bam      (BAM input only: symbolic links, with .bam.bai)
    SETUP_NOTES.md        (checklist of what is still to check or decide,
                           preflight results and the next commands)

Presets: default_yaml/presets/references.yaml and default_yaml/presets/panels.yaml.
Guide: _docs/new_project_setup.md

Python 2.7 and 3 compatible. Needs PyYAML only (the jrflab-modules env has it).

Examples:
    python modules/scripts/setup_project.py --species human --seq-type WGS \\
        --fastq-dir /path/to/Project_12345 --dry-run
    python modules/scripts/setup_project.py --species human --seq-type PANEL \\
        --panel IMPACT505 --sample-sheet samples.tsv
    python modules/scripts/setup_project.py --species mouse --seq-type WES \\
        --bam-dir /path/to/bams
"""
from __future__ import print_function

import argparse
import datetime
import io
import os
import re
import shutil
import socket
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("setup_project.py needs PyYAML. Activate the jrflab env first:\n"
                     "  source ~/share/usr/anaconda-envs/jrflab-modules-0.1.4/bin/activate\n")
    sys.exit(1)

MODULES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESET_DIR = os.path.join(MODULES_DIR, 'default_yaml', 'presets')
TEMPLATE_FILE = os.path.join(MODULES_DIR, 'default_yaml', 'project_config.setup_template.yaml')

SPECIES_DEFAULT_REF = {'human': 'b37', 'mouse': 'GRCm38'}
SEQ_TYPES = ('WGS', 'WES', 'PANEL')
SV_CALLER_TARGETS = {
    'manta': 'manta_tumor_normal',
    'svaba': 'svaba_tumor_normal',
    'gridss': 'gridss_tumor_normal',
    'lumpy': 'lumpy',
    'delly': 'delly',
}
INDEL_CALLERS = ('varscan_indels', 'strelka_indels', 'scalpel_indels', 'lancet_indels',
                 'platypus_indels', 'pindel', 'mutect_indels')
# Lancet is off by default (2026-11-26): left out by 16 of 27 Reis-Filho lab projects and
# by 6 of 7 recent WGS projects; it ran 24 h on one human chromosome. Add it with
# --indel-callers ... lancet_indels.
LAB_INDEL_CALLERS = 'varscan_indels strelka_indels scalpel_indels platypus_indels'
FACETS_WGS = {'pre_cval': 700, 'cval1': 750, 'cval2': 700, 'min_nhet': 25}
FACETS_TARGETED = {'pre_cval': 50, 'cval1': 150, 'cval2': 50, 'min_nhet': 25}
HUMAN_ONLY_TARGETS = 'msisensor, mimsi, hotspot, hotspot_summary, hr_detect, cravat_annotate, cravat_summary'
SAMPLE_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9-]*$')
NORMAL_SUFFIX_RE = re.compile(r'^(?P<patient>.+?)-?(N|Normal|NORMAL|normal|Blood|BLOOD|blood|PBMC|Germline|GL)\d*$')
FASTQ_RE = re.compile(r'\.(fastq|fq)\.gz$')
R1_PATTERNS = [
    (re.compile(r'_R1(_\d{3})?(\.(fastq|fq)\.gz)$'), r'_R2\1\2'),
    (re.compile(r'_1(\.(fastq|fq)\.gz)$'), r'_2\1'),
]
NODE_LOCAL_TMP = ('/tmp', '/scratch', '/lscratch', '/var/tmp', '/fscratch')


class SetupError(Exception):
    pass


# ------------------------------------------------------------------ small helpers

def load_yaml(path):
    with io.open(path, 'r', encoding='utf-8') as handle:
        if hasattr(yaml, 'safe_load'):
            return yaml.safe_load(handle)
        return yaml.load(handle)


def expand(path):
    """Expand ~, $HOME, $(HOME) and $(USER) the way make + shell would."""
    if path is None:
        return None
    path = str(path)
    path = path.replace('$(HOME)', os.path.expanduser('~'))
    path = path.replace('$(USER)', os.environ.get('USER', ''))
    return os.path.expandvars(os.path.expanduser(path))


def yaml_scalar(value):
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if value == '':
        return '""'
    return str(value)


def write_text(path, text):
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(text if isinstance(text, type(u'')) else text.decode('utf-8'))


# ------------------------------------------------------------------ samples

class Sample(object):
    def __init__(self, name, sample_type, patient):
        self.name = name
        self.type = sample_type      # 'T' or 'N'
        self.patient = patient
        self.fastq_pairs = []        # [[R1, R2], ...]
        self.bam = None
        self.bai = None
        self.original_name = name


def fastq_mate(r1_path):
    base = os.path.basename(r1_path)
    for pattern, repl in R1_PATTERNS:
        if pattern.search(base):
            return os.path.join(os.path.dirname(r1_path), pattern.sub(repl, base))
    return None


def find_fastq_pairs(directory):
    """Return ([R1, R2] pairs, unpaired R1 files) found below directory."""
    files = []
    for root, dirs, names in os.walk(directory, followlinks=True):
        dirs.sort()
        for name in sorted(names):
            if FASTQ_RE.search(name):
                files.append(os.path.join(root, name))
    fileset = set(files)
    pairs, unpaired = [], []
    for path in files:
        mate = fastq_mate(path)
        if mate is None:
            continue
        if mate in fileset:
            pairs.append([path, mate])
        else:
            unpaired.append(path)
    return pairs, unpaired


def sample_name_from_fastq(path):
    """IGO naming: .../Sample_<name>_IGO_<project>_<n>/<name>_IGO_..._S1_L001_R1_001.fastq.gz"""
    for part in reversed(os.path.dirname(path).split(os.sep)):
        if part.startswith('Sample_'):
            name = part[len('Sample_'):]
            return re.sub(r'_IGO_.*$', '', name)
    name = os.path.basename(path)
    name = re.sub(r'(_S\d+)?(_L\d{3})?_R1(_\d{3})?\.(fastq|fq)\.gz$', '', name)
    name = re.sub(r'_1\.(fastq|fq)\.gz$', '', name)
    return re.sub(r'_IGO_.*$', '', name)


def find_bam_index(bam):
    for candidate in (bam + '.bai', re.sub(r'\.bam$', '.bai', bam)):
        if os.path.exists(candidate):
            return candidate
    return None


def guess_type_and_patient(names):
    """Guess tumor/normal and patient from names (folder input only)."""
    types, patients = {}, {}
    normal_patients = {}
    for name in names:
        match = NORMAL_SUFFIX_RE.match(name)
        if match:
            types[name] = 'N'
            patients[name] = match.group('patient').rstrip('-')
            normal_patients[patients[name]] = name
    for name in names:
        if name in types:
            continue
        types[name] = 'T'
        best = None
        for patient in normal_patients:
            # the character after the patient id must not be a digit (P1 vs P10)
            if name.startswith(patient) and not name[len(patient):len(patient) + 1].isdigit() \
                    and len(name) > len(patient):
                if best is None or len(patient) > len(best):
                    best = patient
        if best is None:
            best = re.sub(r'-?(T|Tumor|TUMOR|tumor)\d*$', '', name) or name
        patients[name] = best
    return types, patients


def samples_from_fastq_dirs(dirs, messages):
    samples = {}
    for directory in dirs:
        directory = os.path.abspath(expand(directory))
        if not os.path.isdir(directory):
            raise SetupError("FASTQ folder not found: {}".format(directory))
        pairs, unpaired = find_fastq_pairs(directory)
        for path in unpaired:
            messages['errors'].append("R1 FASTQ without R2 mate: {}".format(path))
        if not pairs:
            raise SetupError("no paired FASTQ files (*_R1_*.fastq.gz / *_R2_*.fastq.gz) below {}".format(directory))
        for r1, r2 in pairs:
            name = sample_name_from_fastq(r1)
            samples.setdefault(name, []).append([r1, r2])
    # underscores are replaced before guessing, so that P1_N gives patient P1
    fixed = dict((name, name.replace('_', '-')) for name in samples)
    types, patients = guess_type_and_patient(sorted(fixed.values()))
    result = []
    for name in sorted(samples):
        new = fixed[name]
        sample = Sample(new, types[new], patients[new])
        sample.original_name = name
        sample.fastq_pairs = sorted(samples[name])
        result.append(sample)
    messages['notes'].append("Tumor/normal types and patients were GUESSED from the sample names "
                             "(normal = name ending in N, Normal, Blood, PBMC or GL). Check samples.yaml, "
                             "or use --sample-sheet for an explicit design.")
    return result


def samples_from_bam_dir(directory, messages):
    directory = os.path.abspath(expand(directory))
    if not os.path.isdir(directory):
        raise SetupError("BAM folder not found: {}".format(directory))
    bams = sorted(f for f in os.listdir(directory) if f.endswith('.bam'))
    if not bams:
        raise SetupError("no *.bam files in {}".format(directory))
    names = [re.sub(r'\.bam$', '', f) for f in bams]
    fixed = [n.replace('_', '-') for n in names]
    types, patients = guess_type_and_patient(fixed)
    result = []
    for name, new, bam in zip(names, fixed, bams):
        sample = Sample(new, types[new], patients[new])
        sample.original_name = name
        sample.bam = os.path.join(directory, bam)
        sample.bai = find_bam_index(sample.bam)
        result.append(sample)
    messages['notes'].append("Tumor/normal types and patients were GUESSED from the BAM file names. "
                             "Check samples.yaml, or use --sample-sheet for an explicit design.")
    return result


def samples_from_sheet(path, messages):
    """TSV columns: sample, type (T/N), patient, path. One sample may have several rows."""
    path = expand(path)
    if not os.path.isfile(path):
        raise SetupError("sample sheet not found: {}".format(path))
    base_dir = os.path.dirname(os.path.abspath(path))
    samples, order = {}, []
    with io.open(path, 'r', encoding='utf-8') as handle:
        for lineno, line in enumerate(handle, 1):
            line = line.rstrip('\r\n')
            if not line.strip() or line.startswith('#'):
                continue
            fields = [f.strip() for f in line.split('\t')]
            if lineno == 1 and fields[0].lower() in ('sample', 'sample_id', 'name'):
                continue
            if len(fields) < 4:
                raise SetupError("{} line {}: need 4 tab-separated columns (sample, type, patient, path), "
                                 "found {}".format(path, lineno, len(fields)))
            name, sample_type, patient, data_path = fields[:4]
            sample_type = sample_type.upper()
            if sample_type in ('TUMOR', 'TUMOUR'):
                sample_type = 'T'
            if sample_type == 'NORMAL':
                sample_type = 'N'
            if sample_type not in ('T', 'N'):
                raise SetupError("{} line {}: type must be T or N, not '{}'".format(path, lineno, fields[1]))
            if name not in samples:
                samples[name] = Sample(name, sample_type, patient)
                order.append(name)
            sample = samples[name]
            if sample.type != sample_type or sample.patient != patient:
                raise SetupError("{} line {}: sample {} has two different types or patients".format(
                    path, lineno, name))
            data_path = expand(data_path)
            if not os.path.isabs(data_path):
                data_path = os.path.join(base_dir, data_path)
            if data_path.endswith('.bam'):
                if sample.bam is not None:
                    raise SetupError("sample {} has more than one BAM".format(name))
                sample.bam = data_path
                sample.bai = find_bam_index(data_path)
            elif os.path.isdir(data_path):
                pairs, unpaired = find_fastq_pairs(data_path)
                for unp in unpaired:
                    messages['errors'].append("R1 FASTQ without R2 mate: {}".format(unp))
                if not pairs:
                    messages['errors'].append("sample {}: no paired FASTQ files below {}".format(name, data_path))
                sample.fastq_pairs.extend(pairs)
            elif FASTQ_RE.search(data_path):
                mate = fastq_mate(data_path)
                if mate is None:
                    raise SetupError("sample {}: cannot find the R2 name for {} (expected _R1_ or _1 in the "
                                     "file name)".format(name, data_path))
                sample.fastq_pairs.append([data_path, mate])
            else:
                raise SetupError("sample {}: path must be a BAM, an R1 FASTQ or a folder of FASTQs: {}".format(
                    name, data_path))
    return [samples[n] for n in order]


def fix_and_check_names(samples, fix_names, messages):
    renamed = [(s.original_name, s.name) for s in samples if s.original_name != s.name]
    for sample in samples:
        if '_' in sample.name and fix_names:
            sample.name = sample.name.replace('_', '-')
            renamed.append((sample.original_name, sample.name))
        if '_' in sample.patient and fix_names:
            sample.patient = sample.patient.replace('_', '-')
    for sample in samples:
        if '_' in sample.name:
            messages['errors'].append("sample name '{}' contains an underscore; use hyphens "
                                      "(or run with --fix-names)".format(sample.name))
        elif not SAMPLE_NAME_RE.match(sample.name):
            messages['errors'].append("sample name '{}' has characters other than letters, digits and "
                                      "hyphens".format(sample.name))
        if '_' in sample.patient or not SAMPLE_NAME_RE.match(sample.patient):
            messages['errors'].append("patient name '{}' must have letters, digits and hyphens only".format(
                sample.patient))
    seen = {}
    for sample in samples:
        if sample.name in seen:
            messages['errors'].append("two samples have the name '{}' ({} and {})".format(
                sample.name, seen[sample.name], sample.original_name))
        seen[sample.name] = sample.original_name
    if renamed:
        messages['notes'].append("Renamed {} samples (underscore to hyphen): {}".format(
            len(renamed), ', '.join('{} -> {}'.format(a, b) for a, b in renamed)))
    return renamed


def check_files(samples, messages):
    for sample in samples:
        if sample.bam is None and not sample.fastq_pairs:
            messages['errors'].append("sample {} has no FASTQ or BAM".format(sample.name))
        if sample.bam is not None and sample.fastq_pairs:
            messages['errors'].append("sample {} has both FASTQ and BAM input; give one".format(sample.name))
        for r1, r2 in sample.fastq_pairs:
            for path in (r1, r2):
                if not os.path.isfile(path):
                    messages['errors'].append("sample {}: FASTQ not found: {}".format(sample.name, path))
        if sample.bam is not None:
            if not os.path.isfile(sample.bam):
                messages['errors'].append("sample {}: BAM not found: {}".format(sample.name, sample.bam))
            elif sample.bai is None:
                messages['warnings'].append("sample {}: no BAM index (.bam.bai or .bai) next to {}; "
                                            "the pipeline will index it".format(sample.name, sample.bam))


def build_pairs(samples, messages):
    """Return list of (patient, normal or None, [tumors]) in input order."""
    by_patient, order = {}, []
    for sample in samples:
        if sample.patient not in by_patient:
            by_patient[sample.patient] = {'N': [], 'T': []}
            order.append(sample.patient)
        by_patient[sample.patient][sample.type].append(sample.name)
    entries = []
    for patient in order:
        normals, tumors = by_patient[patient]['N'], by_patient[patient]['T']
        if len(normals) > 1:
            messages['errors'].append("patient {} has {} normals ({}); samples.yaml allows one normal per "
                                      "entry: give the extra normal its own patient id".format(
                                          patient, len(normals), ', '.join(normals)))
            continue
        normal = normals[0] if normals else None
        if normal is None:
            messages['warnings'].append("patient {}: tumor-only ({}); somatic callers, FACETS and SV callers "
                                        "need a normal (use a pooled normal or snv_type mutect2)".format(
                                            patient, ', '.join(tumors)))
        if normal is not None and not tumors:
            messages['warnings'].append("patient {}: normal {} has no tumor; it is aligned but not "
                                        "paired".format(patient, normal))
        entries.append((patient, normal, tumors))
    return entries


def samples_yaml_text(entries):
    lines = ["# tumor/normal design written by setup_project.py. One entry per patient;",
             "# `tumor` is always a list. Run `make config` after every change.",
             "# Names: letters, digits and hyphens only (no underscores)."]
    for patient, normal, tumors in entries:
        lines.append("- name: {}".format(patient))
        if normal is not None:
            lines.append("  normal: {}".format(normal))
        if tumors:
            lines.append("  tumor: [{}]".format(', '.join(tumors)))
    return '\n'.join(lines) + '\n'


def sample_fastq_yaml_text(samples, path_rewrite):
    lines = ["# one [R1, R2] pair per lane; written by setup_project.py"]
    for sample in samples:
        if not sample.fastq_pairs:
            continue
        lines.append("{}:".format(sample.name))
        for r1, r2 in sample.fastq_pairs:
            lines.append("- [{}, {}]".format(path_rewrite(r1), path_rewrite(r2)))
    return '\n'.join(lines) + '\n'


# ------------------------------------------------------------------ project_config

def resolve_presets(args):
    references = load_yaml(os.path.join(PRESET_DIR, 'references.yaml'))
    panels = load_yaml(os.path.join(PRESET_DIR, 'panels.yaml'))
    ref = args.ref or SPECIES_DEFAULT_REF[args.species]
    if ref not in references:
        raise SetupError("--ref {} has no preset; choose one of {}".format(ref, ', '.join(sorted(references))))
    ref_preset = references[ref]
    if ref_preset['species'] != args.species:
        raise SetupError("--ref {} is a {} genome but --species is {}".format(ref, ref_preset['species'],
                                                                           args.species))
    panel = None
    if args.panel:
        if args.panel not in panels:
            raise SetupError("--panel {} is not in default_yaml/presets/panels.yaml; known: {}".format(
                args.panel, ', '.join(sorted(panels))))
        panel = dict(panels[args.panel])
        panel['name'] = args.panel
        if panel['ref'] != ref:
            raise SetupError("panel {} is defined for ref {}, not {}".format(args.panel, panel['ref'], ref))
        wanted_kind = {'PANEL': 'panel', 'WES': 'exome'}.get(args.seq_type)
        if wanted_kind is None:
            raise SetupError("--panel is used with --seq-type PANEL or WES, not WGS")
        if panel['kind'] != wanted_kind:
            raise SetupError("panel {} is a{} {} preset; use it with --seq-type {}".format(
                args.panel, 'n' if panel['kind'] == 'exome' else '', panel['kind'],
                'WES' if panel['kind'] == 'exome' else 'PANEL'))
    if args.seq_type == 'PANEL' and panel is None and not args.targets_file:
        raise SetupError("--seq-type PANEL needs --panel <name> or --targets-file <BED> "
                         "(see --list-panels)")
    return ref, ref_preset, panel


def default_sv_callers(species, seq_type):
    if seq_type != 'WGS':
        return ['manta']
    if species == 'mouse':
        return ['manta', 'svaba']
    return ['manta', 'svaba', 'gridss']


def build_config(args, ref, ref_preset, panel):
    seq_type = args.seq_type
    targeted = seq_type in ('WES', 'PANEL')
    facets = dict(FACETS_TARGETED if targeted else FACETS_WGS)
    if panel is not None:
        facets.update(panel.get('facets') or {})
    cluster = {'lsf': ('LSF', True), 'slurm': ('SLURM', True), 'local': ('local', False)}[args.cluster]
    c = {
        'cluster_engine': cluster[0],
        'use_cluster': cluster[1],
        'site': None, 'cluster_queue': None, 'cluster_extra_args': None,
        'ref': ref,
        'seq_type': seq_type,
        'ref_fasta': None, 'nochr_ref_fasta': None, 'chr_ref_fasta': None,
        'aligner': 'bwamem',
        'bam_chr1_base_recal': True,
        'bam_dup_type': 'markdup',
        'bam_no_filter': False,
        'bam_no_recal': False,
        'bam_no_realn': False,
        'bam_no_sort': False,
        'bam_fix_rg': False,
        'bam_phred64': False,
        'bam_reprocess': False,
        'merge_split_bams': False,
        'targets_file': None, 'exome_bed': None, 'targets_list': None, 'call_intervals_bed': None,
        'ontarget_file': None, 'offtarget_file': None,
        'snv_type': args.snv_type,
        'mutect_split_chr': True,
        'mutect_use_contest': False,
        'indel_types': ' '.join(args.indel_callers),
        'strelka_version': None,
        'svaba_version': None, 'svaba': None, 'svaba_env': None,
        'ann_facets': True,
        'ann_mut_taste': False,
        'ann_provean': False,
        'ann_pathogen': bool(ref_preset.get('ann_pathogen')),
        'vcf_post_ann_filter_expression': 'ExAC_AF > 0.01',
        'gatk_hard_filter_snps': True,
        'gatk_pool_snp_recal': False,
        'facets_pre_cval': facets['pre_cval'],
        'facets_cval1': facets['cval1'],
        'facets_cval2': facets['cval2'],
        'facets_min_nhet': facets['min_nhet'],
        'facets_union_gatk_dbsnp': False,
        'dbsnp_subset': None,
        'slack_channel': None,
        'qsub_priority': 0,
    }
    if args.cluster == 'slurm':
        c['site'] = None   # stays commented: no iris site block exists yet
    if args.ref_fasta:
        c['ref_fasta'] = c['nochr_ref_fasta'] = c['chr_ref_fasta'] = args.ref_fasta
    if seq_type == 'WGS':
        c['targets_file'] = args.targets_file or ref_preset.get('wgs_targets_file')
        c['call_intervals_bed'] = args.call_intervals_bed or ref_preset.get('wgs_call_intervals_bed')
    elif seq_type == 'WES':
        if args.targets_file:
            c['exome_bed'] = args.targets_file
        elif panel is not None and expand(panel['targets_file']) != expand(ref_preset.get('default_exome_bed')):
            c['exome_bed'] = panel['targets_file']
        if args.call_intervals_bed:
            c['call_intervals_bed'] = args.call_intervals_bed
    else:  # PANEL
        c['targets_file'] = args.targets_file or panel['targets_file']
        if args.call_intervals_bed:
            c['call_intervals_bed'] = args.call_intervals_bed
    if panel is not None and not args.targets_file:
        c['targets_list'] = panel.get('targets_list')
        c['ontarget_file'] = panel.get('ontarget_file')
        c['offtarget_file'] = panel.get('offtarget_file')
    if args.species == 'mouse':
        c['ann_pathogen'] = False
        if seq_type == 'WGS':
            c['strelka_version'] = 2
            c['bam_no_realn'] = True
            c['bam_no_recal'] = True
    if args.strelka_version:
        c['strelka_version'] = args.strelka_version
    if 'svaba' in args.sv_callers:
        c['svaba_version'] = args.svaba_version
        if args.svaba_version == 2:
            c['svaba'] = '/data/riazlab/lib/bin/svaba'
            c['svaba_env'] = ''
    return c


def render_template(values, header_lines, sv_targets):
    with io.open(TEMPLATE_FILE, 'r', encoding='utf-8') as handle:
        template = handle.read().splitlines()
    out = []
    key_re = re.compile(r'^(?P<key>\w+): <<(?P<name>\w+)(\|(?P<example>.*))?>>$')
    for line in template:
        if line.startswith('#!'):
            continue
        if line.strip() == '<<header>>':
            out.extend(header_lines)
            continue
        match = key_re.match(line)
        if match:
            name = match.group('name')
            if name not in values:
                raise SetupError("template placeholder {} has no value (setup_project.py bug)".format(name))
            value = values[name]
            if value is None:
                example = match.group('example') or ''
                out.append('# {}: {}'.format(match.group('key'), example).rstrip())
            else:
                out.append('{}: {}'.format(match.group('key'), yaml_scalar(value)))
            continue
        out.append(line.replace('<<sv_targets>>', sv_targets))
    return '\n'.join(out) + '\n'


# ------------------------------------------------------------------ preflight

def read_make_default(path, var):
    """Value of `VAR ?= x` or `VAR = x` in a make file (first match), $(HOME)/$(USER) expanded."""
    if not os.path.isfile(path):
        return None
    pattern = re.compile(r'^\s*' + re.escape(var) + r'\s*[?:]?=\s*(.*?)\s*$')
    with io.open(path, 'r', encoding='utf-8', errors='replace') as handle:
        for line in handle:
            match = pattern.match(line)
            if match:
                return expand(match.group(1))
    return None


def contigs_of(path, limit_lines=2000000):
    contigs = set()
    opener = io.open(path, 'r', encoding='utf-8', errors='replace')
    with opener as handle:
        for i, line in enumerate(handle):
            if i >= limit_lines:
                break
            if not line.strip() or line.startswith(('#', 'track', 'browser', '@')):
                continue
            contigs.add(re.split(r'[\t ]', line, 1)[0])
    return contigs


def fai_contigs(fasta):
    for candidate in (fasta + '.fai',):
        if os.path.isfile(candidate):
            return contigs_of(candidate)
    return None


def contig_style(contigs):
    main = [c for c in contigs if re.match(r'^(chr)?([0-9]+|X|Y|M|MT)$', c)]
    if not main:
        return 'unknown'
    with_chr = sum(1 for c in main if c.startswith('chr'))
    if with_chr == len(main):
        return 'chr'
    if with_chr == 0:
        return 'nochr'
    return 'mixed'


def preflight(config, ref_preset, args, project_dir):
    results = []

    def add(status, item, detail):
        results.append((status, item, detail))

    fasta = expand(config['ref_fasta'] or ref_preset['fasta'])
    fasta_contigs = None
    if os.path.isfile(fasta):
        add('OK', 'reference FASTA', fasta)
        fasta_contigs = fai_contigs(fasta)
        if fasta_contigs is None:
            add('WARN', 'FASTA index', 'no {}.fai'.format(fasta))
        dict_file = re.sub(r'\.(fasta|fa)$', '.dict', fasta)
        if not (os.path.isfile(dict_file) or os.path.isfile(fasta + '.dict')):
            add('WARN', 'FASTA dictionary', 'no {} (Picard/GATK need it)'.format(dict_file))
    else:
        add('FAIL', 'reference FASTA', 'not found: {}'.format(fasta))
    expected_style = contig_style(fasta_contigs) if fasta_contigs else ref_preset['contig_style']

    bed_keys = ['targets_file', 'exome_bed', 'call_intervals_bed', 'ontarget_file', 'offtarget_file']
    if config['seq_type'] == 'WES' and not config['exome_bed']:
        config_default_exome = ref_preset.get('default_exome_bed')
    else:
        config_default_exome = None
    beds = [(k, config[k]) for k in bed_keys if config.get(k)]
    if config_default_exome:
        beds.append(('EXOME_BED (genome include default)', config_default_exome))
    for key, value in beds:
        path = expand(value)
        if not os.path.isfile(path):
            add('FAIL', key, 'not found: {}'.format(path))
            continue
        contigs = contigs_of(path)
        style = contig_style(contigs)
        if style != expected_style and expected_style != 'unknown':
            add('FAIL', key + ' contig style', '{} uses {} contig names, the reference uses {}'.format(
                path, style, expected_style))
        elif fasta_contigs is not None:
            missing = sorted(contigs - fasta_contigs)
            if missing:
                add('WARN', key + ' contigs', '{} contigs are not in the FASTA: {}{}'.format(
                    len(missing), ', '.join(missing[:6]), ' ...' if len(missing) > 6 else ''))
            else:
                add('OK', key, '{} ({} contigs, {} style)'.format(path, len(contigs), style))
        else:
            add('OK', key, '{} ({} style; FASTA index not available for a contig-by-contig check)'.format(
                path, style))
    if config.get('targets_list'):
        path = expand(config['targets_list'])
        add('OK' if os.path.isfile(path) else 'FAIL', 'targets_list', path if os.path.isfile(path)
            else 'not found: {}'.format(path))

    config_inc = os.path.join(MODULES_DIR, 'config.inc')
    envs = ['JRFLAB_MODULES_ENV']
    if config['seq_type'] == 'PANEL':
        envs.append('CNVKIT_ENV')
    if 'gridss' in args.sv_callers:
        envs.append('GRIDSS_ENV')
    if 'svaba' in args.sv_callers and config.get('svaba_version') == 1:
        envs.append('SVABA_ENV')
    for env in envs:
        path = read_make_default(config_inc, env)
        if path is None:
            add('WARN', env, 'not defined in config.inc')
        elif os.path.isdir(path):
            add('OK', env, path)
        else:
            add('FAIL', env, 'not found: {}'.format(path))
    if config.get('strelka_version') == 2:
        path = read_make_default(os.path.join(MODULES_DIR, 'variant_callers', 'somatic', 'strelka.mk'),
                                 'STRELKA_ENV')
        add('OK' if path and os.path.isdir(path) else 'FAIL', 'STRELKA_ENV (strelka_version 2)',
            path if path and os.path.isdir(path) else 'not found: {}'.format(path))
    if config.get('svaba_version') == 2:
        path = expand(config['svaba'])
        add('OK' if os.path.isfile(path) else 'FAIL', 'svaba 2.0.0 binary',
            path if os.path.isfile(path) else 'not found: {}'.format(path))

    site_tmp = read_make_default(config_inc, 'SITE_TMPDIR') or expand('~/share/data/$USER/tmp')
    if os.path.isdir(site_tmp) and os.access(site_tmp, os.W_OK):
        add('OK', 'SITE_TMPDIR (exported as TMPDIR by Makefile.inc)', site_tmp)
    else:
        add('FAIL', 'SITE_TMPDIR (exported as TMPDIR by Makefile.inc)',
            'missing or not writable: {} (job scripts are written there; it must be on a file system the '
            'compute nodes read)'.format(site_tmp))
    if site_tmp.startswith(NODE_LOCAL_TMP):
        add('FAIL', 'SITE_TMPDIR shared', '{} looks node-local; compute nodes cannot read it'.format(site_tmp))
    env_tmp = os.environ.get('TMPDIR')
    if env_tmp and env_tmp.startswith(NODE_LOCAL_TMP):
        add('WARN', 'TMPDIR of this shell', '{} is node-local. Makefile.inc overrides it for make, but scripts '
            'run outside make use it'.format(env_tmp))

    if not os.path.exists(os.path.join(project_dir, 'modules', 'Makefile')):
        add('FAIL', 'modules/ in project', 'no {}/modules/Makefile; clone or link the modules tree there '
            '(or use --link-modules)'.format(project_dir))
    else:
        add('OK', 'modules/ in project', os.path.realpath(os.path.join(project_dir, 'modules')))
    if args.species == 'mouse':
        add('WARN', 'dbsnp_subset (mouse)', 'no mouse SNP-site BED exists; cluster_samples stops until one is '
            'built and set')
    return results


# ------------------------------------------------------------------ notes

def checklist(args, config, ref, ref_preset, panel, entries, samples):
    items = []
    seq_type = args.seq_type
    if samples:
        items.append("Check the tumor/normal pairs in `samples.yaml` ({} patients, {} samples).".format(
            len(entries), len(samples)))
    else:
        items.append("Write `samples.yaml` (and `sample.fastq.yaml` for FASTQ input): run setup_project.py "
                     "again with --sample-sheet, --fastq-dir or --bam-dir and --force, or write them by hand.")
    if seq_type == 'WGS':
        items.append("WGS chunking: `targets_file` = `{}` and `call_intervals_bed` = `{}`. Lab human WGS "
                     "projects set the whole-genome BED as targets_file; mouse WGS sets call_intervals_bed "
                     "only.".format(config['targets_file'] or '(not set)',
                                    config['call_intervals_bed'] or '(targets_file)'))
        items.append("FACETS critical values {}/{}/{} (pre_cval/cval1/cval2), min_nhet {}. These are the lab "
                     "WGS values. Earlier WGS projects used other values: WGS_CDH1SV 2050/2150/2050, I-SceI "
                     "WGS 650/750/650. Decide before the first `make facets`.".format(
                         config['facets_pre_cval'], config['facets_cval1'], config['facets_cval2'],
                         config['facets_min_nhet']))
        items.append("Resource profile `config/profiles/wgs.inc` (sized for 30-100x). For higher depth "
                     "raise single values in project_config.yaml (for example `lancet_resources`).")
        items.append("Run `make wgs_metrics` after alignment (coverage check before calling).")
    if seq_type == 'WES':
        kit = config['exome_bed'] or ref_preset.get('default_exome_bed')
        items.append("Capture kit: the targets are `{}`. Confirm the kit with IGO or the vendor; for another "
                     "kit use `--panel <kit>` or `--targets-file`.".format(kit))
        items.append("`QUALIMAP_TARGETS_FILE` and `EMU_TARGETS_FILE` stay the SureSelect 50 Mb BEDs of the "
                     "genome include, whatever the kit.")
        if config['targets_list']:
            items.append("`targets_list` = `{}` (CollectHsMetrics in bam_metrics).".format(config['targets_list']))
    if seq_type == 'PANEL':
        items.append("Panel BED: `targets_file` = `{}`. Confirm the panel version with IGO/CMO (IMPACT341, "
                     "410, 468 and 505 differ).".format(config['targets_file']))
        if config['targets_list']:
            items.append("`targets_list` = `{}` (CollectHsMetrics in bam_metrics).".format(config['targets_list']))
        else:
            items.append("Set `targets_list` (Picard interval list of the panel): bam_metrics otherwise uses "
                         "MSK-IMPACT-v4.sorted.list.")
        if config['ontarget_file']:
            items.append("CNVkit BEDs set (`make cnv_kit`): `{}` and `{}`.".format(config['ontarget_file'],
                                                                                 config['offtarget_file']))
        else:
            items.append("No CNVkit BEDs for this panel: build them with `cnvkit.py target` / `antitarget` "
                         "before `make cnv_kit`, or skip CNVkit.")
    if seq_type in ('WES', 'PANEL'):
        items.append("FACETS critical values {}/{}/{}, min_nhet {} (lab values for exomes and panels).".format(
            config['facets_pre_cval'], config['facets_cval1'], config['facets_cval2'], config['facets_min_nhet']))
        items.append("Manta runs with `--exome` (seq_type {}).".format(seq_type))
    if panel is not None:
        for note in panel.get('notes') or []:
            items.append("Panel preset {}: {}".format(panel['name'], note))
    if args.species == 'mouse':
        items.append("Mouse: these targets stop with an explicit error: {}. Do not run them.".format(
            HUMAN_ONLY_TARGETS))
        items.append("Mouse: `ann_pathogen: false` (pathogenicity annotation is human-only).")
        items.append("Mouse: `cluster_samples` needs `dbsnp_subset` (a BED of common SNP sites); none exists on "
                     "lilac yet.")
        items.append("Mouse: `delmh_summary` needs BSgenome.Mmusculus.UCSC.mm10, which is not installed in "
                     "jrflab-modules-0.1.4.")
        items.append("Mouse: GRIDSS uses the mm10 blacklist and the riazlab FASTA copy (GRIDSS_REF_FASTA), without a PON.")
        if seq_type == 'WGS':
            items.append("Mouse WGS: `bam_no_realn: true` and `bam_no_recal: true` skip GATK realignment and "
                         "BQSR, and `strelka_version: 2` runs Strelka2, as in the mouse WGS example of "
                         "mouse_and_seq_type_config.md. Set the two bam keys to false to realign and recalibrate "
                         "with the MGP v5 known sites.")
        if seq_type == 'WES':
            if config.get('exome_bed'):
                items.append("Mouse WES: targets are the capture-kit BED `{}` (exome_bed). Check that it uses "
                             "GRCm38 contig names without `chr` (1..19 X Y MT).".format(config['exome_bed']))
            else:
                items.append("Mouse WES: targets are the known-gene exon BED of genome_inc/GRCm38.inc, not a "
                             "capture-kit BED. No mouse kit BED was found on lilac. If the kit is known, give "
                             "`--targets-file <kit BED>` (written as exome_bed).")
    ref_notes = list(ref_preset.get('notes') or [])
    if seq_type == 'WGS':
        ref_notes += ref_preset.get('wgs_notes') or []
    for note in ref_notes:
        items.append("Reference {}: {}".format(ref, note))
    if args.ref_fasta:
        items.append("Custom FASTA `{}`: check that every BED uses its contig names and that the .fai, "
                     ".dict and bwa index exist next to it.".format(args.ref_fasta))
    if 'svaba' in args.sv_callers:
        if args.svaba_version == 2:
            items.append("svaba 2.0.0: read `modules/sv_callers/SVABA_SETUP_NOTES.md` (somatic table and "
                         "region-inclusion BED).")
        else:
            items.append("svaba 1.1.0 from SVABA_ENV (`--svaba-version 2` switches to 2.0.0).")
    if args.cluster == 'slurm':
        items.append("Slurm: config.inc has no iris site block. Add one (cluster_backends.md section 3), then "
                     "set `site`, `cluster_queue` and `cluster_extra_args` in project_config.yaml. Tool and "
                     "reference paths still point to lilac ($(HOME)/share).")
    if args.cluster == 'local':
        items.append("`use_cluster: false`: every job runs on this host. Use for tests only.")
    tumor_only = [p for p, n, t in entries if n is None]
    if tumor_only:
        items.append("{} patients are tumor-only ({}): plan a pooled normal or `snv_type: mutect2`.".format(
            len(tumor_only), ', '.join(tumor_only)))
    items.append("Annotation: `ann_pathogen: {}`, `vcf_post_ann_filter_expression: {}`.".format(
        yaml_scalar(config['ann_pathogen']), config['vcf_post_ann_filter_expression']))
    return items


def notes_text(args, config, ref, ref_preset, panel, entries, samples, messages, results, input_kind,
               command_line, project_dir):
    lines = []
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    lines.append("# Setup notes: {}".format(os.path.basename(os.path.abspath(project_dir))))
    lines.append("")
    if args.example:
        lines.append("Example written by `modules/scripts/setup_project.py` (`_docs/examples/make_examples.sh`).")
    else:
        lines.append("Written by `modules/scripts/setup_project.py` on {} (host {}).".format(
            now, socket.gethostname()))
    lines.append("Command: `{}`".format(command_line))
    lines.append("Guide: `modules/_docs/new_project_setup.md`")
    lines.append("")
    lines.append("| Setting | Value |")
    lines.append("|---|---|")
    lines.append("| species | {} |".format(args.species))
    lines.append("| ref | {}{} |".format(ref, ' (custom FASTA)' if args.ref_fasta else ''))
    lines.append("| seq_type | {} |".format(args.seq_type))
    lines.append("| panel / kit | {} |".format(panel['name'] if panel else (args.targets_file or '-')))
    lines.append("| cluster | {} |".format(args.cluster))
    lines.append("| input | {} |".format(input_kind))
    lines.append("| samples | {} ({} tumors, {} normals) |".format(
        len(samples), sum(1 for s in samples if s.type == 'T'), sum(1 for s in samples if s.type == 'N')))
    lines.append("| patients | {} ({} with a normal) |".format(len(entries), sum(1 for e in entries if e[1])))
    lines.append("| SV callers | {} |".format(', '.join(args.sv_callers)))
    lines.append("| indel callers | {} |".format(config['indel_types']))
    lines.append("")
    lines.append("## 1. Check or decide before the first run")
    lines.append("")
    for item in checklist(args, config, ref, ref_preset, panel, entries, samples):
        lines.append("- [ ] " + item)
    lines.append("")
    lines.append("## 2. Sample set-up messages")
    lines.append("")
    if not (messages['notes'] or messages['warnings']):
        lines.append("None.")
    for note in messages['notes']:
        lines.append("- " + note)
    for warn in messages['warnings']:
        lines.append("- WARNING: " + warn)
    lines.append("")
    lines.append("## 3. Preflight")
    lines.append("")
    if results is None:
        lines.append("Not run (`--no-preflight`).")
    else:
        lines.append("Run on host {}. FAIL = must be fixed before the run; WARN = check.".format(
            socket.gethostname()))
        lines.append("")
        lines.append("| Status | Item | Detail |")
        lines.append("|---|---|---|")
        for status, item, detail in results:
            lines.append("| {} | {} | {} |".format(status, item, detail.replace('|', '/')))
    lines.append("")
    lines.append("## 4. Next commands")
    lines.append("")
    sv_targets = ' '.join(SV_CALLER_TARGETS[c] for c in args.sv_callers)
    lines.append("```bash")
    lines.append("cd {}".format('<project>' if args.example else os.path.abspath(project_dir)))
    lines.append("source ~/share/usr/anaconda-envs/jrflab-modules-0.1.4/bin/activate   # configure.py needs PyYAML")
    lines.append("make config                      # writes project_config.inc; re-run after every yaml change")
    lines.append("make -n somatic_variants | grep -c run.py   # dry run: count the jobs it would submit")
    lines.append("make -n facets {}".format(sv_targets))
    lines.append("```")
    lines.append("")
    lines.append("On lilac, run make itself as an LSF job (survives a login-node reboot; skill "
                 "`lilac-genomics-make-driver`):")
    lines.append("")
    lines.append("```bash")
    lines.append("D=~/.ipdot/skills/lilac-genomics-make-driver/scripts/jrflab_make_driver.sh")
    if input_kind.startswith('FASTQ'):
        lines.append("$D bwamem                         # 1. alignment (FASTQ input)")
    elif samples:
        lines.append("# BAMs are linked into bam/: no alignment step")
    else:
        lines.append("$D bwamem                         # 1. alignment (FASTQ input; skip when BAMs are in bam/)")
    wave1 = ['somatic_variants', 'facets'] + [SV_CALLER_TARGETS[c] for c in args.sv_callers]
    if args.seq_type == 'WGS':
        wave1.insert(0, 'wgs_metrics')
    else:
        wave1.insert(0, 'bam_metrics')
    if args.seq_type == 'PANEL' and config['ontarget_file']:
        wave1.append('cnv_kit')
    if args.species == 'human':
        wave1.append('gatk')
    lines.append("for t in {}; do $D $t; done   # 2. read bam/ only; run in parallel".format(' '.join(wave1)))
    if args.species == 'human':
        lines.append("$D mutation_summary   # 3. after somatic_variants (needs a big driver: "
                     "JRFLAB_DRIVER_MEM=64 JRFLAB_DRIVER_MAXMEM=96)")
        lines.append("$D cravat_annotate    # 3. after gatk (germline), then cravat_summary")
    else:
        lines.append("$D mutation_summary   # 3. after somatic_variants (needs a big driver: "
                     "JRFLAB_DRIVER_MEM=64 JRFLAB_DRIVER_MAXMEM=96)")
    lines.append("```")
    lines.append("")
    lines.append("Related: `modules/_docs/mouse_and_seq_type_config.md`, `modules/_docs/cluster_backends.md`, "
                 "`modules/_docs/pipeline_run_checklist.md`.")
    return '\n'.join(lines) + '\n'


# ------------------------------------------------------------------ main

def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog='setup_project.py',
        description='Set up a jrflab-modules project: project_config.yaml, samples.yaml, sample.fastq.yaml, '
                    'BAM links and SETUP_NOTES.md. Guide: modules/_docs/new_project_setup.md',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Sample sheet (--sample-sheet): tab-separated, header optional, columns\n'
               '  sample  type(T|N)  patient  path\n'
               'path = a BAM, an R1 FASTQ (R2 found by name) or a folder of FASTQs for that sample.\n'
               'A sample may have several rows (one per lane or per FASTQ folder).')
    parser.add_argument('--species', choices=['human', 'mouse'], help='required')
    parser.add_argument('--ref', help='b37 (human default), hg19, hg38, GRCm38 (mouse default)')
    parser.add_argument('--seq-type', type=lambda s: s.upper(), choices=SEQ_TYPES, help='required')
    parser.add_argument('--panel', help='panel or exome-kit preset (see --list-panels)')
    parser.add_argument('--targets-file', help='custom panel BED (PANEL) or capture-kit BED (WES), or the '
                                               'WGS targets BED')
    parser.add_argument('--call-intervals-bed', help='chunking BED for mutect/scalpel/lancet (default: '
                                                     'preset)')
    parser.add_argument('--ref-fasta', help='custom FASTA; sets ref_fasta, nochr_ref_fasta and chr_ref_fasta')
    parser.add_argument('--sv-callers', nargs='+', choices=sorted(SV_CALLER_TARGETS),
                        help='default: WGS human manta svaba gridss; WGS mouse manta svaba; WES/PANEL manta')
    parser.add_argument('--indel-callers', nargs='+', choices=INDEL_CALLERS,
                        default=LAB_INDEL_CALLERS.split(), help='default: ' + LAB_INDEL_CALLERS)
    parser.add_argument('--snv-type', choices=['mutect', 'mutect2'], default='mutect')
    parser.add_argument('--strelka-version', type=int, choices=[1, 2],
                        help='default 1; 2 for mouse WGS')
    parser.add_argument('--svaba-version', type=int, choices=[1, 2], default=1,
                        help='1 = svaba 1.1.0 (default), 2 = svaba 2.0.0 (/data/riazlab/lib/bin/svaba)')
    parser.add_argument('--cluster', choices=['lsf', 'slurm', 'local'], default='lsf')
    inputs = parser.add_argument_group('sample input (give one)')
    inputs.add_argument('--fastq-dir', nargs='+', help='FASTQ folders (IGO naming: Sample_<name>_IGO_*/...)')
    inputs.add_argument('--bam-dir', help='folder of <sample>.bam files, linked into bam/')
    inputs.add_argument('--sample-sheet', help='TSV: sample, type T/N, patient, path')
    inputs.add_argument('--config-only', action='store_true',
                        help='write project_config.yaml and SETUP_NOTES.md only (no sample files)')
    parser.add_argument('--project-dir', default='.', help='project directory (default: current)')
    parser.add_argument('--fix-names', action='store_true',
                        help='replace underscores in sample and patient names by hyphens '
                             '(always on for --fastq-dir and --bam-dir)')
    parser.add_argument('--rawdata-link', action='store_true',
                        help='with one --fastq-dir: link it as <project>/rawdata and write rawdata/... paths')
    parser.add_argument('--link-modules', action='store_true',
                        help='link <project>/modules to this modules tree if it is missing')
    parser.add_argument('--no-file-check', action='store_true', help='do not check that FASTQ/BAM files exist')
    parser.add_argument('--no-preflight', action='store_true', help='skip the preflight checks')
    parser.add_argument('--force', action='store_true',
                        help='overwrite existing project_config.yaml / samples.yaml / sample.fastq.yaml '
                             '(old files are kept as *.bak.<time>)')
    parser.add_argument('--dry-run', action='store_true', help='print what would be written; write nothing')
    parser.add_argument('--list-panels', action='store_true', help='list the panel and exome-kit presets')
    # used by _docs/examples/make_examples.sh: no date, host, paths or preflight
    parser.add_argument('--example', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.list_panels:
        return args
    if not args.species or not args.seq_type:
        parser.error('--species and --seq-type are required')
    given = [x for x in (args.fastq_dir, args.bam_dir, args.sample_sheet) if x]
    if len(given) > 1:
        parser.error('give only one of --fastq-dir, --bam-dir, --sample-sheet')
    if not given and not args.config_only:
        parser.error('give --fastq-dir, --bam-dir or --sample-sheet (or --config-only)')
    if args.rawdata_link and not (args.fastq_dir and len(args.fastq_dir) == 1):
        parser.error('--rawdata-link needs exactly one --fastq-dir')
    if args.sv_callers is None:
        args.sv_callers = default_sv_callers(args.species, args.seq_type)
    return args


def list_panels():
    panels = load_yaml(os.path.join(PRESET_DIR, 'panels.yaml'))
    print("{:<20} {:<6} {:<7} {}".format('name', 'kind', 'ref', 'description'))
    for name in sorted(panels):
        p = panels[name]
        print("{:<20} {:<6} {:<7} {}".format(name, p['kind'], p['ref'], p['description']))
        print("{:<20} targets: {}".format('', p['targets_file']))
        if p.get('ontarget_file'):
            print("{:<20} CNVkit:  {}".format('', p['ontarget_file']))


class Plan(object):
    """Collects the file actions so that --dry-run can print them and nothing is half-written."""

    def __init__(self, dry_run, force):
        self.dry_run = dry_run
        self.force = force
        self.actions = []
        self.stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

    def write(self, path, text, overwrite_ok=True, only_if_absent=False):
        self.actions.append(('write', path, text, overwrite_ok, only_if_absent))

    def copy(self, src, dst):
        self.actions.append(('copy', dst, src, True, True))

    def symlink(self, src, dst):
        self.actions.append(('link', dst, src, False, True))

    def check(self):
        problems = []
        for kind, path, _, overwrite_ok, only_if_absent in self.actions:
            if os.path.lexists(path) and not only_if_absent and not self.force:
                problems.append("{} exists (use --force to replace it; the old file is kept as {}.bak.<time>)"
                                .format(path, os.path.basename(path)))
        return problems

    def run(self):
        for kind, path, payload, overwrite_ok, only_if_absent in self.actions:
            exists = os.path.lexists(path)
            if exists and only_if_absent:
                print("  keep    {} (exists)".format(path))
                continue
            if self.dry_run:
                verb = {'write': 'write', 'copy': 'copy', 'link': 'link'}[kind]
                extra = ''
                if kind == 'write':
                    extra = ' ({} lines)'.format(payload.count('\n'))
                elif kind == 'link':
                    extra = ' -> {}'.format(payload)
                print("  would {} {}{}{}".format(verb, path, extra, ' (replacing; backup kept)' if exists else ''))
                continue
            parent = os.path.dirname(path)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
            if exists:
                backup = '{}.bak.{}'.format(path, self.stamp)
                shutil.move(path, backup)
                print("  backup  {}".format(backup))
            if kind == 'write':
                write_text(path, payload)
                print("  wrote   {}".format(path))
            elif kind == 'copy':
                shutil.copy(payload, path)
                print("  copied  {}".format(path))
            else:
                os.symlink(payload, path)
                print("  linked  {} -> {}".format(path, payload))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = parse_args(argv)
    if args.list_panels:
        list_panels()
        return 0
    project_dir = os.path.abspath(expand(args.project_dir))
    shown_argv = list(argv)
    if args.example:
        args.no_preflight = True
        shown_argv = [a for a in argv if a != '--example']
        if '--project-dir' in shown_argv:
            i = shown_argv.index('--project-dir')
            del shown_argv[i:i + 2]
    command_line = 'python modules/scripts/setup_project.py ' + ' '.join(shown_argv)
    messages = {'errors': [], 'warnings': [], 'notes': []}
    try:
        ref, ref_preset, panel = resolve_presets(args)
        samples, input_kind = [], 'none (--config-only)'
        if args.fastq_dir:
            samples = samples_from_fastq_dirs(args.fastq_dir, messages)
            input_kind = 'FASTQ folder'
            args.fix_names = True
        elif args.bam_dir:
            samples = samples_from_bam_dir(args.bam_dir, messages)
            input_kind = 'BAM folder'
            args.fix_names = True
        elif args.sample_sheet:
            samples = samples_from_sheet(args.sample_sheet, messages)
            kinds = set('BAM' if s.bam else 'FASTQ' for s in samples)
            input_kind = 'sample sheet ({})'.format('+'.join(sorted(kinds)))
            if 'FASTQ' in kinds:
                input_kind = 'FASTQ ' + input_kind
            if len(kinds) > 1:
                messages['warnings'].append("the sheet mixes FASTQ and BAM samples; FASTQ samples are aligned "
                                            "(bwamem), BAM samples are linked into bam/")
        entries = []
        if samples:
            fix_and_check_names(samples, args.fix_names, messages)
            if not args.no_file_check:
                check_files(samples, messages)
            entries = build_pairs(samples, messages)
            if not any(normal for _, normal, _ in entries):
                messages['warnings'].append("no tumor/normal pair: samples.yaml has tumor-only entries only")

        config = build_config(args, ref, ref_preset, panel)
        if args.seq_type == 'PANEL' and not config['targets_file']:
            raise SetupError("PANEL needs a targets_file")

        results = None if args.no_preflight else preflight(config, ref_preset, args, project_dir)
        if args.link_modules and not os.path.exists(os.path.join(project_dir, 'modules')) and results:
            results = [r for r in results if r[1] != 'modules/ in project']
            results.append(('OK', 'modules/ in project', 'will be linked to {}'.format(MODULES_DIR)))
    except SetupError as err:
        sys.stderr.write("ERROR: {}\n".format(err))
        return 1

    for warn in messages['warnings']:
        print("WARNING: " + warn)
    if messages['errors']:
        for err in messages['errors']:
            sys.stderr.write("ERROR: {}\n".format(err))
        sys.stderr.write("{} errors; nothing was written.\n".format(len(messages['errors'])))
        return 1

    # ---- plan the files
    plan = Plan(args.dry_run, args.force)
    if args.link_modules and not os.path.lexists(os.path.join(project_dir, 'modules')):
        plan.symlink(MODULES_DIR, os.path.join(project_dir, 'modules'))
    if not args.example:
        plan.write(os.path.join(project_dir, 'Makefile'), 'include modules/Makefile\n', only_if_absent=True)
        plan.copy(os.path.join(MODULES_DIR, 'default_yaml', 'summary_config.yaml'),
                  os.path.join(project_dir, 'summary_config.yaml'))

    sv_targets = ' '.join(SV_CALLER_TARGETS[c] for c in args.sv_callers)
    header = ['# Written by setup_project.py{}:'.format(
        '' if args.example else ' on ' + datetime.date.today().isoformat()),
              '#   ' + command_line,
              '# Case: species {}, ref {}, seq_type {}{}. Checklist: SETUP_NOTES.md'.format(
                  args.species, ref, args.seq_type, ', panel ' + panel['name'] if panel else '')]
    config_text = render_template(config, header, sv_targets)
    plan.write(os.path.join(project_dir, 'project_config.yaml'), config_text)

    if samples:
        plan.write(os.path.join(project_dir, 'samples.yaml'), samples_yaml_text(entries))
        fastq_samples = [s for s in samples if s.fastq_pairs]
        if fastq_samples:
            rewrite = lambda p: p
            if args.rawdata_link:
                fastq_root = os.path.abspath(expand(args.fastq_dir[0]))
                link = os.path.join(project_dir, 'rawdata')
                if os.path.lexists(link) and os.path.realpath(link) != os.path.realpath(fastq_root):
                    sys.stderr.write("ERROR: {} exists and does not point to {}\n".format(link, fastq_root))
                    return 1
                plan.symlink(fastq_root, link)
                rewrite = lambda p: os.path.join('rawdata', os.path.relpath(p, fastq_root))
            plan.write(os.path.join(project_dir, 'sample.fastq.yaml'), sample_fastq_yaml_text(fastq_samples,
                                                                                            rewrite))
        for sample in samples:
            if sample.bam:
                plan.symlink(os.path.abspath(sample.bam), os.path.join(project_dir, 'bam', sample.name + '.bam'))
                if sample.bai:
                    plan.symlink(os.path.abspath(sample.bai),
                                 os.path.join(project_dir, 'bam', sample.name + '.bam.bai'))

    notes = notes_text(args, config, ref, ref_preset, panel, entries, samples, messages, results, input_kind,
                       command_line, project_dir)
    plan.write(os.path.join(project_dir, 'SETUP_NOTES.md'), notes)

    problems = plan.check()
    if problems:
        for problem in problems:
            sys.stderr.write("ERROR: {}\n".format(problem))
        sys.stderr.write("nothing was written.\n")
        return 1

    print("Project {}: species {}, ref {}, seq_type {}{}; {} samples, {} patients".format(
        project_dir, args.species, ref, args.seq_type, ', panel ' + panel['name'] if panel else '',
        len(samples), len(entries)))
    if results is not None:
        n_fail = sum(1 for r in results if r[0] == 'FAIL')
        n_warn = sum(1 for r in results if r[0] == 'WARN')
        print("Preflight: {} FAIL, {} WARN, {} OK (details in SETUP_NOTES.md)".format(
            n_fail, n_warn, len(results) - n_fail - n_warn))
        for status, item, detail in results:
            if status != 'OK':
                print("  {:<4} {}: {}".format(status, item, detail))
    if args.dry_run:
        print("Dry run: nothing written. Planned actions:")
    plan.run()
    if args.dry_run:
        print("\nActive keys of project_config.yaml:")
        for line in config_text.splitlines():
            if line and not line.startswith(('#', '---', '...')):
                print("  " + line)
    else:
        print("Next: read {}, then `make config`.".format(os.path.join(project_dir, 'SETUP_NOTES.md')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
