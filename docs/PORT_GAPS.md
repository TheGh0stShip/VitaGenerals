# Consolidated port gaps

Generated from `port/sweep-gaps.json` and 6 pinned sweep reports. All findings
are open evidence gaps; counts do not represent unique defects or game completion.
Repeated engine-build gaps from individual sweeps share one parent finding.
Dependencies are joint closure prerequisites, not an exclusive work schedule.
Unique IDs prevent duplicate identities; semantic grouping remains a reviewed
registry decision. The nine current findings are not a complete defect census.

| Gap | Priority | Dependencies |
| --- | --- | --- |
| SOURCE-ROLES: Original runtime source roles and configuration reachability remain unresolved | blocking | None |
| DEPENDENCIES: Original workspace dependencies and middleware providers are unresolved | blocking | None |
| ENGINE-BUILD: Target selection covers a checksum probe rather than the original game engine | blocking | SOURCE-ROLES, DEPENDENCIES |
| PARSE-COVERAGE: Parser recoveries prevent a complete callable and guard denominator | required | SOURCE-ROLES |
| REGISTRATION: Authored module sites do not establish target registration execution | required | ENGINE-BUILD, PARSE-COVERAGE |
| SCRIPT-COMPATIBILITY: Script enum, template and dispatch mismatches need compatibility review | required | PARSE-COVERAGE |
| INI-SEMANTICS: Top-level INI bindings do not cover field layout and content semantics | required | REGISTRATION |
| GRAPHICS-CONTRACT: Graphics reference sites do not establish renderer equivalence | required | ENGINE-BUILD, PARSE-COVERAGE |
| PHYSICAL-ACCEPTANCE: Complete-game Vita/PSTV acceptance remains unproven | measurement | ENGINE-BUILD, REGISTRATION, SCRIPT-COMPATIBILITY, INI-SEMANTICS, GRAPHICS-CONTRACT |

## Evidence and closure criteria

### SOURCE-ROLES

Reconcile original projects, runtime callers, generated sources and target selection; retain unresolved rows.

Evidence: [original-projects.json.gz](../reports/generated/original-projects.json.gz) `/summary/units_without_original_project_reference`, [original-projects.json.gz](../reports/generated/original-projects.json.gz) `/summary/source_reference_resolutions`.

### DEPENDENCIES

Audit each missing project/provider, licensing and platform replacement contract; compile/link the selected original dependency graph.

Evidence: [original-projects.json.gz](../reports/generated/original-projects.json.gz) `/summary/missing_workspace_projects`.

### ENGINE-BUILD

Deterministically stage the original runtime graph and link the complete engine with audited platform boundaries and matching artifact identities.

Evidence: [original-projects.json.gz](../reports/generated/original-projects.json.gz) `/selected_original_sources`, [original-projects.json.gz](../reports/generated/original-projects.json.gz) `/summary/translation_units`.

### PARSE-COVERAGE

Reconcile recovered nodes with original macros, configuration-aware parsing and compiler evidence; review literal/empty/sole-return candidates without assuming stubs.

Evidence: [source-structure.json.gz](../reports/generated/source-structure.json.gz) `/summary/files_with_parse_recoveries`, [source-structure.json.gz](../reports/generated/source-structure.json.gz) `/summary/parse_recoveries`, [source-structure.json.gz](../reports/generated/source-structure.json.gz) `/summary/returns_without_callable_owner`.

### REGISTRATION

Join constructors, module data, interfaces and authored INI bindings to target selection and startup/object-construction traces.

Evidence: [module-registrations.json](../reports/generated/module-registrations.json) `/summary/registration_sites`, [module-registrations.json](../reports/generated/module-registrations.json) `/summary/guarded_sites`.

### SCRIPT-COMPATIBILITY

Classify sentinels/obsolete values, retail use, load remapping, parameter semantics and original dispatch behavior; verify all game modes.

Evidence: [script-dispatch.json](../reports/generated/script-dispatch.json) `/groups/0/declared_without_case`, [script-dispatch.json](../reports/generated/script-dispatch.json) `/groups/0/declared_without_template_assignment`, [script-dispatch.json](../reports/generated/script-dispatch.json) `/groups/1/declared_without_case`, [script-dispatch.json](../reports/generated/script-dispatch.json) `/groups/1/declared_without_template_assignment`.

### INI-SEMANTICS

Inventory field/fallback parsers, actual host/ARM offsets, includes, inheritance, overrides and all authored references with runtime load evidence.

Evidence: [ini-dispatch.json](../reports/generated/ini-dispatch.json) `/summary/block_tokens`, [ini-dispatch.json](../reports/generated/ini-dispatch.json) `/unknowns`.

### GRAPHICS-CONTRACT

Preserve original renderer hierarchy and submission/state ownership; verify format/shader behavior, visual output and physical memory/timing.

Evidence: [renderer-boundary.json.gz](../reports/generated/renderer-boundary.json.gz) `/summary/symbols_by_category`, [renderer-boundary.json.gz](../reports/generated/renderer-boundary.json.gz) `/unknowns`.

### PHYSICAL-ACCEPTANCE

Measure fixed replays on both devices, including all modes, multiplayer determinism, input, saves/transitions, audio/video, lifecycle and soak; target60FPS remains unproven.

Evidence: [source-structure.json.gz](../reports/generated/source-structure.json.gz) `/unknowns`.

## Complete-game coverage obligations

| Scope | Evidence status |
| --- | --- |
| runtime sources and registrars | partial |
| guards returns and unsupported paths | partial |
| renderer objects materials states formats and submissions | partial |
| assets loaders and references across all maps and modes | partial |
| scripts INI modules and save load | partial |
| terrain fog navigation AI economy construction upgrades projectiles damage aircraft superweapons | not established |
| campaigns challenges skirmish networking frontend audio movies | not established |
| cursor selection groups camera commands hotkeys purchase modal locks | not established |
| physical Vita PSTV performance memory visuals and lifecycle | not established |

Partial inventories retain unknowns. Reference, symbol, declaration, parser-recovery
and site counts are observations inside these findings, not additional findings.
Host/ARM compile evidence does not establish physical Vita/PSTV correctness.

Reproduce: `python3 tools/consolidate_sweep_gaps.py --output build-gaps/consolidated-gaps.json --ledger build-gaps/PORT_GAPS.md`.
Compare both outputs with their published counterparts.
