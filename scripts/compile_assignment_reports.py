#!/usr/bin/env python3
"""Compile the actual measured lab evidence into independent submission PDFs."""
from pathlib import Path
import json,re,shutil,os,sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor,white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'reports/submissions'
OUT.mkdir(parents=True,exist_ok=True)
M=json.loads((ROOT/'reports/asic_metrics.json').read_text())
C=json.loads((ROOT/'reports/physical_checks.json').read_text())
PG=json.loads((ROOT/'reports/power_pins.json').read_text())
assert PG['status']=='PASS','Power terminal audit incomplete'
L=json.loads((ROOT/'reports/lvs_summary.json').read_text())
assert json.loads((ROOT/'reports/closure_summary.json').read_text())['status']=='PASS','Closure incomplete'
assert L['status']=='PASS' and L['port_labels_match'],'LVS evidence incomplete'
R=json.loads((ROOT/'reports/regression.json').read_text())
A=json.loads((ROOT/'reports/architectural_tests.json').read_text())
assert M['completed'],'Physical flow incomplete'
W,H=landscape(A4);margin=38;usable=W-2*margin
NAVY=HexColor('#12283e');TEAL=HexColor('#007c83');INK=HexColor('#263544');GRAY=HexColor('#617183')
STYLE=ParagraphStyle('body',fontName='Helvetica',fontSize=12,leading=17,textColor=INK,spaceAfter=12)
SMALL=ParagraphStyle('small',parent=STYLE,fontSize=9,leading=12)
CELL=ParagraphStyle('cell',parent=STYLE,fontSize=10,leading=14)
class Report:
 def __init__(self,file,label):
  self.c=canvas.Canvas(str(OUT/file),pagesize=(W,H));self.label=label;self.n=0
  self.c.setTitle(label+' | Five-stage RISC-V processor');self.c.setAuthor('Shiv Sriram V | AI-assisted compilation')
 def page(self,title,kicker=''):
  if self.n:self.footer();self.c.showPage()
  self.n+=1;c=self.c;c.setFillColor(NAVY);c.rect(0,H-15,W,15,fill=1,stroke=0)
  c.setFont('Helvetica-Bold',10);c.setFillColor(TEAL);c.drawString(margin,H-39,self.label.upper()+'   /   '+kicker.upper())
  c.setFillColor(NAVY);c.setFont('Helvetica-Bold',23);c.drawString(margin,H-72,title)
  self.y=H-102
 def footer(self):
  c=self.c;c.setStrokeColor(HexColor('#d3dce3'));c.line(margin,31,W-margin,31)
  c.setFont('Helvetica',8);c.setFillColor(GRAY);c.drawString(margin,18,'Shiv Sriram V  |  24BVD0168  |  L21+L22  |  Evidence run: 24 October 2026')
  c.drawRightString(W-margin,18,str(self.n))
 def p(self,text,small=False):
  obj=Paragraph(text,SMALL if small else STYLE);_,h=obj.wrap(usable,self.y-45)
  assert self.y-h>=44,(self.label,self.n,'paragraph overflow',self.y,h)
  obj.drawOn(self.c,margin,self.y-h);self.y-=h+12
 def table(self,rows,widths=None):
  data=[[Paragraph(escape(str(v)),CELL) for v in row]for row in rows]
  t=Table(data,colWidths=widths or [usable/len(rows[0])]*len(rows[0]))
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e4eff1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),1,TEAL),('LINEBELOW',(0,1),(-1,-1),0.3,HexColor('#d3dce3'))]))
  _,h=t.wrap(usable,self.y-44);assert self.y-h>=44,(self.n,'table overflow',h)
  t.drawOn(self.c,margin,self.y-h);self.y-=h+16
 def code(self,text,size=9):
  lines=text.splitlines();height=len(lines)*(size+4)+20
  assert self.y-height>=44,(self.n,'code overflow',height)
  c=self.c;c.setFillColor(HexColor('#edf2f6'));c.roundRect(margin,self.y-height,usable,height,5,fill=1,stroke=0)
  c.setFillColor(INK);c.setFont('Courier',size)
  y=self.y-15
  for line in lines:
   assert c.stringWidth(line,'Courier',size)<usable-20,('code line too wide',line)
   c.drawString(margin+10,y,line);y-=size+4
  self.y-=height+15
 def photo(self,name,title,caption,kicker='Evidence'):
  self.page(title,kicker);self.p(caption,small=True)
  f=ROOT/'reports/evidence'/name
  assert f.is_file(),f
  im=ImageReader(str(f));iw,ih=im.getSize();height=self.y-48;scale=min(usable/iw,height/ih)
  dw,dh=iw*scale,ih*scale
  self.c.drawImage(im,(W-dw)/2,48+(height-dh)/2,width=dw,height=dh)
 def finish(self):self.footer();self.c.save();print(self.label,self.n,'pages')
