# SPDX-License-Identifier: GPL-3.0-or-later
import gzip
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from compare_report import compare,canonical

class ReportComparison(unittest.TestCase):
    def test_compression_and_key_order_are_not_content(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.json.gz';b=Path(d)/'b.json.gz'
            a.write_bytes(gzip.compress(b'{"a":1,"b":[2,3]}',compresslevel=1,mtime=1))
            b.write_bytes(gzip.compress(b'{"b":[2,3],"a":1}',compresslevel=9,mtime=2))
            compare(a,b)
    def test_types_and_sequence_order_still_matter(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.json';b=Path(d)/'b.json'
            for left,right in [('true','1'),('1','1.0'),('[1,2]','[2,1]')]:
                a.write_text(left);b.write_text(right)
                with self.assertRaises(ValueError):compare(a,b)
    def test_duplicate_keys_and_nonfinite_values_fail(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.json'
            for text in ['{"x":1,"x":2}','{"x":NaN}']:
                a.write_text(text)
                with self.assertRaises(ValueError):canonical(a)
if __name__=='__main__':unittest.main()
