# System and snapshot ownership candidates

The pinned 2,961 C/C++ source/header files contain 5,767 parsed class records.
`reports/generated/system-ownership.json.gz` retains every class/base record,
source hash, line span, conditional syntax ancestry, selected lifecycle/transfer
call spelling, raw arguments, callable context and parser recovery.
These are unpreprocessed candidates, not a resolved runtime ownership graph.

| Evidence | Candidates |
| --- | ---: |
| Parsed class records with bodies | 3,431 |
| SubsystemInterface name/edge closure | 127 |
| Snapshot name/edge closure | 628 |
| Named lifecycle/transfer calls | 2,156 |
| initSubsystem calls | 104 |
| addSnapshotBlock calls | 23 |
| Ambiguous base references | 909 |
| Unsupported base nodes | 62 |
| Calls with their own parse error | 28 |
| Parser ERROR/missing nodes | 14,677 |

Class indices identify separate parsed records, including forward declarations.
Body presence is recorded; seed propagation starts from records with bodies.
No declaration/definition identity is merged. Each simple base spelling keeps
all lexical name matches; qualified spellings use qualified-name candidates,
while unqualified spellings can match records in unrelated namespaces or tools.
Seed membership propagates independently through those possible edges. It does
not select a C++ binding, merge same-named classes, or count unique runtime types.
The two seed roots in this source are the original Common interface headers.
Template bases, aliases, macro expansion and semantic lookup remain unresolved.
Their original nodes/spellings remain available for review. A candidate closure
can both overcount and omit implementations; it is not a conservative census.

The 104 initSubsystem candidates include 45 in GameEngine.cpp (including helper
delegation), 29 in MapCacheBuilder and 30 in WorldBuilder. No tool is silently
classified as gameplay or discarded. Allocation macros produce parse errors in
28 of those calls; AST argument children are candidates, while raw argument
spelling remains available. Receiver and overload bindings remain unresolved.
Generic init/reset/update/draw/crc/xfer calls can belong to unrelated objects.

Original SubsystemInterfaceList::initSubsystem names and initializes the object,
loads optional INI paths/directory, then appends it to m_subsystems. Post-load
processing traverses that list forward; reset and shutdown traverse it backward.
Shutdown deletes its entries. Constructor addSubsystem registration instead
records m_allSubsystems under DUMP_PERF_STATS. Performance registration and the
lifecycle list are distinct. Correctness still requires caller, allocation,
configuration, failure-path and runtime lifetime evidence.

GameState.cpp contains 17 SNAPSHOT_SAVELOAD registrations and six
SNAPSHOT_DEEPCRC_LOGICONLY registrations. Repeated target pointers/tokens across
those modes remain separate rows. Snapshot declares crc, xfer and
loadPostProcess; XferCRC::xferSnapshot dispatches crc, while XferSave and XferLoad
dispatch xfer. This establishes authored routes, not save-format correctness,
complete transfer coverage or successful reconstruction of game state.

```sh
build-parser/bin/python tools/audit_system_ownership.py \
  --source build-source-ci/GeneralsMD/Code \
  --output build-arm-ci/system-ownership.json.gz
python3 tools/compare_report.py reports/generated/system-ownership.json.gz \
  build-arm-ci/system-ownership.json.gz
```

Use the hash-pinned parser dependencies in tools/parser-requirements.txt.
Original Latin-1 bytes are transcoded to UTF-8 for parsing; original hashes and
line coordinates are retained, without claiming parser byte offsets are disk
offsets. Calls inside lambdas have their nearest parsed callable recorded.
Conditional ancestry is syntax, not evaluated branch reachability. Source
fingerprint mismatches and symlinks fail. CI compares typed JSON independent of
gzip encoding. The consolidated source-role and parser gaps include this sweep
without adding duplicate parent findings.

Complete factory bindings, registrations, deletion paths, assets across maps
and modes, save/load ownership, input routes and system behavior remain open.
Other lifecycle/transfer mechanisms are outside the selected route set. Parser
recoveries may omit or misclassify structure. No engine build, runtime retention,
physical Vita/PSTV correctness or complete-game inventory is established here.
