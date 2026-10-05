# Tool-version/PDK-dependent flow; unexecuted until college access is restored.
foreach name {LEF_FILES POWER_NET GROUND_NET POWER_PIN GROUND_PIN RING_H_LAYER RING_V_LAYER CTS_BUFFER_CELLS} {
 if {![info exists ::env($name)]} {error "Set $name from the actual PDK/library"}
}
if {![file exists build/asic/netlist.v]} {error "Run the mapped Genus synthesis first"}
set init_top_cell pipelined_soc
set init_verilog build/asic/netlist.v
set init_lef_file $::env(LEF_FILES)
set init_mmmc_file asic/mmmc.tcl
set init_pwr_net $::env(POWER_NET)
set init_gnd_net $::env(GROUND_NET)
init_design
floorPlan -r 1.0 0.60 10 10 10 10
globalNetConnect $::env(POWER_NET) -type pgpin -pin $::env(POWER_PIN) -inst *
globalNetConnect $::env(GROUND_NET) -type pgpin -pin $::env(GROUND_PIN) -inst *
addRing -nets [list $::env(POWER_NET) $::env(GROUND_NET)] -type core_rings \
 -layer [list top $::env(RING_H_LAYER) bottom $::env(RING_H_LAYER) left $::env(RING_V_LAYER) right $::env(RING_V_LAYER)] \
 -width 2 -spacing 1 -offset 2
sroute -nets [list $::env(POWER_NET) $::env(GROUND_NET)] -connect {corePin blockPin padPin padRing floatingStripe}
place_opt_design
timeDesign -preCTS -outDir build/asic/prects
create_ccopt_clock_tree_spec
set_ccopt_property buffer_cells $::env(CTS_BUFFER_CELLS)
ccopt_design
timeDesign -postCTS -outDir build/asic/postcts
routeDesign
optDesign -postRoute
timeDesign -postRoute -outDir build/asic/postroute
timeDesign -postRoute -hold -outDir build/asic/postroute_hold
verifyGeometry -report build/asic/geometry.rpt
verifyConnectivity -report build/asic/connectivity.rpt
saveDesign build/asic/routed.enc
saveNetlist build/asic/routed.v
rcOut -spef build/asic/routed.spef
if {[info exists ::env(ACTIVITY_VCD)] && [info exists ::env(ACTIVITY_SCOPE)]} {
 read_activity_file -format VCD -scope $::env(ACTIVITY_SCOPE) $::env(ACTIVITY_VCD)
 report_power -outfile build/asic/power.rpt
}
exit
