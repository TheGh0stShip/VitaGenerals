# Module registration sweep

`reports/generated/module-registrations.json` records authored `addModule`
call sites across the pinned Zero Hour source/header tree. The scanner verifies
all source-tree hashes before publishing relative paths, source hashes, line
numbers, class arguments and nested conditional branch histories.

There are 224 sites: 205 in `ModuleFactory::init` and 19 in
`W3DModuleFactory::init`, which calls the base initializer first. There are 223
distinct identifier arguments. Five sites depend on `ALLOW_SURRENDER` and one
on `ALLOW_DEMORALIZE`; their target configuration reachability remains unknown.
The macro binds instance/data constructors, module type, stringized class name
and interface mask. Its definition is recorded separately from call sites.

`WeaponBonusUpgrade` occurs twice in the base initializer. The original
`addModuleInternal` assigns the factory map entry keyed by decorated name/type.
The repeated source sites remain two records; they are not two unique defects.
No runtime consequence is established here.

| Gap | Priority | Dependency / evidence needed |
| --- | --- | --- |
| Original factories absent from target engine build | Blocking | Original engine dependency staging and target platform boundaries |
| Guard reachability unknown | Required | Target definitions and preprocessor expansion |
| Class/data constructors and INI binding not joined | Required | Implementation and retail configuration inventories |
| Registration execution unverified | Required | Startup trace and original object construction on Vita/PSTV |
| Other registration mechanisms not covered | Required | Full source/interface sweep, including scripts and INI dispatch |

This is a bounded lexical sweep, not a complete C++ parser, registrar census or
runtime proof. Comments and ordinary literals are masked; unsupported nested
call syntax and unmatched conditionals fail the scan. Raw strings, macro aliases,
token pasting and complete preprocessing remain outside its scope. Guard records
preserve branch history without asserting truth. No retail data is included.

Reproduce with the pinned source checkout:

```sh
python3 tools/audit_module_registrations.py --source build-source-ci/GeneralsMD/Code \
  --output build-arm-ci/module-registrations.json
cmp reports/generated/module-registrations.json build-arm-ci/module-registrations.json
```
