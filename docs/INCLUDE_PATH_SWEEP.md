# Original include path sweep

The pinned Code tree contains 17,587 lexical include sites across 2,961 C/C++
source and header files: 15,713 quoted and 1,874 angled operands. The scan retains
inactive branches without evaluating
configuration reachability. It does not select headers or establish compilation.

`reports/generated/include-paths.json.gz` records source hashes, physical lines,
original operands, normalized paths and all matching candidates. There are 190
backslash spellings, 463 sites with case-insensitive source-relative matches but
no normalized exact match, and 1,685 sites with multiple suffix candidates.
These overlapping counts are neither unique defects nor confirmed runtime
failures. System, generated and external headers may have no tree candidate.

Candidate lookup explicitly uses Windows separator normalization and casefold
matching. `relative_exact` means the normalized candidate spelling exists in the
pinned tree; it does not mean the original operand resolves on Linux or Vita.
Search-root candidates are sorted full-tree suffix matches, including tooling
copies. They are not the original compiler's search order. Parent-relative
operands receive relative candidates without speculative suffix search.
Quoted and angled operands are both inventoried; their compiler lookup rules
remain distinct and unestablished. No candidate is automatically selected.

For example, WWLib `thread.h` requests `vector.h`, while the library contains
`Vector.H`; an additional copy exists in the WW3D tooling tree. A portability
patch must preserve the original project's library include ownership rather
than choose a same-named file from an arbitrary global include directory.
Original WWMath projects also reach headers through Windows backslash paths.
The include spelling and shared allocation/calling-convention boundary must be
reconciled together before claiming a usable original math library.

```sh
python3 tools/audit_include_paths.py --source build-source-ci/GeneralsMD/Code \
  --output build-arm-ci/include-paths.json.gz
python3 tools/compare_report.py reports/generated/include-paths.json.gz \
  build-arm-ci/include-paths.json.gz
```

The scanner splices backslash-newline before masking ordinary comments,
quoted strings and character literals. It uses the same spliced stream for
operand parsing and maps results to original physical lines. Computed operands
remain explicit. Raw strings, macro expansion, compiler extensions and full
preprocessing remain coverage gaps. Dirty input fingerprints and symlinks fail.
CI reproduces typed JSON content independently of gzip encoding differences.
The consolidated dependency gap includes this evidence without adding another
parent defect. Host or syntax-check results provide no physical Vita/PSTV proof.
