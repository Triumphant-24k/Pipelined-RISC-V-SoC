foreach name {LIBERTY_FILES QRC_TECH_FILE} {
 if {![info exists ::env($name)]} {error "Missing $name"}
}
create_library_set -name typical -timing $::env(LIBERTY_FILES)
create_rc_corner -name rc_typical -qx_tech_file $::env(QRC_TECH_FILE)
create_delay_corner -name dc_typical -library_set typical -rc_corner rc_typical
create_constraint_mode -name functional -sdc_files {build/asic/mapped.sdc}
create_analysis_view -name typical_view -constraint_mode functional -delay_corner dc_typical
set_analysis_view -setup {typical_view} -hold {typical_view}
# Add actual fast/slow PVT corners before claiming multi-corner timing closure.
