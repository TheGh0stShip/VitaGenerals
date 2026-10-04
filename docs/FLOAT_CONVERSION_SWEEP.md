# Numeric conversion and rounding candidates

`tools/audit_float_routes.py` inventories selected conversion and rounding
calls across the pinned original Code tree. It derives conversion macro names
from function-like definitions in `Lib/BaseType.h` that mention the four
`fast_float` helpers. Macro bodies remain unexpanded text: aliases, strings,
conditional selection and type bindings are not resolved. The machine-readable
report is `reports/generated/float-routes.json.gz`; CI regenerates it from
fresh pinned source and compares decoded JSON content.

Source hashes, ordered arguments, callable owners, guards and parser recovery
are retained. This is a partial numeric boundary census, not a count of defects
or a proof that a call executes. The audit does not interpret assembly, infer
input ranges or establish multiplayer determinism.

The baseline has 453 call candidates and 13 conversion macros across 2,961
C/C++ inputs. Calls include 224 `REAL_TO_INT`, 131 `REAL_TO_INT_FLOOR`, 54
`REAL_TO_INT_CEIL` and 17 `setFPMode` sites. No selected call has its own parser
error; 14,677 parser recoveries across the source remain possible omissions.

`GameLogic.cpp::setFPMode` resets floating-point state, selects `_RC_NEAR`
and `_PC_24`, and applies them through `_controlfp`. Its CHOP comments and
commented alternative do not describe the active selection. Callers include
INI loading, game logic and frontend/rendering paths. The Direct3D color
conversion assembly separately saves the x87 control word, temporarily selects
truncation and restores the previous word.

The original truncation helper masks float bits using an x86 shift count that
wraps modulo 32. A host translation of those instructions matched a defined
32-bit integer model across 4,096 sign/exponent/mantissa boundary cases and
100,000 deterministic bit patterns. It differs from standard truncation for
negative zero, negative fractions near zero, some large exponents and NaN
payloads. These are diagnostic observations; original compiler behavior and
reachable gameplay input domains still need verification.

The original floor/ceil helpers adjust selected signs by the binary32 value
immediately below one, then call the bit truncation helper. With nearest
rounding and 24-bit precision, diagnostic integral inputs can produce results
such as `ceil(1) == 2` and `floor(-1) == -2`. Replacing these routines with
mathematical floor/ceil would change that observed behavior. Constant folding,
inlining, runtime state and original executable behavior remain open.

The x87 integer conversion writes a 32-bit destination. Diagnostic ties use
nearest-even rounding under the active nearest setting. With masked exceptions,
selected invalid conversions return the minimum signed 32-bit value and set
the invalid status flag; a valid minimum value has the same result without
that flag. Unchecked C++ casts do not establish equivalent behavior.

Vita is little-endian ARMv7-A/Cortex-A9, 32-bit ARM/Thumb with ILP32. Preserve
32-bit original conversion semantics on LP64/LLP64 hosts. Target float ABI,
rounding control, exception behavior, alignment and compiler flags need their
own checks. No global structure packing or actual pointer truncation is valid.
Host differential tests and ARM object compilation do not prove physical
Vita/PSTV behavior. No production conversion replacement or complete allocator
implementation is supplied by this audit.
