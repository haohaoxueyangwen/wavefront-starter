# Code provenance

The speckle reference code derives from Zhi Qiao / UChicago Argonne (2020), with subsequent local WSVT project modifications. Its original copyright and redistribution terms are retained in every copied module and LICENSE-ARGONNE.txt.

This educational distribution is a modified local packaging, not the original ANL release. Solver function bodies are preserved; personal command-line demos are removed. Grating and Zernike primitives were extracted from the user's historical code. Hartmann centroid primitives were extracted from the user's existing hartmann_V2 repository at the recorded commit.

Version 0.3.1 removes unreferenced legacy helpers from the bundled speckle modules. The WXST and WSVT solver class bodies and their seven required helper bodies remain unchanged. Original source identifiers and hashes are retained in sources.json; the cleanup inventory and before/after synthetic-array comparison are in validation/cleanup.json. The internal vendor helper collection is not a supported public API; use wfs_starter.core or the CLI.

New adapters, configuration validation, examples and documentation are new teaching material. The historical Zernike index helper was not copied: inspection found that j=1 maps to an invalid (n,m). The teaching fitter uses explicit (n,m) modes and records them in every result; original research files were not edited.

The source repository excludes raw experimental arrays, training weights, PDF papers, credentials and workstation absolute paths. Documentation includes selected CRL data previews. Original workstation locations are recorded in a separate local deliverable.

Version 0.4.1 bundles the user's complete `analysis_zernike.py` as an unchanged source snapshot (`advanced_zernike_original.py`). The original function generates the full report and numerical maps. `advanced_zernike.py` replaces the invalid historical Noll mapping in the worker's module instance and converts photon energy to wavelength in correct micrometre units. Source hashes, GUI control coverage and correction references are recorded in zernike_full.json and docs/10_zernike_parity.md. The vendor file's standalone historical main is not the supported launcher; use the complete `zernike_full` CLI/UI entry.

Version 0.5.0 freezes native CPU/GPU deployment sources from WSVT_CPP commit 3f418aa71771e9d209af0702b742ac7e7a69aa9a. File hashes and selections are in native_speckle_050.json; original code bytes and source notices are preserved. The new teaching bridge and examples are separate files. This package does not add an umbrella license or redistribute experiment arrays, binaries or machine credentials.

Version 0.6.0 adds Windows portability overlays applied only to build copies, automatic native discovery, and public release assets containing app-local runtimes. The original 147-file source snapshot remains hash-identical. Source/binary/patch hashes are recorded in windows_native_build.json; component terms and corresponding FFTW sources accompany the Windows release. GPU and CPU executables remain separate; no real experiment data or local machine configuration is distributed.

Version 0.6.1 replaces default speckle examples with the user-selected BB11 CRL acquisition. Windows and the separate data ZIP include an exact 512-square uint16 crop of 100 reference/sample pairs. provenance/crl_bb11_example.json records original and crop hashes, crop indices, sample identity and historical calibration. No original experiment files or notebooks are modified or redistributed in full. Native algorithms and binaries remain unchanged.
