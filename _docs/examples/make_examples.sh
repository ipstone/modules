#!/bin/bash
# Regenerate the per-case examples in _docs/examples/<case>/ with
# scripts/setup_project.py, so that they always match the script and the
# presets. Run from the modules directory:  bash _docs/examples/make_examples.sh
# Writes only project_config.yaml and SETUP_NOTES.md (no samples, no preflight).
set -e
cd "$(dirname "$0")/../.."
PY=${PY:-python}
run() {
    case_name=$1; shift
    mkdir -p _docs/examples/$case_name
    rm -f _docs/examples/$case_name/project_config.yaml _docs/examples/$case_name/SETUP_NOTES.md
    $PY scripts/setup_project.py "$@" --config-only --example --project-dir _docs/examples/$case_name > /dev/null
    echo "wrote _docs/examples/$case_name"
}
run human_wgs             --species human --seq-type WGS
run human_wes             --species human --seq-type WES --panel xgen_exome_v2
run human_panel_impact505 --species human --seq-type PANEL --panel IMPACT505
run mouse_wes             --species mouse --seq-type WES
run mouse_wgs             --species mouse --seq-type WGS
