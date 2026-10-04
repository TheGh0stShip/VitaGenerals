# vitaGL dependency patches

These patches modify vitaGL revision
`6e7fe40292e8f1d10f9a94ff2cd2f4fb1ba452a5` beneath Zero Hour's original W3D
renderer boundary. They were adapted from the corresponding Renegade Vita work
at commit `0599518d2c357617e83973b08fe605f066e84eed`; exported entry points and
title-specific comments were renamed for this port.

vitaGL and these modified source fragments are distributed under LGPLv3. The
build retains the complete pinned source, `COPYING`, `COPYING.LESSER`, applied
patches, compiler identity and artifact hashes. Static release packages must
also provide the material and instructions required to relink the application.

The patches provide compact unlit immediate vertices, copied 16-bit indexed
immediate submission, full RGBA replacement uploads and transactional DXT mip
chains. They do not transfer Renegade renderer ownership or establish Zero Hour
runtime or hardware acceptance.