def cover(r,subtitle):
 r.page('32-bit RISC-V processor','Group project')
 r.p('<b>'+subtitle+'</b>')
 r.table([['Team member','Registration number','Lab slot'],['Shiv Sriram V','24BVD0168','L21+L22']])
 r.p('Five elastic stages: instruction fetch, decode, execute, memory and writeback. The physical design includes the processor and its iterative multiply/divide unit. Instruction/data memory, caches, the accelerator and chip IO pads are outside this GDS boundary.')
 r.p('Implementation platform: public Nangate45 / FreePDK45, typical Liberty corner at 1.1 V and 25 C. Clock target: 10 ns. Results are measured from saved tool runs; limitations are identified alongside the corresponding checks.')
 r.p('Prepared against the supplied assignment question paper. Screenshots are actual tool windows captured on an isolated Linux X11 display; terminal figures explicitly review recorded logs. Full source, logs and databases accompany the project.',small=True)
def tools(r):
 r.page('Tools and reproducible environment','Implementation method')
 rows=[['Tool / input','Version or identity']]+[[k,v]for k,v in M['versions'].items() if k!='platform_commit']
 r.table(rows,[130,usable-130])
 r.p('Platform checkout: '+M['versions']['platform_commit']+'. The official Ubuntu 22.04 OpenROAD release and its SHA256 are recorded in reports/toolchain_installation.json. No commercial libraries were required.',small=True)
 r.photo('tools_terminal.png','Toolchain verification','Actual version-command output captured in xterm. The installation package and platform revision are pinned in the project.','Terminal evidence')
def contributions(r,stage):
 r.page('Contributions, scope and reproduction','Project record')
 r.table([['Contributor / assistance','Recorded role'],['Shiv Sriram V, 24BVD0168','Project owner; supplied the processor proposal and existing project repository. No additional team members were provided.'],['Existing repository','Processor, optional SoC extensions, firmware and regression infrastructure predated this session.'],['AI-assisted work in this session',stage+'; tool execution, evidence capture and report compilation. Student review and approval of the submitted claims remain with the project owner.']],[190,usable-190])
 r.p('No commits were made or staged. Suggested stage-by-stage commit messages and file groupings are in docs/COMMIT_GUIDE.md. The project includes exact constraints, source scripts, tool outputs and screenshots for independent reproduction.',small=True)
 r.code('make pipeline\nmake all\npython3 asic/open/synth.py\nmake closure\nmake evidence\nmake submissions',10)
def references(r):
 r.page('Source and evidence index','References')
 r.p('Assignment sources: the supplied Assignment VIII project proposal; ASIC Design Lab QP 9 (1).pdf (Assignment IX, Front End); ASIC Design Lab QP 0.pdf (Assignment X, Back End). Submission 8 duplicates the supplied proposal.',small=True)
 r.p('OpenROAD flow and public platform documentation:<br/><link href="https://openroad-flow-scripts.readthedocs.io/en/latest/">https://openroad-flow-scripts.readthedocs.io/en/latest/</link><br/>Official binary release:<br/><link href="https://github.com/Precision-Innovations/OpenROAD/releases/tag/2024-12-14">https://github.com/Precision-Innovations/OpenROAD/releases/tag/2024-12-14</link><br/>LVS source: <link href="https://github.com/laurentc2/FreePDK45_for_KLayout/tree/d15da945559773854ca04aeb9bc2c150d55a1e6c">FreePDK45_for_KLayout - pinned BSD-3-Clause source and license</link>',small=True)
 r.table([['Evidence location','Content'],['rtl/ and tb/','Synthesizable sources and independent directed scoreboard'],['build/evidence/','Full regression, hazard/gate logs and waveforms; terminal review text'],['build/asic/','Synthesis log/netlist/JSON; ODB, DEF, SDC, STA paths, SPEF, GDS and DRC database'],['reports/asic_metrics.json','Measured area, utilization, setup/hold slack and tool/platform versions'],['reports/physical_checks.json','Independent GDS DRC and measured LVS status'],['reports/lvs_summary.json','Validated cell masters, negative controls and processor comparison counts'],['reports/closure_summary.json','Final DRC, electrical, timing, functional, power and LVS audit'],['reports/evidence/','Unaltered actual GUI and xterm screenshot PNG files'],['asic/open/README.md','Reproduction, constraints, scope and tool setup']],[205,usable-205])
