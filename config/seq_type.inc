# vim: set ft=make :
# Sequencing type and species switches.
# Included by Makefile.inc BEFORE modules/genome_inc/$(REF).inc, because the
# genome include reads EXOME to decide TARGETS_FILE and CHROMOSOMES.
#
# SEQ_TYPE (project_config.yaml key: seq_type) = WGS | WES | PANEL
#   WGS   : EXOME = false; Manta runs without --exome; WGS resource profile.
#   WES   : EXOME = true (TARGETS_FILE = EXOME_BED of the genome include);
#           Manta runs with --exome; WES resource profile.
#   PANEL : EXOME = false; TARGETS_FILE must be set in the project config;
#           Manta runs with --exome; WES resource profile.
#   unset : old behaviour. EXOME is left as configured, Manta adds --exome
#           when TARGETS_FILE is non-empty, and the WGS resource profile is
#           used (the resource values this fork used before SEQ_TYPE existed).
# Full description: _docs/mouse_and_seq_type_config.md
ifndef SEQ_TYPE_INC

# configure.py writes "None" for an empty yaml value; treat it as unset
ifneq ($(filter None none null,$(SEQ_TYPE)),)
override SEQ_TYPE :=
endif
SEQ_TYPE := $(strip $(SEQ_TYPE))

ifneq ($(SEQ_TYPE),)
ifneq ($(filter WGS wgs,$(SEQ_TYPE)),)
override SEQ_TYPE := WGS
EXOME = false
else ifneq ($(filter WES wes,$(SEQ_TYPE)),)
override SEQ_TYPE := WES
EXOME = true
else ifneq ($(filter PANEL panel,$(SEQ_TYPE)),)
override SEQ_TYPE := PANEL
EXOME = false
ifeq ($(strip $(TARGETS_FILE)),)
$(error SEQ_TYPE=PANEL needs targets_file (TARGETS_FILE) set to the panel BED in project_config.yaml)
endif
else
$(error SEQ_TYPE='$(SEQ_TYPE)' is not valid; use WGS, WES or PANEL, or leave it unset)
endif
endif

# BED used to split the genome into chunks / calling intervals (mutect,
# mutect2, scalpel, lancet). Defaults to TARGETS_FILE; set it separately when
# the calling intervals differ from the capture targets.
CALL_INTERVALS_BED ?= $(TARGETS_FILE)

# Resource profile (cluster memory, walltime, threads). Every value is a
# ?= default, so project_config.inc / config.inc can override single values.
ifneq ($(filter WES PANEL,$(SEQ_TYPE)),)
RESOURCE_PROFILE ?= wes
else
RESOURCE_PROFILE ?= wgs
endif
include modules/config/profiles/$(RESOURCE_PROFILE).inc

endif
SEQ_TYPE_INC = true
