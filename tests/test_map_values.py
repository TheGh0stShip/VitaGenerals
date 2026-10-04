# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import struct
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from map_values import Cursor

class MapValues(unittest.TestCase):
    def test_ascii_bytes_and_empty(self):
        self.assertEqual(Cursor(struct.pack('<H',3)+b'a\0\xff').ascii(),'a\0\xff')
        self.assertEqual(Cursor(b'\0\0').ascii(),'')
    def test_all_scalar_types_and_duplicate_entries(self):
        data=struct.pack('<H',4)+struct.pack('<iB',256,2)+struct.pack('<ii',257,-2147483648)+struct.pack('<iI',258,0x7fc01234)+struct.pack('<iH',259,0)
        c=Cursor(data);rows=c.dictionary({1:['same']})
        self.assertEqual([r['type'] for r in rows],[0,1,2,3])
        self.assertEqual([r['id_u32'] for r in rows],[1]*4)
        self.assertEqual(rows[0]['value'],True)
        self.assertEqual(rows[1]['value'],-2147483648)
        self.assertEqual(rows[2]['value'],{'float32_bits':'3412c07f'})
        self.assertEqual(rows[3]['value'],'')
        self.assertEqual(c.pos,len(data))
    def test_unicode_is_wire_units(self):
        data=struct.pack('<HiH3H',1,260,3,0xd800,0x41,0xdc00)
        self.assertEqual(Cursor(data).dictionary({})[0]['value'],{'utf16le_units':[0xd800,0x41,0xdc00]})
        self.assertEqual(Cursor(struct.pack('<HiH',1,260,0)).dictionary({})[0]['value'],{'utf16le_units':[]})
    def test_signed_key_shift_and_candidate_preservation(self):
        row=Cursor(struct.pack('<HiB',1,-256,0)).dictionary({0xffffffff:['A','B']})[0]
        self.assertEqual(row['id_u32'],0xffffffff)
        self.assertEqual(row['key_candidates'],['A','B'])
        self.assertFalse(row['value'])
    def test_bounds_and_unknown_type(self):
        for data in (b'',b'\1',struct.pack('<Hi',1,261),struct.pack('<HiH',1,260,1)):
            with self.subTest(data=data),self.assertRaises(ValueError):Cursor(data).dictionary({})
        c=Cursor(b'a')
        with self.assertRaises(ValueError):c.take(-1)
        with self.assertRaises(ValueError):c.take(2)
        self.assertEqual(c.pos,0)
    def test_native_layout_formats_refused(self):
        for fmt in ('i','@i','=i'):
            with self.subTest(fmt=fmt),self.assertRaises(ValueError):Cursor(b'\0'*4).unpack(fmt)
        self.assertEqual(Cursor(b'\1\0\0\0').unpack('<i'),(1,))
if __name__=='__main__':unittest.main()
