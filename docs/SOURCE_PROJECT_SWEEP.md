# Original project and source sweep

The recorded scope is every supplied Zero Hour `Code` VC6 project/workspace
and every C/C++ translation unit in that tree. It establishes original project
references and configuration selection, not complete runtime ownership.

Machine-readable snapshot:
[original-projects.json.gz](../reports/generated/original-projects.json.gz).
It is compressed JSON, containing relative paths, source/project hashes,
source-line anchors, configuration selections, workspace dependencies, missing
references and explicit unknowns. It contains no retail content or local roots.

| Evidence | Count |
| --- | ---: |
| Project files | 50 |
| Workspace files | 12 |
| Translation units | 1,436 |
| Units without an original project reference | 69 |
| Original source references resolved | 2,975 |
| Missing source references | 162 |
| References outside Code or using unresolved substitutions | 224 |
| Configuration conditions evaluated | 1,542 |
| Unsupported configuration conditions in this snapshot | 0 |
| Custom build hook sites retained as metadata | 136 |
| Missing workspace project references | 6 |
| Original units selected by the retained ARM compile database | 1 |

Exclusions are per configuration. Custom-build `SOURCE=$(InputPath)` variables
are not source declarations. Windows paths are resolved case-insensitively
with collisions explicit. Unknown branch conditions stay unknown; unsupported
IDE directives fail parsing. The audit executes no original build hooks. A source-tree fingerprint verifies
the entire supplied Code tree against the pinned pristine baseline.

Five missing workspace projects are RTS dependencies for GameSpy HTTP,
patching, peer, presence and statistics. The sixth belongs to the Autorun
English workspace. Missing source references include headers/resources and
unavailable library code; they are not 162 confirmed runtime defects.
References outside Code include original retail INI/WND paths. The 69 units
without project references need caller/build-role review before disposition.

Port selection is joined to an ARM Vita compile database and the import
manifest. An omitted database means unknown selection. The selected original
unit is WWLib realcrc.cpp. Source selection and linkage do not prove correct
registrar execution, implementation completeness or gameplay use.

```sh
python3 tools/audit_original_projects.py --source /path/to/GeneralsMD/Code \
  --compile-commands build-arm-ci/compile_commands.json \
  --output build-arm-ci/reproduced-projects.json
python3 tools/verify_project_inventory.py build-arm-ci/reproduced-projects.json
python3 -m unittest discover -s tests -p 'test_*.py'
```

Next: classify original runtime/tool/build-provider roles with caller evidence,
then inventory static module/script/loader registrars and join matching symbols.
The complete runtime exclusion sweep remains open; renderer, guards/stubs,
content, scripts/systems and all physical acceptance sweeps remain open.

ARM CI fetches the exact official source commit and regenerates this snapshot.
The comparison excludes only the machine-specific compile database hash;
original-source metadata and selected-source facts must match.
