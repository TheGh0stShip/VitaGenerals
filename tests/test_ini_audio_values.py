# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ini_audio_values import field_value, SOUND_LISTS, FILENAMES

class IniAudioValues(unittest.TestCase):
    def test_sound_list_separators_and_replacement(self):
        for name in SOUND_LISTS:
            row=field_value(name.encode()+b'=A,B C= D,,')
            self.assertEqual(row['values'],['A','B','C','D'])
            self.assertEqual(row['replacement_rule'],'clear_then_assign_vector')
        self.assertEqual(field_value(b'Sounds = ; nothing')['values'],[])
    def test_ascii_first_token_and_empty(self):
        for name in FILENAMES:
            row=field_value(name.encode()+b'=a.wav other')
            self.assertEqual(row['value'],'a.wav')
        self.assertEqual(field_value(b'Filename=')['value'],'')
    def test_quote_handling_remains_unresolved(self):
        row=field_value(b'Filename = "a b" tail')
        self.assertEqual(row['status'],'quoted_ascii_semantics_unresolved')
        self.assertNotIn('value',row)
        self.assertIn('"a b"',row['raw_value'])
        self.assertEqual(field_value(b'Sounds="a b"')['values'],['"a','b"'])
    def test_comments_nuls_controls_and_high_bytes(self):
        self.assertEqual(field_value(b'Sounds A; B')['values'],['A'])
        self.assertEqual(field_value(b'Filename A\0B')['value'],'A')
        self.assertEqual(field_value(b'Filename\x01\xff')['value'],'\xff')
        for control in range(1,32):
            if control==10:continue
            self.assertEqual(field_value(b'Sounds A'+bytes([control])+b'B')['values'],['A','B'])
    def test_unknown_fields_and_physical_line_guard(self):
        self.assertIsNone(field_value(b'Unknown=A'))
        self.assertIsNone(field_value(b''))
        self.assertIsNone(field_value(b'; hidden'))
        for data in (b'Filename A\nFilename B',b'A'*1028):
            with self.assertRaises(ValueError):field_value(data)
    def test_one_separator_consumed_before_handler(self):
        self.assertEqual(field_value(b'Sounds =A,B')['values'],['A','B'])
        self.assertEqual(field_value(b'Filename,A=B'),None)
        self.assertEqual(field_value(b'Filename A,B=C')['value'],'A,B')

if __name__=='__main__':unittest.main()
