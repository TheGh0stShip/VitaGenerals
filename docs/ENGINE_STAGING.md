# Complete original source staging

`tools/stage_engine_tree.py` prepares all 3,197 files from the pinned Zero Hour
Code tree without changing upstream or executing original project/build hooks.
It includes source, headers and original build metadata without deciding which
files are unnecessary. Runtime selection and provider pairing remain separate.

```sh
python3 tools/fetch_source_baseline.py --directory build-source-ci
python3 tools/stage_engine_tree.py --source build-source-ci/GeneralsMD/Code \
  --output build-engine/staged --summary build-engine/engine-stage-baseline.json
cmp reports/generated/engine-stage-baseline.json build-engine/engine-stage-baseline.json
```

The output contains `Code/`, the byte-preserved EA `LICENSE.md` and a private
`receipt.json` with every staged file hash. The complete pristine Code fingerprint
must match `tools/source-lock.json`. Declared patch inputs must match that tree
and the vendored manifest. The existing zero-fuzz patch pipeline produces the
two patched WWLib checksum files; they are mapped back to their original paths.
Every final file is verified against original or declared patched bytes before
promotion. License bytes must match the preserved project license.

`reports/generated/engine-stage-baseline.json` publishes only source/recipe/tree
identity and staging counts. It is reproducible from the pinned source checkout;
its full file receipt and source copies stay in ignored build directories.
This is source-staging evidence, not an engine compilation, package or runtime
acceptance result. The current CMake probes still select the small checksum and
archive baselines; the complete staged tree is preparation for original engine
build clusters, not an implicitly selected runtime graph.

Staging output must be a subdirectory of an ignored project build tree. Dirty
source inputs, symlinks, altered staged files, unexpected files, license or patch
mismatches fail. A clean generation with identical receipt keeps its existing
file times. Metadata changes during generation fail before publication.
Cooperating stagers serialize with an advisory lock. Promotion preserves the
previous generation on ordinary exceptions, including a failed final rename.

Run staging with build consumers idle. Directory promotion uses two same-parent
renames with rollback; it is not crash-atomic. An interrupted process can leave
an absent output and a scratch generation. Rebuild from verified pristine inputs
before consuming such output. No source or retail files are modified. No claim
of full engine or physical Vita/PSTV correctness follows from successful staging.