# Assignment VIII preserves the user's original proposal verbatim.
shutil.copy2(ROOT/'docs/source/Assignment_VIII_Proposal.pdf',OUT/'Assignment_VIII_Project_Proposal.pdf')
r=Report('Assignment_IX_Front_End.pdf','Assignment IX - Front End');cover(r,'RTL implementation, functional verification and logic synthesis');tools(r)
r.page('Design hierarchy and stage responsibilities','RTL implementation')
r.table([['Block','Implementation and purpose'],['rv32_pipeline','Physical top. Register file, decode/immediates, five valid-controlled stages, bypassing, memory handshakes, redirect/exception control, counters and machine CSRs.'],['rv32_muldiv','Iterative RV32M arithmetic unit. Blocks EX until the result is ready; signed and unsigned multiply/divide/remainder cases.'],['pipeline_evidence_tb','Directed test with an independent architectural scoreboard and explicit coverage counters.'],['cpu_tb and isa_reference.py','Randomized request/response latency; retirement trace checked against an independent instruction interpreter.'],['pipelined_soc and component RTL','Separately verified cache/fabric/accelerator extension; excluded from the core physical implementation.']],[175,usable-175])
r.p('This retains the proposed processor idea while using the existing RV32IM implementation. The fetch frontend has one outstanding request and does not sustain one instruction per cycle. No pipeline speedup or ISA certification is inferred from the five-stage structure.',small=True)
r.page('Five-stage data and control flow','Architecture')
y=375;bw=132;gap=19
for i,(name,desc) in enumerate([('IF','PC / fetch request'),('ID','Decode / register read'),('EX','ALU / branch / M unit'),('MEM','Data transaction'),('WB','Retire / writeback')]):
 x=margin+i*(bw+gap);r.c.setFillColor(HexColor('#e4eff1'));r.c.roundRect(x,y,bw,74,6,fill=1,stroke=0);r.c.setFillColor(NAVY);r.c.setFont('Helvetica-Bold',15);r.c.drawCentredString(x+bw/2,y+46,name);r.c.setFont('Helvetica',9);r.c.drawCentredString(x+bw/2,y+24,desc)
 if i<4:r.c.setStrokeColor(TEAL);r.c.line(x+bw,y+38,x+bw+gap,y+38)
