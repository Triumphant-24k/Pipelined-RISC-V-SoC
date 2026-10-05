# Run from project root: genus -batch -files asic/genus.tcl
# LIBERTY_FILES: Tcl list of authorized standard-cell and applicable macro .lib files.
if {![info exists ::env(LIBERTY_FILES)]} {error "Set LIBERTY_FILES to authorized Liberty files"}
file mkdir build/asic
set_db library $::env(LIBERTY_FILES)
read_hdl -sv [glob rtl/*.sv]
elaborate pipelined_soc
check_design -unresolved
read_sdc asic/constraints.sdc
set_db syn_generic_effort high
set_db syn_map_effort high
set_db syn_opt_effort high
syn_generic
syn_map
syn_opt
report_timing > build/asic/genus_timing.rpt
report_area > build/asic/genus_area.rpt
report_gates > build/asic/genus_gates.rpt
write_hdl > build/asic/netlist.v
write_sdc > build/asic/mapped.sdc
write_db build/asic/genus.db
exit
