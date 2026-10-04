# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import struct
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from script_leaf_values import leaf

def scalar(kind=0,text=b'a\0\xff'):
    return struct.pack('<iiI',kind,-2147483648,0x7fc01234)+struct.pack('<H',len(text))+text

def record(label,version,parameters=()):
    key=struct.pack('<i',-253) if version >= (4 if label=='Condition' else 2) else b''
    return struct.pack('<i',7)+key+struct.pack('<i',len(parameters))+b''.join(parameters)

class ScriptLeafValues(unittest.TestCase):
    def test_all_versions_and_both_action_routes(self):
        for label in ('Condition','ScriptAction','ScriptActionFalse'):
            for version in ((1,2,3,4) if label=='Condition' else (1,2)):
                with self.subTest(label=label,version=version):
                    r=leaf(record(label,version),label,version,{0xffffffff:['A','B']})
                    self.assertEqual(r['raw_enum_i32'],7)
                    self.assertEqual(r['raw_parameters'],[])
                    self.assertFalse(r['runtime_binding_and_healing_verified'])
                    if 'raw_name_key' in r:
                        self.assertEqual(r['raw_name_key'],{'packed_i32':-253,'type_byte':3,'id_u32':0xffffffff,'name_candidates':['A','B']})
    def test_scalar_bytes_and_coordinates_preserve_bits(self):
        bits=bytes.fromhex('0000803f000000800000807f')
        r=leaf(record('Condition',4,[scalar(),struct.pack('<i',16)+bits]),'Condition',4,{})
        self.assertEqual(r['raw_parameters'][0],{'raw_type_i32':0,'integer_i32':-2147483648,'real_float32_bits':'3412c07f','ascii_bytes':'a\0\xff'})
        self.assertEqual(r['raw_parameters'][1],{'raw_type_i32':16,'coordinate_float32_bits':bits.hex()})
    def test_unknown_parameter_type_remains_wire_value(self):
        r=leaf(record('ScriptAction',1,[scalar(-1,b'')]),'ScriptAction',1,{})
        self.assertEqual(r['raw_parameters'][0]['raw_type_i32'],-1)
    def test_parameter_limit_and_malformed_count(self):
        self.assertEqual(len(leaf(record('ScriptAction',1,[scalar()]*12),'ScriptAction',1,{})['raw_parameters']),12)
        for n in (-1,13,2147483647):
            with self.subTest(n=n),self.assertRaises(ValueError):leaf(struct.pack('<ii',0,n),'ScriptAction',1,{})
    def test_every_truncation_and_trailing_bytes(self):
        for label,version in (('ScriptAction',1),('ScriptActionFalse',2),('Condition',4)):
            data=record(label,version,[scalar(),struct.pack('<i',16)+b'\0'*12])
            for end in range(len(data)):
                with self.subTest(label=label,end=end),self.assertRaises(ValueError):leaf(data[:end],label,version,{})
            with self.assertRaises(ValueError):leaf(data+b'x',label,version,{})
    def test_unknown_label_version_and_unresolved_key(self):
        for label,version in (('Other',1),('ScriptAction',0),('Condition',5)):
            with self.subTest(label=label,version=version),self.assertRaises(ValueError):leaf(b'',label,version,{})
        r=leaf(record('ScriptAction',2),'ScriptAction',2,{})
        self.assertEqual(r['raw_name_key']['name_candidates'],[])

if __name__=='__main__':unittest.main()
