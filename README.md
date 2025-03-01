# This is a folk from jrflab/modules. This module is BEING tailored for WGS analysis.
[![Build Status](https://travis-ci.org/cBioPortal/cbioportal.svg?branch=master)](https://travis-ci.org/jrflab/modules)

# Summary
  To start a new project:

            `git clone https://github.com/jrflab/modules.git`

            `./modules/init_project`  or 

            `perl modules/scripts/initProject.pl` 


# Getting started
    [wiki](https://github.com/jrflab/modules/wiki).

# Known issues

# Updates

## April 2024 - mouse_wgs branch
- Fixed `yaml.load()` calls in `scripts/configure.py` to include the required `Loader=yaml.SafeLoader` parameter for compatibility with newer PyYAML versions
- Added mouse genome support and WGS pipeline modifications
- Updated various makefiles for mouse WGS analysis:
  - Modified copy number analysis modules (cnvkit, facets)
  - Updated variant callers for mouse genome compatibility
  - Added mouse-specific genome references in genome_inc
  - Improved summary generation for mouse WGS data
