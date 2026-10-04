# Original runtime provider sweep

`reports/generated/runtime-providers.json` joins the pinned original project
inventory with raw DSP target types and typed linker/librarian directives.
All 50 original DSP files are covered. Raw input provenance, configuration
names, directive lines and branch activity are retained; no hooks execute.

The RTS workspace ordering closure has 24 projects: 15 static-library targets,
four executable targets and five missing GameSpy projects. The executables are
RTS, launcher, versionUpdate and buildVersionUpdate. A workspace dependency
can order a build tool or launcher without linking its code into the game.
Runtime necessity remains unresolved for every project.

Explicit RTS `.lib` arguments match output-name candidates from nine original
static-library projects across the union of configurations: GameEngine,
GameEngineDevice, Benchmark, WW3D2, WWDebug, WWDownload, WWLib, WWMath and WWUtil.
This is not the complete runtime provider set, nor proof of exact file identity.
Original libraries not directly matched must not be removed: default/pragma
inputs, archive symbol pulls and transitive dependencies remain open.

`/nodefaultlib` arguments are excluded defaults, not linked inputs. `/out`,
`/implib` and `/libpath` are recorded separately. The earlier project inventory's
`build_tokens` field intentionally retains generic tokens; it must not be used
as a typed library-input list. Output/import-library basename matches retain
all provider/configuration candidates. Actual search-path resolution, artifact
identity and compatible configuration pairing require further evidence.
Workspace paths use the original inventory's case-resolved candidates;
collisions remain unresolved.

| Gap | Priority | Dependency / evidence needed |
| --- | --- | --- |
| Runtime roles remain unproven | Blocking | Original caller, launcher/build-hook and authored content evidence |
| Missing GameSpy projects | Blocking | Original APIs, service-provider replacements and licensing review |
| Configuration pairing and final library identity | Required | Search paths, output artifacts, target definitions and link evidence |
| Transitive/default/pragma providers | Required | Source pragmas, archive symbols and linker resolution |
| Non-Windows platform/middleware boundaries | Blocking | Original interfaces, license obligations and audited replacements |

Original RTS link lines also reference Direct3D8/D3DX8, Windows system libraries,
Bink and Miles providers. Their replacement and licensing contracts are open;
source/project presence does not establish redistribution permission or target
compatibility. Preserve original subsystem ownership while replacing boundaries.
The [consolidated ledger](PORT_GAPS.md) keeps these observations inside existing
source/dependency findings rather than counting them as additional defects.

```sh
python3 tools/audit_runtime_providers.py --source build-source-ci/GeneralsMD/Code \
  --output build-arm-ci/runtime-providers.json
cmp reports/generated/runtime-providers.json build-arm-ci/runtime-providers.json
```
