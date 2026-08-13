# notebook_source/ — provenance archive, not an implementation

These are the v15 notebook cells the package was extracted from, kept
read-only for diffing (`diff notebook_source/cells/222.py <(sed ...)
src/dci/pipeline/stages/c222_gate0_selftest.py`) and for the migrator
(`tools/migrate_v15.py`), which regenerates `src/dci/pipeline/stages/` from
them. The package is the single authoritative implementation; do not edit the
science here. Post-migration notebooks should be thin clients that `import
dci` and read run artifacts.