r.y=340
r.p('Stage registers carry PC, instruction, operand values and control state. A valid/ready-style elastic transfer allows MEM or EX to wait without losing instruction state. Stores use byte strobes; loads shift and extend the selected byte or halfword.')
r.p('Bypasses select the newest matching result from the EX/MEM and MEM/WB paths. A dependent instruction waits while a load result is unavailable. Taken branches, JAL/JALR and exceptions cancel younger instructions and redirect fetch; pending wrong-path responses are marked killed.')
r.p('The register file forces x0 to zero. CSR and fence operations serialize as needed. The machine-mode environment includes directed exception and interrupt support, but does not implement an MMU, user/supervisor modes or a full privileged architecture.')
r.photo('rtl_terminal.png','RTL control source','Source review of the load-use interlock, redirect condition and data interface assignments. Complete modules are supplied under rtl/.','RTL terminal evidence')
r.page('Forwarding and load-use control','Relevant RTL excerpt')
r.p('Exact source excerpts from rv32_pipeline.sv. The newest valid result wins bypass priority; the interlock prevents a dependent ID instruction from consuming an unavailable load result.',small=True)
src=(ROOT/'rtl/rv32_pipeline.sv').read_text().splitlines()
r.code('\n'.join(src[54:61]+['']+src[159:168]),8)
r.p('Complete rv32_pipeline.sv, rv32_muldiv.sv and pipeline_evidence_tb.sv are embedded as file attachments in this PDF and supplied as normal project files.',small=True)
r.page('Stage transfer and architectural writeback','Relevant RTL excerpt')
r.p('Exact stage-transfer source: ID captures operand values with bypassing, and WB exposes retirement and updates the architectural register file. Valid bits govern which payloads are meaningful.',small=True)
r.code('\n'.join(src[196:220]),8)
r.page('Verification plan and measured coverage','Functional verification')
archpass=sum(x['status']=='pass'for x in A['results'])
r.table([['Requirement / test','Measured evidence'],['Forwarding and load-use stall','Directed test: forwarding=2; load-use stall=13 cycles; architectural scoreboard passes.'],['Control hazards','Two redirects; PC 0x20 and 0x28 are forbidden from retirement; taken and untaken branches plus JAL checked.'],['Architectural state','Expected x1=7, x2=12, x3=12, x4=24, x6=0, x7=x8=40. Test finishes at cycle 70 with 12 retirements observed before the exit-store response.'],['RV32M arithmetic',str(R['m_vectors'])+' multiply/divide test vectors including edge cases.'],['CPU differential verification','; '.join(str(x['differential_instructions'])+' retirements at delay '+str(x['delay'])for x in R['cpu'])+'.'],['Architectural suite',str(archpass)+' passing programs; adapted riscv-tests environment, not certification.'],['Additional regression','Cache, AXI adapter, traps, matrix/DMA and integrated firmware sweeps; fatal lint and a 25-cycle bounded arbiter safety proof.']],[200,usable-200])
r.photo('verification_terminal.png','Directed pipeline test results','The recorded run prints each retirement and the scoreboard/coverage result. Wrong-path instructions are rejected by PC; the exit store completes after the reported 12 retirements.','Simulation terminal evidence')
r.photo('verification_gui.png','Pipeline waveform in GTKWave','The asserted load-hazard interval holds ID while memory is busy. ex_redirect pulses correspond to the taken branch and jump. X values before a stage becomes valid are uninitialized, invalid payloads.','Simulation GUI evidence')
r.photo('regression_terminal.png','Full regression and reference comparisons','Saved make all output and generated JSON results. Whole-SoC checks extend beyond the processor core that is physically implemented.','Regression terminal evidence')
r.page('Technology synthesis flow and constraints','Logic synthesis')
r.p('Yosys elaborates and flattens rv32_pipeline and rv32_muldiv, lowers processes and memories, maps flip-flops with dfflibmap, then maps combinational logic through ABC using the Nangate45 typical Liberty library. Tie cells implement constants. Structural checks run before and after mapping.')
r.code('read_verilog -sv rtl/rv32_pipeline.sv rtl/rv32_muldiv.sv\nsynth -top rv32_pipeline -flatten\ndfflibmap -liberty NangateOpenCellLibrary_typical.lib\nabc -liberty NangateOpenCellLibrary_typical.lib -D 10000\nhilomap -hicell LOGIC1_X1 Z -locell LOGIC0_X1 Z\ncheck -assert\nwrite_verilog -noattr -noexpr build/asic/1_synth.v',10)
r.p('The 10 ns clock is a target. IO budgets are 1 ns; output load is 0.01 pF and input transition 0.1 ns. Setup uncertainty is 0.2 ns and hold uncertainty 0.05 ns. The register file maps to standard cells; no instruction/data SRAM is part of synthesis.',small=True)
syn=M['stages']['1_synth']
r.page('Synthesis results and interpretation','Mapped design')
r.table([['Metric','Measured result'],['Mapped cells','17,853 cells including tie cells'],['Mapped cell area','29,685.866 square micrometres'],['Clock / corner','10 ns; Nangate45 typical, 1.1 V / 25 C'],['Initial setup slack',str(syn['setup_wns_ns'])+' ns; ideal clock, no routed interconnect'],['Initial hold slack',str(syn['hold_wns_ns'])+' ns under the revised 0.05 ns hold uncertainty'],['Inference boundary','Core register file and arithmetic are mapped; external memory and optional SoC modules are excluded.']],[220,usable-220])
r.p('Initial synthesis timing does not meet the setup target and includes electrical violations from the minimally driven mapped netlist. Physical placement and repair resize cells and insert buffers; the later back-end report presents those measured improvements. Initial synthesis slack is not a post-route frequency result.')
r.photo('synthesis_terminal.png','Mapped Yosys synthesis output','Recorded standard-cell statistics and Liberty area. The area excludes external instruction/data memories, caches, accelerator and IO pads.','Synthesis terminal evidence')
r.photo('1_synth_gui.png','Initial timing paths in OpenROAD','The mapped netlist is loaded into the OpenROAD Timing Report. No placement geometry is expected at this stage; timing is based on ideal interconnect. The displayed 100% is an unplaced-tool default, not physical core utilization.','Synthesis GUI evidence')
r.photo('gate_terminal.png','Mapped and routed logical regression','The same independent directed architectural scoreboard passes on the routed, mapped netlist using Liberty-derived functional cell models. This is zero-delay simulation without SDF, and is separate from physical LVS.','Netlist terminal evidence')
r.page('Discussion of front-end results','Findings and limitations')
r.p('The directed evidence demonstrates the required dependency and redirect behavior. The broader regression checks instruction semantics and several memory latency configurations. The observed CPI reflects the conservative fetch protocol and memory stalls; five stages alone do not imply ideal throughput.')
r.p('Technology mapping succeeded, but the initial setup slack is negative. Placement-time resizing substantially changes both timing and area. The front-end report therefore retains the synthesis result and leaves the physically optimized result to Assignment X.')
r.p('The existing project includes more functionality than the initial RV32I proposal: iterative RV32M, a limited machine-mode environment and optional SoC modules. Only the processor top and M unit are included in the GDS. Formal evidence covers the arbiter for 25 bounded cycles; there is no whole-CPU formal proof or complete privileged-ISA certification.')
r.p('Supplemental physical LVS passes for the repaired routed processor, including named top ports. Repeated back-end checks report zero antenna markers and zero maximum-capacitance violations. This is a separate check from the front-end zero-delay netlist simulation; full setup, controls and result evidence are documented in Assignment X.')
r.p('A short readmemh image warning in the older regression means the initialized simulation memory is larger than the loaded program. The directed evidence image uses an explicit range. Assertions and architectural comparisons, rather than the absence of warning text, establish the reported pass results.')
contributions(r,'Directed hazard test and waveform; technology-mapped synthesis; mapped/post-route directed netlist checks');references(r);r.finish()
# Backend report
r=Report('Assignment_X_Back_End.pdf','Assignment X - Back End');cover(r,'Floorplanning through routing, timing analysis and physical checks')
r.page('Implementation outcome and boundaries','Measured overview')
final=M['stages']['7_final'];core=M['core_um'];die=M['die_um']
r.table([['Metric','Result'],['Physical top','rv32_pipeline including rv32_muldiv'],['Die dimensions',f'{die[2]-die[0]:.3f} x {die[3]-die[1]:.3f} um'],['Core dimensions',f'{core[2]-core[0]:.3f} x {core[3]-core[1]:.3f} um; area {M["core_area_um2"]:.3f} um2'],['Final cell area / utilization',f'{final["cell_area_um2_rounded"]:.0f} um2 / {final["utilization_percent_rounded"]}% (tool-rounded; excludes filler inflation)'],['Post-route setup / hold slack',f'{final["setup_wns_ns"]:.2f} ns / {final["hold_wns_ns"]:.2f} ns; extracted RC, typical corner'],['Detailed-router design-rule markers',', '.join(M['router_drvs'])],['Maximum-capacitance violations',str(len(M['max_capacitance_violations']))+' after final routed-RC extraction'],['Independent GDS DRC',str(C.get('drc_markers','not completed'))+' markers; see physical-verification section'],['LVS status',C['lvs']]],[220,usable-220])
tools(r)
stageinfo=[
 ('2_floorplan','Floorplanning','initialize_floorplan -utilization 40 -aspect_ratio 1 -core_space 10',
 'A square floorplan targets 40% initial cell utilization with approximately 10 um core margins. Rows snap to the 0.19 x 1.4 um standard-cell site. Pins are distributed on metal5/metal6. The extra whitespace accommodates repair buffers and routing; no SRAM macros or IO pads are placed.'),
 ('3_power','Power planning','pdngen -failed_via_report build/asic/pdn_failed_vias.rpt',
 'Global VDD/VSS connections feed metal1 follow-pin rails. Metal4 stripes are 0.48 um wide at 40 um pitch; metal7 straps are 1.4 um wide at 30 um pitch. A metal6/metal7 ring uses 1.4 um widths, 1.0 um spacing and 3.0 um core offset. Via connections join metal1-metal4, metal4-metal7 and metal6-metal7. The final power-grid check verifies connectivity, not package supply or IR-drop signoff.'),
 ('4_placement','Placement','global_placement -density 0.55 -routability_driven; detailed_placement',
 'Routability-driven global placement is followed by electrical repair, resizing and legalization. One-site padding reserves space between cells. Initial synthesis slew/capacitance violations motivate repair. The resulting area increase is reported separately from the synthesis area; placement is checked for overlaps and row/site legality.'),
 ('5_cts','Clock tree synthesis','clock_tree_synthesis -root_buf CLKBUF_X3 -buf_list {CLKBUF_X1 CLKBUF_X2 CLKBUF_X3}',
 'TritonCTS builds a clustered tree from the clk input. Clock inverters and clock nets are repaired, the new buffers are legalized and clocks become propagated for timing. The actual Clock Tree Viewer and stage log retain the clock-buffer hierarchy and counts. The original 0.2 ns hold uncertainty exhausted repair limits; the revised hold budget is 0.05 ns while setup stays 0.2 ns. This is a disclosed constraint revision, not closure against the earlier hold budget.'),
 ('6_global_route','Global routing','global_route -congestion_iterations 100 -verbose',
 'Signals use metal2-metal6 and clocks metal4-metal6 to limit exposure to thick upper-metal antenna geometry. Routing capacities are reduced by 30% to reserve resources. The logged global-congestion table records the layer-by-layer overflow and resource use; the initial global-route guide wirelength is recorded in asic_metrics.json. Global routing writes guides for detailed routing. Timing here uses global-route parasitic estimates; it is not the extracted final timing.'),
 ('7_final','Detailed routing and extraction','detailed_route; extract_parasitics; write_spef; read_spef',
 'Detailed routing resolves track assignment and vias using the guides. Standard-cell filler masters complete row gaps. The flow exports routed DEF and mapped Verilog, extracts routed RC with OpenRCX, writes/reads SPEF and reports setup/hold with propagated clocks. The final cell area is a logic/repair-area metric, not the die area or a full-chip pad/memory area.')]
