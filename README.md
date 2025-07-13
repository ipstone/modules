# modules_ipstone: WGS-Optimized Bioinformatics Pipeline

This is a fork from jrflab/modules, specifically tailored and optimized for **Whole Genome Sequencing (WGS)** analysis. The pipeline includes enhanced resource allocation, WGS-specific tools, and comprehensive documentation.

[![Build Status](https://travis-ci.org/cBioPortal/cbioportal.svg?branch=master)](https://travis-ci.org/jrflab/modules)

## Quick Start

### For Human WGS Analysis:
```bash
git clone https://github.com/ipstone/modules.git
cd modules
git checkout master  # Default branch
./init_project
```

### For Mouse WGS Analysis:
```bash
git clone https://github.com/ipstone/modules.git
cd modules  
git checkout mouse_wgs
./init_project
```

### For Mouse Exome Analysis:
```bash
git clone https://github.com/ipstone/modules.git
cd modules
git checkout mouse
./init_project
```

## Project Initialization

After cloning, initialize a new project:
```bash
./modules/init_project
# or
perl modules/scripts/initProject.pl
```

## Key Features by Branch

| Feature | master | mouse_wgs | mouse | merge_jrflab |
|---------|--------|-----------|-------|-------------|
| **Human WGS Optimized** | ✅ | ❌ | ❌ | ✅ |
| **Mouse Genome Support** | ❌ | ✅ | ✅ | ❌ |
| **MIMSI Analysis** | ✅ | ❌ | ❌ | ❌ |
| **Enhanced Documentation** | ✅ | ❌ | ❌ | ✅ |
| **Resource Optimization** | ✅ | ✅ | ❌ | ✅ |
| **GNU Make 3.82 Compatible** | ✅ | ❌ | ✅ | ✅ |

## Getting Started
- [Documentation](https://github.com/jrflab/modules/wiki)
- [Module Documentation](_docs/README_docs.md) (master branch)
- [Configuration Examples](_docs/examples/) (master branch)

## Requirements
- GNU Make 3.82 or newer is required
- Cluster environment with SGE/PBS/LSF support (recommended)
- Conda environments for tool dependencies (see config.inc)

## Support
For issues specific to WGS optimizations or ipstone modifications, please contact the development team. For general jrflab/modules issues, refer to the [original repository](https://github.com/jrflab/modules).

## Branch Overview

This repository maintains several specialized branches for different analysis scenarios:

### 🔬 **master** (Current)
- **Purpose**: Production-ready WGS analysis with latest updates
- **Features**: 
  - WGS-optimized resource allocation (20G Picard memory, enhanced threading)
  - MIMSI analysis for microsatellite instability detection
  - Comprehensive documentation in `_docs/` directory
  - GNU Make 3.82 compatibility
- **Last Updated**: 2025-07-12
- **Use Case**: Primary branch for human WGS projects

### 🔄 **merge_jrflab** 
- **Purpose**: Historical merge point of jrflab updates into ipstone
- **Features**: 
  - Integration of jrflab modules while preserving WGS optimizations
  - Updated genome references (dmp/current WGS reference)
- **Date**: 2019-08-16
- **Use Case**: Reference for understanding jrflab integration history

### 🐭 **mouse**
- **Purpose**: Mouse genome analysis (exome/targeted sequencing)
- **Features**:
  - Mouse reference genome (mm10) configuration
  - Deletion microhomology analysis adapted for mouse
- **Date**: 2020-02-28  
- **Use Case**: Mouse exome sequencing projects

### 🐭 **mouse_wgs**
- **Purpose**: Mouse whole genome sequencing analysis
- **Features**:
  - Mouse WGS pipeline modifications
  - Enhanced memory specifications for somatic indel analysis
  - YAML loader parameter fixes
  - 12+ commits of mouse-specific optimizations
- **Last Updated**: 2025-03-06
- **Use Case**: Mouse WGS projects

### 🧪 **i238**
- **Purpose**: Testing and validation branch
- **Features**:
  - Test cases for variant classification
  - Pathogenicity prediction validation
  - Sample test outputs
- **Date**: 2017-07-26
- **Use Case**: Development testing and validation
