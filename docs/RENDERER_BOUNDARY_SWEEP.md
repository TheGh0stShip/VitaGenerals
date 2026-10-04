# Renderer boundary reference sweep

`reports/generated/renderer-boundary.json.gz` records graphics-boundary identifier
sites across all 2,961 scanned C/C++ source/header files in the pinned Zero Hour
Code tree. It contains 8,697 sites in 176 files, grouped into 792 distinct symbol
spellings. Source hashes and relative file/line provenance are retained.
Deterministic compression permits byte-for-byte reproduction.

| Category | Distinct spellings |
| --- | ---: |
| DX8Wrapper members | 214 |
| DX8CALL device-call methods, retaining macro variant | 33 |
| Texture/surface formats | 43 |
| Render states / texture-stage states | 74 / 31 |
| Vertex-layout identifiers / primitive types | 20 / 4 |
| Resource usage / locking | 7 / 5 |
| D3DX helper identifiers / device interfaces | 30 / 11 |
| CLASSID identifiers | 71 |
| Other D3D identifiers | 249 |

These are source spellings, not API implementations, executed submissions,
unique renderer classes or defects. The tree also contains tools and legacy
paths; none are discarded as unnecessary. A repeated symbol site remains a
separate reference. CLASSID spellings require hierarchy/owner review before
being used as a runtime renderer-object denominator.

The original boundary is Direct3D8/D3DX8. `dx8wrapper.h` defines `DX8CALL` and
`DX8CALL_HRES` around the original device, and `DX8CALL_D3D` around its Direct3D
interface. `dx8wrapper.cpp` submits indexed primitives through these macros.
Terrain, texture/buffer and shader owners retain their original higher-level
responsibilities. A new graphics backend must replace the device boundary
without introducing a replacement scene graph.

| Gap | Priority | Dependency / evidence needed |
| --- | --- | --- |
| Original renderer absent from target engine build | Blocking | Original W3D dependency staging and target graphics boundary |
| Complete render-object/material/submission routes unknown | Required | Hierarchy, state cache, sorting and pass ownership sweep |
| Format/state equivalence unverified | Required | Original conversion paths and Vita capability/visual checks |
| Macro and indirect call paths unresolved | Required | Preprocessor expansion, COM/direct-call owners and generated shaders |
| Build/configuration reachability unknown | Required | Target definitions, selected sources and linker evidence |
| Memory, timing and visual behavior unverified | Required | Physical Vita/PSTV captures, RAM/CDRAM high-water data and fixed replays |

The lexical scanner masks comments and ordinary literals. It records identifier
references and preliminary include candidates without evaluating preprocessing.
Raw strings, aliases, generated code and full C++ parsing remain outside scope.
Includes inside inactive branches or comments may remain candidates. This
inventory is not the complete renderer sweep or evidence of a usable backend.

```sh
python3 tools/audit_renderer_boundary.py --source build-source-ci/GeneralsMD/Code \
  --output build-arm-ci/renderer-boundary.json.gz
cmp reports/generated/renderer-boundary.json.gz build-arm-ci/renderer-boundary.json.gz
```
