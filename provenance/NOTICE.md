# Code provenance

The speckle reference code derives from Zhi Qiao / UChicago Argonne (2020), with subsequent local WSVT project modifications. Its original copyright and redistribution terms are retained in every copied module and LICENSE-ARGONNE.txt.

This educational distribution is a modified local packaging, not the original ANL release. Solver function bodies are preserved; personal command-line demos are removed. Grating and Zernike primitives were extracted from the user's historical code. Hartmann centroid primitives were extracted from the user's existing hartmann_V2 repository at the recorded commit.

Version 0.3.1 removes unreferenced legacy helpers from the bundled speckle modules. The WXST and WSVT solver class bodies and their seven required helper bodies remain unchanged. Original source identifiers and hashes are retained in sources.json; the cleanup inventory and before/after synthetic-array comparison are in validation/cleanup.json. The internal vendor helper collection is not a supported public API; use wfs_starter.core or the CLI.

New adapters, configuration validation, examples and documentation are new teaching material. The historical Zernike index helper was not copied: inspection found that j=1 maps to an invalid (n,m). The teaching fitter uses explicit (n,m) modes and records them in every result; original research files were not edited.

No real experimental arrays, training weights, PDF papers, credentials or workstation absolute paths are included in this repository. Original workstation locations are recorded in a separate local deliverable.
