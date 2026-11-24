ifndef MANTA_INC
CONFIG_MANTA = $(HOME)/share/usr/manta-0.29.6.centos5_x86_64/bin/configManta.py
# Manta --exome mode: on for SEQ_TYPE = WES or PANEL, off for WGS. With
# SEQ_TYPE unset the old rule applies: --exome whenever TARGETS_FILE is set.
# Set MANTA_EXOME = true/false in the project to force either mode.
MANTA_EXOME ?= $(if $(SEQ_TYPE),$(if $(filter WES PANEL,$(SEQ_TYPE)),true,false),$(if $(TARGETS_FILE),true,false))
MANTA_EXOME_OPT = $(if $(findstring true,$(MANTA_EXOME)),--exome)
CONFIG_MANTA_OPTS ?= --referenceFasta $(REF_FASTA) --config modules/sv_callers/manta_config.py.ini $(MANTA_EXOME_OPT)
MANTA_HS_CONFIG = modules/sv_callers/manta_hs_config.py.ini
MANTA_CONFIG = modules/sv_callers/manta_config.py.ini
MANTA_HIGH_SENS ?= false
CONFIG_MANTA_OPTS = --referenceFasta $(REF_FASTA) \
		    --config $(if $(findstring true,$(MANTA_HIGH_SENS)),\
		    				    $(MANTA_HS_CONFIG),$(MANTA_CONFIG)) \
		    $(MANTA_EXOME_OPT) \
		    $(if $(MANTA_REGION),--region $(MANTA_REGION))
endif
MANTA_INC = true
