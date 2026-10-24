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
  if name in ('1_synth_gui','timing_gui'):
   run(['xdotool','mousemove','1200','73','click','--repeat','2','--delay','120','1'])
   time.sleep(1)
   floating=subprocess.check_output(['xdotool','search','--onlyvisible','--name','^Timing Report$'],env=env,text=True).split()
   if floating:
    run(['xdotool','windowmove',floating[-1],'0','0','windowsize',floating[-1],'1440','900'])
    run(['xdotool','mousemove','500','155','click','1'])
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
 if len(sys.argv)==1 or 'layout' in sys.argv or 'synthonly' in sys.argv:
  platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
  for stage in ['1_synth','2_floorplan','3_power','4_placement','5_cts','6_global_route','7_final']:
   if 'synthonly' in sys.argv and stage!='1_synth':continue
   if not (root/f'build/asic/{stage}.odb').exists():continue
   script=root/'build/evidence/view.tcl'
   s=f'read_liberty {platform}/lib/NangateOpenCellLibrary_typical.lib\nread_db {{{root}/build/asic/{stage}.odb}}\nread_sdc {{{root}/build/asic/{stage}.sdc}}\n'
   s+='foreach w {\"Help Browser\" \"Inspector\" \"Hierarchy Browser\" \"Timing Report\" \"Charts\"} {gui::hide_widget $w}\n'
   s+='gui::set_display_controls "Nets/Power" visible true\ngui::set_display_controls "Nets/Ground" visible true\ngui::fit\n'
   if stage=='5_cts':s+='select -type Inst -name "clkbuf*" -highlight 1\n'
   if stage=='1_synth':s+='gui::show_widget "Timing Report"\ngui::update_timing_report\n'
   s+=f'puts "Evidence view: {stage}; rv32_pipeline; Nangate45"\nreport_design_area\n'
   script.write_text(s)
   capture(stage+'_gui',['openroad','-gui',str(script)],7)
 if len(sys.argv)==1 or 'timing' in sys.argv:
  platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
  script=root/'build/evidence/timing_view.tcl'
  script.write_text(f'read_liberty {platform}/lib/NangateOpenCellLibrary_typical.lib\nread_db {{{root}/build/asic/7_final.odb}}\nread_sdc {{{root}/build/asic/7_final.sdc}}\nread_spef {{{root}/build/asic/7_final.spef}}\nforeach w {{"Help Browser" "Inspector" "Hierarchy Browser" "Charts"}} {{gui::hide_widget $w}}\ngui::show_widget "Timing Report"\ngui::update_timing_report\ngui::fit\nputs "Post-route extracted timing at 10 ns; setup U=0.2, hold U=0.05 ns"\nreport_worst_slack -max\nreport_worst_slack -min\n')
  capture('timing_gui',['openroad','-gui',str(script)],8)
 if len(sys.argv)==1 or 'physical' in sys.argv:
  script=root/'build/evidence/klayout_view.py'
  platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
  script.write_text('import pya\napp=pya.Application.instance()\nwin=app.main_window()\ncv=win.load_layout('+repr(str(root/'build/asic/rv32_pipeline.gds'))+',0)\nview=win.current_view()\nview.load_layer_props('+repr(str(platform/'FreePDK45.lyp'))+')\nview.add_missing_layers()\nview.max_hier()\nview.zoom_fit()\nidx=view.load_rdb('+repr(str(root/'build/asic/klayout_drc.lyrdb'))+')\nview.show_rdb(idx,0)\n')
  capture('physical_checks_gui',['klayout','-r',str(script)],8)
 if len(sys.argv)==1 or 'terminal' in sys.argv:
  for review in sorted((root/'build/evidence').glob('*_review.txt')):
   shell=root/'build/evidence/review.sh'
   shell.write_text('set -x\ncat "'+str(review.relative_to(root))+'"\nset +x\necho "\nRecorded log review complete. Original logs retained in build/."\nsleep 120\n')
   capture(review.stem.replace('_review','')+'_terminal',['xterm','-fa','DejaVu Sans Mono','-fs','15','-bg','#101820','-fg','#e8edf2','-geometry','118x34+0+0','-title','RISC-V lab evidence: '+review.stem,'-e','bash',str(shell)],2)
finally:
 xvfb.terminate();xvfb.wait();serverlog.close()
