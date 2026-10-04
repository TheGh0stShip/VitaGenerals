#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate a complete engine stage before configuring a consumer build."""
import argparse
from pathlib import Path
from stage_engine_tree import verify_build_stage

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,required=True)
    args=parser.parse_args()
    receipt=verify_build_stage(Path(__file__).resolve().parents[1],args.stage)
    print(f"PASS: {receipt['source_files']} staged source files match current pins")

if __name__=='__main__':
    main()