for key,title,command,description in stageinfo:
 r.page(title,'Implementation and results');r.p(description)
 metric=M['stages'][key]
 r.table([['Metric','Measured result'],['Cell area',str(metric['cell_area_um2_rounded'])+' um2 (rounded by tool)'],['Cell utilization',str(metric['utilization_percent_rounded'])+'% (rounded by tool)'],['Setup slack / hold slack',str(metric['setup_wns_ns'])+' ns / '+str(metric['hold_wns_ns'])+' ns'],['Database / reports','build/asic/'+key+'.odb, .def, .sdc, _setup.rpt and _hold.rpt']],[205,usable-205])
 r.p('Representative stage command: '+escape(command),small=True)
 r.photo(key+'_terminal.png',title+' - tool results','Recorded stage metrics and the beginning of a real setup path from the corresponding STA report. Refer to the full report for every path arc.','Terminal evidence')
 r.photo(key+'_gui.png',title+' - physical view','Actual OpenROAD view of '+key+'.odb. The stage database and constraints are loaded from the implementation output; no layout geometry is drawn for this report.','GUI evidence')
r.photo('clock_tree_gui.png','Clock tree hierarchy in OpenROAD','Actual Clock Tree Viewer for core_clk after CTS. The buffer hierarchy supplements the placed clock-buffer view and recorded tree metrics.','CTS GUI evidence')
r.photo('cts_constraint_revision_terminal.png','Hold-budget revision and failed attempts','Both failed logs are preserved. The final run uses a disclosed 50 ps hold uncertainty; it does not establish closure against the original 200 ps hold budget.','CTS issue evidence')
r.page('Timing analysis and closure assessment','Post-placement to post-route')
rows=[['Stage','Cell area (um2)','Util.','Setup slack (ns)','Hold slack (ns)']]
for k in ['1_synth','4_placement','5_cts','6_global_route','7_final']:
 v=M['stages'][k];rows.append([k,v['cell_area_um2_rounded'],('N/A' if k=='1_synth' else str(v['utilization_percent_rounded'])+'%'),v['setup_wns_ns'],v['hold_wns_ns']])
