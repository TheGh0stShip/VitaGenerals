# Script dispatch sweep

`reports/generated/script-dispatch.json` records original script enum names,
ordinal values, declaration lines, runtime case-label sites, lexical call/return
candidates and template assignment sites. Inputs are pinned to the complete
pristine Zero Hour Code tree; no retail scripts are published.

| Denominator | Declared entries, including sentinel | Case sites across both layers | Template assignment sites |
| --- | ---: | ---: | ---: |
| ScriptActionType | 345 | 344 | 346 |
| ConditionType | 110 | 105 | 104 |

`ScriptEngine::executeActions` handles 24 action types locally and delegates
other types to `ScriptActions::executeAction`. `ScriptEngine::evaluateCondition`
handles five condition types locally and delegates the rest to
`ScriptConditions::evaluateCondition`. The subsystem default paths report an
unknown type; actions return and conditions return false. Presence of a case
label does not prove correct or reachable execution.

Every declared action except the `NUM_ITEMS` sentinel has a case site across
these layers. Conditions without case sites are `NUM_ITEMS`, `OBSOLETE_SCRIPT_1`,
`OBSOLETE_SCRIPT_2`, `TEAM_COMPLETED_SEQUENTIAL_EXECUTION` and
`UNIT_COMPLETED_SEQUENTIAL_EXECUTION`. The two obsolete values are marked obsolete
in the original header. Retail use, compatibility handling and the sequential
execution values remain unresolved.

`NAMED_RECEIVE_UPGRADE` has a dispatch case but no matching direct template
assignment found by this scanner. Conditions without matching direct assignments
include the above five values and two `DEFUNCT_PLAYER_SELECTED_GENERAL` values
marked unused in the original header. Repeated template assignment sites are
retained separately: action `VICTORY`, `DEFEAT`, `CAMERA_FADE_MULTIPLY` and condition
`NAMED_INSIDE_AREA`. Site counts are not unique templates or confirmed defects.

| Gap | Priority | Dependency / evidence needed |
| --- | --- | --- |
| Original script engine absent from target engine build | Blocking | Original subsystem staging and platform dependencies |
| Unmatched enum/template paths | Required review | Retail map references, load remapping and original template ownership |
| Parameter and template field semantics | Required | Full template construction, validation and save/load inventory |
| Conditional reachability and helper implementations | Required | Target preprocessing, source selection and complete function sweep |
| Gameplay execution unverified | Required | Campaign/challenge/skirmish progression and physical Vita/PSTV traces |

This is a bounded lexical comparison, not control-flow analysis or a complete
script census. It does not resolve preprocessing, aliases, nested-switch
ownership, fallthrough, raw strings or generated cases. Unsupported enum
expressions, ambiguous owners and unsupported case syntax fail the scan.
Constants and call identifiers are candidates, not stub classifications.
Original 32-bit script identities must remain unchanged during porting.

Reproduce with the pinned source checkout:

```sh
python3 tools/audit_script_dispatch.py --source build-source-ci/GeneralsMD/Code \
  --output build-arm-ci/script-dispatch.json
cmp reports/generated/script-dispatch.json build-arm-ci/script-dispatch.json
```
