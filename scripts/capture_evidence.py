#!/usr/bin/env python3
"""Capture real EDA GUI/terminal windows on an isolated Linux X11 display.
Terminal images are explicitly log-review captures, not fabricated live runs.
"""
from pathlib import Path
import os,subprocess,time,sys
root=Path(__file__).resolve().parents[1];os.chdir(root)
out=root/'reports/evidence';out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,DISPLAY=':99',QT_X11_NO_MITSHM='1')
serverlog=(root/'build/evidence/xvfb.log').open('w')
xvfb=subprocess.Popen(['Xvfb',':99','-screen','0','1440x900x24','-ac'],stdout=serverlog,stderr=subprocess.STDOUT)
time.sleep(1)
def run(args,**kw):return subprocess.run(args,env=env,check=True,**kw)
def capture(name,args,wait=4):
 log=(root/f'build/evidence/gui_{name}.log').open('w')
 process=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,cwd=root)
 try:
  time.sleep(wait)
  if process.poll() is not None:raise RuntimeError(f'GUI {name} exited: see {log.name}')
  ids=subprocess.check_output(['xdotool','search','--onlyvisible','--pid',str(process.pid)],env=env,text=True).split()
  if not ids:raise RuntimeError('no GUI window')
  wid=ids[-1]
  subprocess.run(['xdotool','windowmove',wid,'0','0','windowsize',wid,'1440','900'],env=env)
  time.sleep(1)
  run(['import','-window','root',str(out/f'{name}.png')])
  print('CAPTURED',name,flush=True)
 finally:
  process.terminate()
  try:process.wait(timeout=5)
  except subprocess.TimeoutExpired:process.kill()
  log.close()
try:
 if len(sys.argv)==1 or 'wave' in sys.argv:
  capture('verification_gui',['gtkwave','build/evidence/pipeline.vcd','-S','asic/open/waves.tcl'])
 if len(sys.argv)==1 or 'layout' in sys.argv:
  platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
  for stage in ['2_floorplan','3_power','4_placement','5_cts','6_global_route','7_final']:
   if not (root/f'build/asic/{stage}.odb').exists():continue
   script=root/'build/evidence/view.tcl'
   s=f'read_liberty {platform}/lib/NangateOpenCellLibrary_typical.lib\nread_db {{{root}/build/asic/{stage}.odb}}\nread_sdc {{{root}/build/asic/{stage}.sdc}}\n'
   s+='gui::set_display_controls "Signals/Power" visible true\ngui::set_display_controls "Signals/Ground" visible true\ngui::fit\n'
   if stage=='5_cts':s+='gui::select -type Inst -name "clkbuf*" -highlight 1\n'
   s+=f'puts "Evidence view: {stage}; rv32_pipeline; Nangate45"\nreport_design_area\n'
   script.write_text(s)
   capture(stage+'_gui',['openroad','-gui',str(script)],7)
 if len(sys.argv)==1 or 'terminal' in sys.argv:
  for review in sorted((root/'build/evidence').glob('*_review.txt')):
   shell=root/'build/evidence/review.sh'
   shell.write_text('set -x\ncat "'+str(review)+'"\nset +x\necho "\nRecorded log review complete. Original logs retained in build/."\nsleep 120\n')
   capture(review.stem.replace('_review','')+'_terminal',['xterm','-fa','DejaVu Sans Mono','-fs','15','-bg','#101820','-fg','#e8edf2','-geometry','118x34+0+0','-title','RISC-V lab evidence: '+review.stem,'-e','bash',str(shell)],2)
finally:
 xvfb.terminate();xvfb.wait();serverlog.close()
