# DEPRECATED (2026-11-24): use scripts/setup_project.py --fastq-dir instead. Kept for old projects;
# reasons and decisions: _docs/new_project_setup.md, section 'Old setup scripts'.
# To generate samples.yaml and sample.fastq.yaml though the list of fastq
# files
#
all: _samples.yaml _sample.fastq.yaml

_samples.yaml: fq_filelist.txt 
	python modules/scripts/prepare_samples/fastq_to_samples/setup_samples.py > _samples.yaml

_sample.fastq.yaml: fq_filelist.txt
	python modules/scripts/prepare_samples/fastq_to_samples/setup_fastq.py > _sample.fastq.yaml

fq_filelist_wes.txt:
	ls rawdata/*.fastq.gz > fq_filelist.txt


