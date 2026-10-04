# ASCII string in-place overlap

The original `AsciiString::ensureUniqueBufferOfSize` reuses a unique buffer when its capacity is sufficient. Its `strcpy` and `strcat` calls can receive a source inside that same buffer through interior assignment or self-concatenation. The overlap patch uses `memmove`, includes the terminating byte, and computes append lengths before moving bytes. Allocation, reference counting and the separate-buffer path retain their original ownership.

The source is preserved verbatim under `vendor/ea/GameEngine/Source/Common/System/AsciiString.cpp`. The manifest pins original, patch and staged hashes; staging rejects mismatches and applies the patch with zero fuzz.

A development host build of the actual string and allocator candidates reproduced the self-concatenation overlap under AddressSanitizer. After the fix, copy-on-write, self-concatenation, interior assignment and formatting-boundary checks passed with AddressSanitizer and UndefinedBehaviorSanitizer. That build also contains separate, unpublished platform migrations; these results are focused development evidence, not a reproducible public full-engine test. The candidate string and allocator cluster compiled and linked for ARMv7 with checked hard-float attributes. Neither the linked checks nor the full game have been executed on Vita/PSTV.

Public gates verify deterministic staging and the existing host/ARM baseline. They do not establish string runtime coverage, gameplay reachability, locale or Unicode compatibility, or hardware correctness. The native platform migration and reproducible integrated string tests remain open.
