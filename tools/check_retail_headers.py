#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read only the BIGF headers through the compiled portable implementation."""
import ctypes
from pathlib import Path
import sys
class Header(ctypes.Structure):
    _fields_ = [('size', ctypes.c_uint32), ('count', ctypes.c_uint32), ('end', ctypes.c_uint32)]
if len(sys.argv) < 3:
    sys.exit('usage: check_retail_headers.py SHARED_LIBRARY DATA_DIRECTORY [...]')
lib = ctypes.CDLL(str(Path(sys.argv[1]).resolve()))
f = lib.vg_big_header_read
f.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64, ctypes.POINTER(Header)]
f.restype = ctypes.c_int
count = 0
for directory in sys.argv[2:]:
    root = Path(directory)
    if not root.is_dir():
        sys.exit('data directory missing')
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() != '.big':
            continue
        with p.open('rb') as stream:
            data = stream.read(16)
        h = Header()
        if not f(data, len(data), p.stat().st_size, ctypes.byref(h)):
            sys.exit('FAIL: retail BIG header rejected')
        count += 1
if not count:
    sys.exit('FAIL: no BIG files checked')
print(f'PASS: {count} retail BIGF headers (read-only, host only)')
