# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import struct
import unittest
import zlib
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from map_chunks import refpack, decode, framing, LIMIT, MAX_TABLE_ENTRIES

def stream(commands, size, kind=0x10fb):
    width = 4 if kind & 0x8000 else 3
    return (kind.to_bytes(2, 'big') + (b'\0' * width if kind & 0x100 else b'')
            + size.to_bytes(width, 'big') + commands)

def table(entries):
    return b'CkMp' + struct.pack('<i', len(entries)) + b''.join(
        bytes([len(name)]) + name + struct.pack('<I', ident) for name, ident in entries)

class MapChunks(unittest.TestCase):
    def test_all_copy_forms_and_overlap(self):
        for command, expected in [(b'\0\0', b'ABCDDDD'),
                                  (b'\x80\0\3', b'ABCDABCD'),
                                  (b'\xc0\0\3\0', b'ABCDABCDA')]:
            with self.subTest(command=command):
                self.assertEqual(refpack(stream(b'\xe0ABCD'+command+b'\xfc', len(expected)), len(expected)), expected)
    def test_literals_before_each_copy_form(self):
        for command, expected in [(b'\1\0Z', b'ABCDZZZZ'),
                                  (b'\x80\xc0\0xyz', b'ABCDxyzzzzz'),
                                  (b'\xc1\0\0\0Z', b'ABCDZZZZZZ')]:
            with self.subTest(command=command):
                self.assertEqual(refpack(stream(b'\xe0ABCD'+command+b'\xfc', len(expected)), len(expected)), expected)
    def test_high_distance_and_length_bits(self):
        for size, command, count in ((1024, b'\x60\xff', 3),
                                     (16384, b'\xbf\x3f\xff', 67),
                                     (131072, b'\xdc\xff\xff\xff', 1028)):
            seed=bytes(i % 251 for i in range(size))
            literals=bytearray()
            for start in range(0,size,112):
                block=seed[start:start+112]
                literals.extend(bytes([0xe0+(len(block)-4)//4])+block)
            expected=seed+seed[:count]
            self.assertEqual(refpack(stream(bytes(literals)+command+b'\xfc',len(expected)),len(expected)),expected)
    def test_header_width_and_optional_field(self):
        for kind in (0x10fb, 0x11fb, 0x90fb, 0x91fb):
            self.assertEqual(refpack(stream(b'\xfdZ', 1, kind), 1), b'Z')
    def test_terminal_literals_and_empty(self):
        for n in range(4):
            expected=b'xyz'[:n]
            self.assertEqual(refpack(stream(bytes([0xfc+n])+expected,n),n),expected)
    def test_reject_truncated_backreference_and_lengths(self):
        invalid = [stream(b'\0\0\xfc',3), stream(b'\xe0AB',4),
                   stream(b'\xfeZ',2), stream(b'\xe0ABCD',4),
                   stream(b'\xfcX',0), stream(b'\xe0ABCD\xfc',3)]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                refpack(data, int.from_bytes(data[2:5], 'big'))
    def test_size_and_type_limits(self):
        with self.assertRaises(ValueError):refpack(b'\x00\xfb',0)
        with self.assertRaises(ValueError):refpack(stream(b'\xfc',0),1)
        with self.assertRaises(ValueError):refpack(stream(b'\xfc',LIMIT+1,0x90fb),LIMIT+1)
    def test_raw_refpack_and_zlib_wrappers(self):
        raw=table([])
        self.assertEqual(decode(raw),(raw,'raw'))
        packed=b'EAR\0'+struct.pack('<i',len(raw))+stream(b'\xe1'+raw+b'\xfc',len(raw))
        self.assertEqual(decode(packed),(raw,'refpack'))
        for version in range(1,10):
            packed=b'ZL'+str(version).encode()+b'\0'+struct.pack('<i',len(raw))+zlib.compress(raw)
            self.assertEqual(decode(packed),(raw,'zlib'))
    def test_wrapper_truncation_size_and_zlib_trailing(self):
        raw=table([]);packed=b'ZL5\0'+struct.pack('<i',len(raw))+zlib.compress(raw)
        for data in (b'EAR\0',b'EAR\0'+struct.pack('<i',-1),b'NOPE'+b'\0'*4,
                     packed[:-1],packed+b'X',b'ZL5\0'+struct.pack('<i',len(raw)-1)+zlib.compress(raw)):
            with self.subTest(data=data),self.assertRaises(ValueError):decode(data)
    def test_explicit_chunk_widths_duplicates_and_unknown_ids(self):
        raw=table([(b'A',7),(b'B',7)])+struct.pack('<IHi',7,0x1234,3)+b'abc'+struct.pack('<IHi',9,1,0)
        result=framing(raw)
        self.assertEqual(result['duplicate_ids'],[7])
        self.assertEqual(result['top_chunks'][0]['label_candidates'],['A','B'])
        self.assertEqual(result['top_chunks'][0]['version_u16'],0x1234)
        self.assertEqual(result['top_chunks'][1]['offset'],len(raw)-10)
        self.assertEqual(result['top_chunks'][1]['label_candidates'],[])
        self.assertFalse(result['complete_references'])
    def test_diagnostic_resource_limits(self):
        with patch('map_chunks.LIMIT',8):
            with self.assertRaises(ValueError):decode(b'CkMp'+b'x'*5)
            with self.assertRaises(ValueError):framing(b'CkMp'+b'x'*5)
        raw=table([])+struct.pack('<IHi',1,1,0)*2
        with patch('map_chunks.MAX_TOP_CHUNKS',1),self.assertRaises(ValueError):framing(raw)
    def test_chunk_table_and_body_bounds(self):
        for raw in (b'bad!',b'CkMp'+struct.pack('<i',-1),b'CkMp'+struct.pack('<i',MAX_TABLE_ENTRIES+1),
                    table([])+b'\0'*9,table([])+struct.pack('<IHi',1,1,-1),
                    table([])+struct.pack('<IHi',1,1,1),b'CkMp'+struct.pack('<i',1)+b'\4ab'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):framing(raw)
if __name__ == '__main__':
    unittest.main()
