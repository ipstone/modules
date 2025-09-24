# Title:
   Conda Environments

# Purpose
   Track the exact package sets required by the pipeline and document how to
   rebuild them on a new system.

# Where Things Live
   - `conda_env/*.txt` - explicit dependency manifests generated with
     `conda list --explicit`.  Example files include
     `jrflab_modules_env.txt`, `sufam_env.txt`, `varscan_env.txt`, etc.
   - `config.inc` - binds those environments to Make variables such as
     `JRFLAB_MODULES_ENV`, `SUFAM_ENV`, `ASCAT_ENV`, `POLYSOLVER_ENV`, and more.
     Targets reference these variables via `-v $(ENV)` when they need to
     activate a Conda environment.

# Recreating an Environment
```
# install directly from an explicit spec
conda create --name jrflab-modules --file conda_env/jrflab_modules_env.txt

# or update an existing env in place
conda install --name jrflab-modules --file conda_env/jrflab_modules_env.txt
```
   After creating the environment, ensure `config.inc` points to the activation
   path (e.g. `JRFLAB_MODULES_ENV = /path/to/jrflab-modules`).

# Updating the Specs
1. Activate the environment you modified.
2. Run `conda list --explicit > conda_env/<name>_env.txt` to refresh the lock
   file (remove platform-specific paths if necessary).
3. Commit the updated manifest alongside code that depends on the new packages.

# Tips
- Keep environment names and variables aligned with the defaults in
  `config.inc` to avoid editing multiple makefiles.
- When adding a brand-new environment, update `config.inc` so downstream targets
  can locate it and drop a corresponding `conda_env/<env>.txt` for reproducible
  rebuilds.
- Use the `-v $(ENV)` flag already present in most recipes if you simply need to
  swap in a refreshed environment path.
