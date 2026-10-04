# Source structure and return sweep

`reports/generated/source-structure.json.gz` records unpreprocessed parsed
structure across all 2,961 C/C++ source/header files in the pinned Zero Hour
Code tree. Files are not discarded based on role or build selection; C inputs
use the C++ grammar. The original tree fingerprint and every input SHA256 are
verified. Legacy text is explicitly transcoded from Latin-1 to UTF-8 for parsing;
reported line coordinates refer to the original file, not UTF-8 byte offsets.

The initial inventory contains 37,515 callable-definition nodes (including
lambdas), 5,767 class/struct nodes, 6,758 conditional guard nodes and 33,387 return
nodes. There are 8,561 literal-return candidates. Empty-body and sole-return
flags are candidates for review, not stub classifications. Ordinary getters,
validation failures and intentional no-ops must retain their original behavior.

The parser reports 14,677 error/missing-node records across 1,223 files. These
are structural coverage gaps, not counts of source defects. File and callable
error flags remain attached to records; recovered output cannot establish a
complete function denominator. Macro-heavy declarations, legacy constructs and
unpreprocessed branches require configuration-aware reconciliation.

Returns retain the nearest parsed callable owner, including nested lambdas.
Guard records preserve directive spelling, condition text and syntax-tree
ancestry; `#ifndef` is distinct from `#ifdef`. An `#else` descendant's ancestry
is not a conjunction of active conditions. No branch truth is asserted.
Class context is lexical nesting, not a resolved inheritance/name graph.

| Gap | Priority | Dependency / evidence needed |
| --- | --- | --- |
| Parser recovery reconciliation | Blocking for complete census | Target preprocessing and original declaration/macro owners |
| Runtime/tool and build selection roles | Required | Original projects, target compile commands and caller evidence |
| Stub, unsupported and early-exit behavior | Required | Original helper implementations, control flow and runtime contracts |
| Guard reachability | Required | Configuration definitions, includes and macro expansion |
| System/renderer/input ownership | Required | Join structured callables to subsystem interfaces and authored content |
| Physical behavior | Required | Complete game execution and acceptance on Vita/PSTV |

Host tooling uses hash-pinned binary wheels for
[Tree-sitter Python bindings](https://github.com/tree-sitter/py-tree-sitter)
0.25.2 and the [C++ grammar](https://github.com/tree-sitter/tree-sitter-cpp)
0.23.4. Both packages are MIT licensed and are not linked into the game.
`tools/parser-requirements.txt` restricts installation to reviewed Linux x86-64
CPython 3.12 wheels; source build hooks are prohibited. Tool versions and the
requirements hash are recorded in the inventory. Different versions fail the
scan. Tests cover nested ownership, ordinary/raw literals, legacy encoding,
conditional alternatives, empty/sole returns and explicit parser recovery.

```sh
python3.12 -m venv build-parser
build-parser/bin/python -m pip install --only-binary=:all: --require-hashes -r tools/parser-requirements.txt
build-parser/bin/python tools/audit_source_structure.py --source build-source-ci/GeneralsMD/Code \
  --output build-arm-ci/source-structure.json.gz
python3 tools/compare_report.py reports/generated/source-structure.json.gz build-arm-ci/source-structure.json.gz
```

A successfully parsed node does not establish target ABI, linker retention,
registration execution, behavior completeness or physical performance.
