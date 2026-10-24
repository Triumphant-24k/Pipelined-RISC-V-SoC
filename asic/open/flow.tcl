# Reproducible academic processor flow; OpenROAD 2.0-17598.
set root [pwd]
cd $root
set platform $::env(HOME)/OpenROAD-flow-scripts/flow/platforms/nangate45
if {[info exists ::env(NANGATE45)]} {set platform $::env(NANGATE45)}
set out build/asic
file mkdir $out
set_thread_count 4
read_lef $platform/lef/NangateOpenCellLibrary.tech.lef
read_lef $platform/lef/NangateOpenCellLibrary.macro.mod.lef
read_liberty $platform/lib/NangateOpenCellLibrary_typical.lib
read_verilog $out/1_synth.v
link_design rv32_pipeline
read_sdc asic/open/constraints.sdc
source $platform/setRC.tcl
set_dont_use {TAPCELL_X1 FILLCELL_X1 AOI211_X1 OAI211_X1}
proc checkpoint {name} {
 global out
 puts "=== CHECKPOINT $name ==="
 report_design_area
 report_worst_slack -max
 report_worst_slack -min
 report_tns
 report_check_types -max_slew -max_capacitance -violators
 report_checks -path_delay max -format full_clock_expanded -group_count 3 > $out/${name}_setup.rpt
 report_checks -path_delay min -format full_clock_expanded -group_count 3 > $out/${name}_hold.rpt
 write_db $out/${name}.odb
 write_def $out/${name}.def
 write_sdc $out/${name}.sdc
}
# Synthesis STA uses ideal clocks and zero interconnect parasitics.
checkpoint 1_synth
initialize_floorplan -utilization 40 -aspect_ratio 1 -core_space 10 -site FreePDK45_38x28_10R_NP_162NW_34O
source $platform/make_tracks.tcl
remove_buffers
place_pins -hor_layers metal5 -ver_layers metal6 -random
repair_tie_fanout -separation 1 LOGIC0_X1/Z
repair_tie_fanout -separation 1 LOGIC1_X1/Z
checkpoint 2_floorplan
add_global_connection -net VDD -inst_pattern .* -pin_pattern ^VDD$ -power
add_global_connection -net VSS -inst_pattern .* -pin_pattern ^VSS$ -ground
global_connect
set_voltage_domain -name CORE -power VDD -ground VSS
define_pdn_grid -name core_grid -voltage_domains CORE -pins {metal7}
add_pdn_ring -grid core_grid -layers {metal6 metal7} -widths 1.4 -spacings 1.0 -core_offsets 3.0 -connect_to_pads
add_pdn_stripe -grid core_grid -layer metal1 -width 0.17 -pitch 2.4 -offset 0 -followpins
add_pdn_stripe -grid core_grid -layer metal4 -width 0.48 -pitch 40 -offset 4
add_pdn_stripe -grid core_grid -layer metal7 -width 1.4 -pitch 30 -offset 4 -extend_to_core_ring
add_pdn_connect -grid core_grid -layers {metal1 metal4}
add_pdn_connect -grid core_grid -layers {metal4 metal7}
add_pdn_connect -grid core_grid -layers {metal6 metal7}
pdngen -failed_via_report $out/pdn_failed_vias.rpt
checkpoint 3_power
set_routing_layers -signal metal2-metal10 -clock metal4-metal10
set_global_routing_layer_adjustment metal2-metal10 0.3
global_placement -density 0.55 -routability_driven
estimate_parasitics -placement
repair_design
set_placement_padding -global -left 1 -right 1
detailed_placement
check_placement -verbose
estimate_parasitics -placement
checkpoint 4_placement
repair_clock_inverters
clock_tree_synthesis -root_buf CLKBUF_X3 -buf_list {CLKBUF_X1 CLKBUF_X2 CLKBUF_X3} -sink_clustering_enable
repair_clock_nets
detailed_placement
set_propagated_clock [all_clocks]
estimate_parasitics -placement
checkpoint 5_cts_raw
if {[catch {repair_timing -max_buffer_percent 50} reason]} {
 puts "TIMING_REPAIR_LIMITATION $reason"
}
# Timing repair inserts cells; legalize before routing.
detailed_placement
check_placement -verbose
estimate_parasitics -placement
report_clock_skew
checkpoint 5_cts
global_route -guide_file $out/route.guide -congestion_iterations 100 -verbose
estimate_parasitics -global_routing
checkpoint 6_global_route
detailed_route -output_drc $out/route_drc.rpt -output_maze $out/maze.log -verbose 0
puts "FINAL_ROUTER_DRVS [detailed_route_num_drvs]"
filler_placement {FILLCELL_X1 FILLCELL_X2 FILLCELL_X4 FILLCELL_X8 FILLCELL_X16 FILLCELL_X32}
check_placement -verbose
global_connect
write_verilog -remove_cells {FILLCELL*} $out/7_final.v
# Extract routed RC, then analyze the propagated clock at the typical corner.
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $platform/rcx_patterns.rules
write_spef $out/7_final.spef
read_spef $out/7_final.spef
checkpoint 7_final
report_clock_skew
report_check_types -max_slew -max_capacitance -max_fanout -violators
check_power_grid -net VDD
check_power_grid -net VSS
puts "FLOW_COMPLETE"
