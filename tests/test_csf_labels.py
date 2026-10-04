# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import csf_labels as csf

def header(labels=1,strings=1,version=3):return struct.pack('<6i',csf.CSF,version,labels,strings,0,0)
def string(raw=b'\xbe\xff',speech=None):
    result=struct.pack('<Ii',csf.STR if speech is None else csf.STRW,len(raw)//2)+raw
    return result if speech is None else result+struct.pack('<i',len(speech))+speech
def label(name=b'L',strings=(string(),)):return struct.pack('<Iii',csf.LBL,len(strings),len(name))+name+b''.join(strings)

class CSFLabels(unittest.TestCase):
    def test_explicit_width_encoded_units(self):
        raw=struct.pack('<4H',0xffbe,0x27ff,0,0xffff)
        result=csf.parse(header()+label(strings=(string(raw),)))
        value=result['rows'][0]['strings'][0]
        self.assertEqual(value['utf16le_encoded_unit_count'],4)
        self.assertEqual(value['encoded_zero_unit_offsets'],[2])
        self.assertEqual(value['encoded_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertTrue(result['exact_end'])
        self.assertEqual(result['runtime_semantics'],'unverified')
    def test_duplicates_multi_strings_speech_nul(self):
        result=csf.parse(header(2,3)+label(b'A\0B',(string(),string(speech=b'voice\0')))+label(b'A\0B'))
        self.assertEqual([r['label'] for r in result['rows']],['A\0B','A\0B'])
        self.assertTrue(result['rows'][0]['label_contains_nul'])
        self.assertEqual(result['rows'][0]['strings'][1]['speech_metadata']['bytes'],6)
        self.assertTrue(result['header_string_count_matches'])
    def test_header_only_zero_strings_and_mismatches(self):
        result=csf.parse(header())
        self.assertFalse(result['header_label_count_matches'])
        self.assertFalse(result['header_string_count_matches'])
        result=csf.parse(header(1,0,99)+label(strings=()))
        self.assertEqual(result['header_int32'][1],99)
        self.assertTrue(result['header_string_count_matches'])
        result=csf.parse(header(0,0)+label())
        self.assertEqual(len(result['rows']),1)
        self.assertFalse(result['header_label_count_matches'])
        self.assertFalse(result['header_string_count_matches'])
    def test_all_truncations_and_trailing_bytes(self):
        fixture=header()+label(strings=(string(speech=b'voice'),))
        for n in range(len(fixture)):
            if n==24:continue
            with self.subTest(n=n),self.assertRaises(ValueError):csf.parse(fixture[:n])
        with self.assertRaises(ValueError):csf.parse(fixture+b'x')
    def test_bad_magic_tags_and_negative_counts(self):
        fixtures=[b'x'+header()[1:],header()+struct.pack('<I',0),header()+struct.pack('<Iii',csf.LBL,-1,0),header()+struct.pack('<Iii',csf.LBL,0,-1),header()+struct.pack('<Iii',csf.LBL,1,0)+struct.pack('<Ii',0,0),header()+label(strings=(struct.pack('<Ii',csf.STR,-1),)),header()+label(strings=(struct.pack('<Ii',csf.STRW,0)+struct.pack('<i',-1),))]
        for data in fixtures:
            with self.subTest(data=data),self.assertRaises(ValueError):csf.parse(data)
    def test_policy_caps(self):
        with patch.object(csf,'MAX',2):
            for data in [header(3,0),header(0,0)+struct.pack('<Iii',csf.LBL,3,0),header(0,0)+label(b'long'),header(0,0)+label(strings=())*3,header(0,0)+label(strings=(string(),string()))*2]:
                with self.subTest(data=data),self.assertRaises(ValueError):csf.parse(data)
        with patch.object(csf,'MAX_BYTES',4),self.assertRaisesRegex(ValueError,'size_policy'):csf.parse(header())
if __name__=='__main__':unittest.main()
