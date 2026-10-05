#!/usr/bin/env python3
"""Package materialized sources for an SSH server that does not have Git."""
from pathlib import Path
import tarfile
ROOT=Path(__file__).resolve().parents[1]
def main():
 target=ROOT/'build/pipelined-soc-source.tar.gz';target.parent.mkdir(exist_ok=True)
 with tarfile.open(target,'w:gz')as archive:
  for path in sorted(ROOT.rglob('*')):
   relative=path.relative_to(ROOT)
   if any(part in('.git','build','work','__pycache__')for part in relative.parts):continue
   if path.is_file()and path.suffix!='.vcd':archive.add(path,arcname=str(Path('pipelined-soc')/relative))
 print(target)
if __name__=='__main__':main()