r.table(rows,[150,150,80,190,usable-570])
path=(ROOT/'build/asic/7_final_setup.rpt').read_text()
start=re.search(r'^Startpoint: (.+)',path,re.M)[1];end=re.search(r'^Endpoint: (.+)',path,re.M)[1]
r.p('Worst reported setup path: '+escape(start)+' to '+escape(end)+'. Clock source/target latencies and the skew term are retained in the saved stage timing reports and final flow log. Setup uncertainty remains 0.2 ns.',small=True)
r.p('Positive slack means the checked paths satisfy the specified single-corner constraints. The hold result applies to a 0.05 ns hold uncertainty; the original blanket 0.2 ns assumption failed repair. Input/output delays remain 1 ns. Setup uncertainty remains 0.2 ns.')
r.p('Synthesis has no physical parasitics; placement uses placement estimates; global routing uses guide-based estimates; final timing uses extracted SPEF and propagated clocks. No fast/slow PVT analysis, process-variation derating, crosstalk signoff or package timing is claimed.',small=True)
r.photo('timing_gui.png','Post-route critical timing paths','OpenROAD Timing Report after loading final ODB, propagated-clock constraints and extracted SPEF. The detailed route does not by itself establish multi-corner signoff.','Timing GUI evidence')
r.photo('electrical_terminal.png','Final electrical constraint check','The final extracted-RC checkpoint records the capacitance result after buffering, sizing, routing and extraction. Electrical limits are checked separately from setup/hold and geometry DRC.','Electrical terminal evidence')
r.page('Physical verification and GDS export','Independent checks')
r.p('KLayout imports routed DEF using the platform layer map, merges the Nangate standard-cell GDS masters and writes rv32_pipeline.gds. Every instantiated master is checked for non-empty geometry. This confirms stream-out completeness, rather than transistor-level equivalence.')
r.table([['Check','Outcome and interpretation'],['Detailed-router DRC',', '.join(M['router_drvs'])+' final markers. This uses the router technology model and is distinct from GDS DRC.'],['Independent KLayout DRC',str(C.get('drc_markers','unavailable'))+' markers using the public FreePDK45 rule deck, including FEOL, BEOL, grid and antenna rule groups.'],['Power connectivity',f"VDD/VSS grid checks pass; all {PG['checked_power_ground_terminals']:,} instance power/ground terminals connect to the expected supply. No supply bump/pad model or voltage-drop analysis was performed."],['LVS',C['lvs']+'. An externally pinned FreePDK45 deck was adapted and validated against the installed Nangate cells.'],['Logical supplemental check','Directed scoreboard passes on mapped/post-route netlists at zero delay. This is not physical LVS or an SDF simulation.']],[185,usable-185])
r.photo('physical_checks_terminal.png','Physical check results','Recorded stream-out and independent DRC status. Any nonzero count remains a reported limitation; gate simulation and power continuity do not replace LVS.','Physical-verification terminal evidence')
r.photo('physical_checks_gui.png','GDS and independent DRC in KLayout','Final merged GDS loaded in KLayout, with the independent DRC results database. Marker categories identify the rules requiring review.','Physical-verification GUI evidence')
r.photo('power_pins_terminal.png','Instance power and ground connectivity','Explicit OpenDB audit of every POWER/GROUND instance terminal. Sizing protection is released before final global power connection; fixed placements are preserved. This supplements the PDN shape-continuity check.','Power terminal evidence')
r.page('LVS flow and validation','Layout versus schematic')
r.p('KLayout independently extracts transistor devices and routed connectivity from the final GDS. OpenROAD write_cdl exports the reference connectivity from the final database using the Nangate library pin order; the independent transistor-level library CDL is explicitly included.')
r.p('The public FreePDK45_for_KLayout deck is pinned at d15da945559773854ca04aeb9bc2c150d55a1e6c, with the original BSD-3-Clause source and license retained. The adaptation removes unrelated OpenRAM cheat blocks, corrects MOS tolerance class names and adds an explicit verdict and named-port check.',small=True)
r.table([['Validation','Measured outcome'],['Basic positive fixtures','INV_X1 and DFF_X1: PASS'],['Transistor-width negative control','Double the inverter MOS widths: expected FAIL, observed FAIL'],['Port-label negative control','Swap A and ZN labels without altering geometry: expected FAIL, observed FAIL'],['Instantiated cell-master sweep',str(L['validated_cell_masters'])+' functional masters: all PASS'],['Comparison validity','Nonempty processor and cell circuits; all circuit pairs and top-level relation pairs match.']],[220,usable-220])
r.p('MOS W/L tolerance: 1 nm absolute plus 0.1%. The deck follows the Nangate implicit-well convention: PWELL/BULK bind to VSS and NWELL to VDD. Only those well aliases are canonicalized; signal labels retain identity, with case normalized for SPICE. No processor or functional-cell black boxes are used.',small=True)
r.photo('lvs_cells_terminal.png','LVS deck validation and negative controls','Positive checks must pass and intentionally incorrect references/layout labels must fail. The whole set of instantiated standard-cell masters is independently checked.','LVS validation terminal evidence')
r.photo('lvs_negative_gui.png','Negative control rejected by LVS','The actual KLayout cross-reference browser shows a mismatch for the inverter whose reference transistor widths were deliberately doubled. This verifies that the flow detects a known defect.','LVS validation GUI evidence')
r.page('Processor LVS results','Measured comparison')
r.table([['Metric','Result'],['Overall comparison',L['status']],['Matched circuit pairs',str(L['matched_circuits'])+' (functional cell masters plus processor)'],['Matched named top-level pins',str(L['top_relations']['pins']['Match'])],['Matched top-level nets',str(L['top_relations']['nets']['Match'])],['Matched standard-cell instances',str(L['top_relations']['subcircuits']['Match'])],['Top-level port identities','PASS after SPICE letter-case normalization; bus indices preserved'],['Comparison duration',str(L['comparison_seconds'])+' seconds'],['Comparison log',str(L['comparison_error_count'])+' errors; '+str(L['comparison_warning_count'])+' internal-net ambiguity warnings'],['Cross-reference database','build/lvs/processor.lvsdb']],[235,usable-235])
r.p('All compared circuits and top-level relation pairs report Match. The warning count above concerns ambiguous internal net assignments; every circuit still reports Match and no comparison errors remain. LVS does not verify path delay, antenna limits or maximum-capacitance limits.',small=True)
r.photo('lvs_processor_terminal.png','Routed processor LVS and named-port audit','Actual recorded verdict and audited comparison counts. Input fingerprints in lvs_summary.json bind this result to the checked GDS, reference netlist and final OpenROAD database.','LVS terminal evidence')
r.photo('lvs_gui.png','Processor LVS cross-reference in KLayout','Actual native LVS database browser. Green circuit relations indicate matched extracted and reference circuits. The saved database supports further net, pin, device and instance inspection.','LVS GUI evidence')
r.page('Antenna and electrical closure','Repair and repeated verification')
r.table([['Check','Original routed core','Repaired routed core'],['Independent GDS antenna markers','43',str(C.get('drc_markers','unavailable'))],['Maximum-capacitance violations','8; worst excess 11.10 fF',str(len(M['max_capacitance_violations']))],['Cell area (um2; tool-rounded)','36,027',str(final['cell_area_um2_rounded'])],['Detailed-router markers','0',', '.join(M['router_drvs'])],['Extracted setup / hold slack','+6.44 / +0.02 ns',f"{final['setup_wns_ns']:+.2f} / {final['hold_wns_ns']:+.2f} ns"],['LVS','PASS before repair',L['status']+' on the new GDS']],[225,250,usable-475])
r.p('Repair anchors real input buffers at legal sites near their core pins, protects them against removal/resizing, and anchors the CTS root near clk. It restricts signal/clock routing to metals 2-6/4-6, and applies electrical repair using global-route parasitics with a 20% capacitance margin and 10% slew margin. Cells are legalized and affected nets re-routed before detailed routing. Final extraction, GDS DRC, routed netlist simulation and transistor-level LVS are repeated.',small=True)
r.p('The original Nangate antenna cell has zero declared diffusion area and an empty CDL device body. It was not used as an unverified diode repair. No DRC rules or Liberty capacitance limits were relaxed, and no antenna markers were waived.',small=True)
r.photo('antenna_candidate_gui.png','Intermediate repair: antenna check still fails','The first candidate cleared capacitance but left small-input-gate buffers free to move toward internal loads. The independent deck reported 79 antenna markers, so this candidate was rejected. The final repair anchors and protects the input buffers and CTS root.','Repair history - actual GUI evidence')
r.photo('antenna_candidate_terminal.png','Rejected candidate - measured check results','Actual saved DRC and electrical results for the intermediate candidate. These are repair-history measurements and are not the final submitted layout result.','Repair history - terminal evidence')
r.photo('repair_terminal.png','Electrical repair commands and tool output','Recorded OpenROAD repair output and the exact buffering, routing and margin commands from the reproducible physical flow.','Repair terminal evidence')
r.photo('closure_terminal.png','Final physical closure audit','The audit requires current GDS/ODB/deck fingerprints, zero GDS and router markers, zero capacitance violations, nonnegative setup/hold slack, passing routed simulation, power connectivity and passing LVS.','Final terminal evidence')
r.photo('antenna_before_gui.png','Original antenna markers before repair','Preserved KLayout view of the original 43-marker result. The final repeated independent check appears earlier in this report.','Repair history - actual GUI evidence')
r.photo('electrical_before_terminal.png','Original capacitance violations before repair','Preserved original extracted result: eight violating pins, with worst excess 11.10 fF. The final electrical check appears earlier in this report.','Repair history - actual terminal evidence')
r.page('Implementation scope and remaining limits','Discussion of results')
r.p('The repaired result is assessed against the same enabled public FreePDK45 DRC rules, Nangate Liberty limits and 10 ns clock constraint. Exact check counts, timing and input fingerprints are retained in the attached machine-readable reports.')
r.p('Hierarchical transistor-level LVS passes under the documented public-PDK extraction and well-bias assumptions. External memory, a pad ring, package power entry and a physical SRAM implementation remain outside this core project.')
r.p('Timing and area are educational typical-corner measurements. The disclosed hold uncertainty is 0.05 ns. Multi-corner timing, voltage-drop analysis and power consumption with representative activity have not been performed. The exported GDS is an academic routed core implementation; this result does not establish foundry signoff.')
contributions(r,'Open-source floorplan, PDN, placement, CTS, routing, extraction, GDS export, antenna/electrical repair, independent DRC/LVS, power audit and evidence/report preparation');references(r);r.finish()

# Include the exact implementation sources as accessible PDF attachments.
from pypdf import PdfReader,PdfWriter
for name,files in {
 'Assignment_IX_Front_End.pdf':['rtl/rv32_pipeline.sv','rtl/rv32_muldiv.sv','tb/pipeline_evidence_tb.sv','asic/open/constraints.sdc','reports/lvs_summary.json','reports/closure_summary.json'],
 'Assignment_X_Back_End.pdf':['asic/open/flow.tcl','asic/open/pin_input_buffers.tcl','asic/open/constraints.sdc','reports/asic_metrics.json','reports/physical_checks.json','reports/lvs_summary.json','asic/open/lvs/processor.lvs','asic/open/lvs/PROVENANCE.json','reports/closure_summary.json','reports/power_pins.json','build/asic/7_final_setup.rpt','build/asic/7_final_hold.rpt']
}.items():
 target=OUT/name
 writer=PdfWriter();writer.clone_document_from_reader(PdfReader(str(target)))
 for file in files:writer.add_attachment(Path(file).name,(ROOT/file).read_bytes())
 temp=target.with_suffix('.tmp.pdf')
 with temp.open('wb') as stream:writer.write(stream)
 temp.replace(target)
